import os
import time
from typing import Dict

from tabulate import tabulate

from .core import cl, logger, THREADS_PER_CORE, Params, Stats
from .mhddos import Tools


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


def show_statistic(
    statistics: Dict[Params, Stats],
    table,
    use_my_ip,
    proxies_cnt,
    time_left
):
    tabulate_text = []
    total_pps, total_bps = 0, 0
    for params, stats in statistics.items():
        pps, bps = stats.reset()
        total_pps += pps
        total_bps += bps
        if table:
            tabulate_text.append((
                f'{cl.YELLOW}%s' % params.target.url.host, params.target.url.port, params.method,
                Tools.humanformat(pps) + "/s", f'{Tools.humanbits(bps)}/s{cl.RESET}'
            ))
        else:
            logger.info(
                f'{cl.YELLOW}Цель:{cl.BLUE} %s,{cl.YELLOW} Порт:{cl.BLUE} %s,{cl.YELLOW} Метод:{cl.BLUE} %s,'
                f'{cl.YELLOW} Запросы:{cl.BLUE} %s/s,{cl.YELLOW} Трафик:{cl.BLUE} %s/s{cl.RESET}' %
                (
                    params.target.url.host,
                    params.target.url.port,
                    params.method,
                    Tools.humanformat(pps),
                    Tools.humanbits(bps),
                )
            )

    if table:
        tabulate_text.append((f'{cl.GREEN}Всего', '', '', Tools.humanformat(total_pps) + "/s",
                              f'{Tools.humanbits(total_bps)}/s{cl.RESET}'))

        cls()
        print(tabulate(
            tabulate_text,
            headers=[f'{cl.BLUE}Цель', 'Порт', 'Метод', 'Запросы', f'Трафик{cl.RESET}'],
            tablefmt='fancy_grid'
        ))
        print_banner(use_my_ip)
    else:
        logger.info(
            f'{cl.GREEN}Всего:{cl.YELLOW} Запросы:{cl.GREEN} %s/s,{cl.YELLOW} Трафик:{cl.GREEN} %s/s{cl.RESET}' %
            (
                Tools.humanformat(total_pps),
                Tools.humanbits(total_bps),
            )
        )

    print_progress(time_left, proxies_cnt, use_my_ip)


def print_progress(time_left, proxies_cnt, use_my_ip):
    logger.info(f'{cl.YELLOW}Новый цикл через: {cl.BLUE}{time_left} секунд{cl.RESET}')
    if proxies_cnt:
        logger.info(f'{cl.YELLOW}Количество прокси: {cl.BLUE}{proxies_cnt}{cl.RESET}')
        if use_my_ip:
            logger.info(f'{cl.YELLOW}Атака также использует {cl.MAGENTA}ваш IP вместе с прокси{cl.RESET}')
    else:
        logger.info(f'{cl.YELLOW}Атака {cl.MAGENTA}без прокси{cl.YELLOW} - используется только ваш IP{cl.RESET}')


def print_banner(use_my_ip):
    print(f'''
- {cl.YELLOW}Нагрузка (количество потоков){cl.RESET} - параметр `-t 3000`, по умолчанию - CPU * {THREADS_PER_CORE}
- {cl.YELLOW}Статистика в виде таблицы или текста{cl.RESET} - флажок `--table` или `--debug`
- {cl.YELLOW}Полная документация{cl.RESET} - https://github.com/Bionec/mhddos_p
    ''')

    if not use_my_ip:
        print(
            f'        {cl.MAGENTA}Использовать свой IP или VPN {cl.YELLOW}в дополнение к прокси - флажок `--vpn`{cl.RESET}\n')
