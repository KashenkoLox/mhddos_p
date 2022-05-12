import random
from socket import AF_INET, SOCK_STREAM, socket

from PyRoxy import ProxyUtiles
from .core import logger, cl, PROXIES_URLS
from .system import read_or_fetch, fetch


# @formatter:off
_globals_before = set(globals().keys()).union({'_globals_before'})
# noinspection PyUnresolvedReferences
from .load_proxies import *
decrypt_proxies = globals()[set(globals().keys()).difference(_globals_before).pop()]
# @formatter:on


class _NoProxy:
    def asRequest(self):
        return None

    def open_socket(self, family=AF_INET, type=SOCK_STREAM, proto=-1, fileno=None):
        return socket(family, type, proto, fileno)


NoProxy = _NoProxy()


def update_proxies(proxies_file, previous_proxies):
    if proxies_file:
        proxies = load_provided_proxies(proxies_file)
    else:
        proxies = load_system_proxies()

    if not proxies:
        if previous_proxies:
            proxies = previous_proxies
            logger.warning(f'{cl.MAGENTA}Будет использован предварительный список прокси{cl.RESET}')
        else:
            logger.error(f'{cl.RED}Не найдено рабочих прокси - останавливаем атаку{cl.RESET}')
            exit()

    return proxies


def load_provided_proxies(proxies_file):
    content = read_or_fetch(proxies_file)
    if content is None:
        logger.warning(f'{cl.RED}Не удалось считать прокси из {proxies_file}{cl.RESET}')
        return None

    proxies = ProxyUtiles.parseAll([prox for prox in content.split()])
    if not proxies:
        logger.warning(f'{cl.RED}В {proxies_file} не найдено прокси - проверьте формат{cl.RESET}')
    else:
        logger.info(f'{cl.YELLOW}Почитано {cl.BLUE}{len(proxies)}{cl.YELLOW} прокси{cl.RESET}')
    return proxies


def load_system_proxies():
    raw = fetch(random.choice(PROXIES_URLS))
    try:
        proxies = ProxyUtiles.parseAll(decrypt_proxies(raw))
    except Exception:
        proxies = []
    if proxies:
        logger.info(
            f'{cl.YELLOW}Получена выборка {cl.BLUE}{len(proxies):,}{cl.YELLOW} прокси '
            f'из списка {cl.BLUE}25.000+{cl.YELLOW} рабочих{cl.RESET}'
        )
    else:
        logger.warning(f'{cl.RED}Не удалось получить персональную выборку прокси{cl.RESET}')
    return proxies
