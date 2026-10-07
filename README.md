# Cross-Asset Alpha Lab

Учебное исследование: дают ли относительный momentum и устойчивость движения добавочную ценность к простым мультиактивным стратегиям после расходов и учёта риска?

Состояние на 6 октября 2026 года: N0 завершён; N1 (данные) выполнен. Вердикт D015 (данные не готовы к N2) утверждён; блокирующие пункты закрыты на скорректированном vintage (источники эмитентов для DBC и GLD, семь исправлений по решению пользователя), предложен вердикт D019: данные готовы к N2; решение утверждает контролёр. Доходность H1/H2 не рассчитывалась, гипотезы не проверены. Положительная альфа не является условием успеха проекта.

MVP: девять рискованных ETF и BIL, USD, дневные данные, месячные решения, long-only, без плеча. Предполагаемое исполнение — следующее открытие с явным ограничением денег. Репозиторий локальный, remote отсутствует.

Основные документы:

- [RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md) — точные формулы, сравнения, параметры и правила исследования.
- [STATUS.md](STATUS.md) — выполненное, критерии готовности и следующий шаг.
- [DECISIONS.md](DECISIONS.md) — решения и причины.
- [Отчёт N1](docs/n1/N1_REPORT.md) — данные, сверка с эмитентами, база сплитов, закрытие блокирующих пунктов и вердикты (D015 «не готово к N2»; D019 «готово», предложен); [журнал запусков N1](docs/n1/execution_record.md).
- [Отчёт N0](docs/n0/N0_REPORT.md) — предпосылки, источники и ограничения.
- [Code review N1](docs/reviews/2026-10-06-n1-review.md) — проверка изменений на 0a0e865: четыре P2, 122 пройденных теста и подтверждённое воспроизведение текущего снимка.
- [Проверка доступности](docs/n0/source_probe.json) — фактические ответы источника, границы и хеши ответов.
- [Проверка AAPL и перенос](docs/n0/AAPL_REUSE_AUDIT.md) — подтверждённая исходная версия и кандидаты на перенос.
- [Полный план N0–N8](docs/MASTER_PLAN.md) — исходный маршрут; уточнения N0 находятся в протоколе и DECISIONS.md.
- [Журнал попыток](experiments/EXPERIMENT_LOG.jsonl) и [его правила](experiments/README.md).

Python-пакет src/alpha_lab содержит конвейер данных N1: загрузку, нормализацию, QA, сверку распределений, слой исправлений и replay. Бэктеста, портфельного движка и расчёта стратегий нет.

## Окружение и проверки N1

Окружение: Python 3.14.0, версии пакетов точно в requirements.lock (включая pip). Пакет alpha_lab не устанавливается; для CLI путь к src задаётся через PYTHONPATH=src, pytest находит его через pythonpath в pyproject.toml. Установка проверена 6 октября 2026 года в Git Bash на новом временном venv вне репозитория: после установки `pip freeze --all` совпал с requirements.lock, `pip check` без замечаний, тесты 66 passed на тот момент (на ветке закрытия 122 passed), `python -m alpha_lab --help` работает с PYTHONPATH=src и без него завершается ошибкой `No module named alpha_lab`.

```bash
py -3.14 -m venv .venv
.venv/Scripts/python -m pip install -r requirements.lock
.venv/Scripts/python -m pip check
.venv/Scripts/python -m pytest -q -p no:cacheprovider --basetemp=$TEMP/n1pt
PYTHONPATH=src .venv/Scripts/python -m alpha_lab --help
```

В рабочем .venv были лишние openpyxl 3.1.5 и et_xmlfile 2.0.0, которых нет в lock-файле. Их установили для раннего незакоммиченного скрипта; закоммиченный код их не импортирует. 6 октября 2026 года они удалены (`pip uninstall -y openpyxl et_xmlfile`); после этого `pip freeze --all` совпадает с requirements.lock. Запуски N1 начиная с 20261006T103809-a4a22ec667 выполнены до удаления, их environment hash включает эти пакеты.

Запуски N1 до закрытия блокирующих пунктов в том виде, в каком они выполнены (с текущим кодом derived-снимок 20261006T122144-73228a71eb не воспроизводится: схема нормализованной таблицы изменилась). Каждый запуск пишет started и completed/failed в experiments/EXPERIMENT_LOG.jsonl и создаёт новый каталог в data/ (не входит в Git):

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab evidence --root . --parent 20261006T103625-5202b05cbc
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T122017-3048321309 --root . --parent 20261006T104437-36dd8f9b4a
PYTHONPATH=src .venv/Scripts/python -m alpha_lab audit data/snapshots/20261006T103809-a4a22ec667 --payable data/reconciliation/20261006T122119-c6bfb5c69b/payable.json --root . --parent 20261006T104336-dff9099c6b
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T122144-73228a71eb --root . --parent 20261006T122144-73228a71eb
```

Закрытие блокирующих пунктов (6 октября 2026 года, ветка claude/n1-closure). Порядок обязателен: каждый шаг получает результат предыдущего, а между запусками журнал коммитится, чтобы следующий запуск начинался с чистого дерева. Локальный снимок DBC data/manual/dbc-invesco-distribution.json в Git не входит и должен лежать на месте (sha256 указан в configs/n1_evidence.json):

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab evidence --root . --parent 20261006T122017-3048321309
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T172354-1c0a8ca2d8 --root . --parent 20261006T122119-c6bfb5c69b
PYTHONPATH=src .venv/Scripts/python -m alpha_lab corrections data/reconciliation/20261006T172415-ce65adb53e --root . --parent 20261006T172415-ce65adb53e
PYTHONPATH=src .venv/Scripts/python -m alpha_lab audit data/snapshots/20261006T103809-a4a22ec667 --payable data/corrections/20261006T172434-fbb5c9f554/payable.json --corrections data/corrections/20261006T172434-fbb5c9f554/corrections.json --root . --parent 20261006T122144-73228a71eb
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T172354-1c0a8ca2d8 --corrections data/corrections/20261006T172434-fbb5c9f554/corrections.json --root . --parent 20261006T172415-ce65adb53e
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T172442-80ef993493 --root . --parent 20261006T172442-80ef993493
```

Снимок Yahoo создан командой `acquire` (запуск 20261006T103809-a4a22ec667) и в 3B не перезагружался. Повтор evidence и acquire обращается к сети и даёт новый vintage; replay работает без сети.

Итог N1: база сплитов EEM 2008 и BIL 2017 подтверждена документами. На исходных данных Yahoo распределения подтверждены (confirmed) у EFA, EEM, IEF, DBC, у GLD статус confirmed_no_distributions; на скорректированном vintage 20261006T172442-80ef993493 (7 исправлений по эмитенту) confirmed или confirmed_no_distributions у всех десяти (docs/n1/N1_REPORT.md). Точность всех цен не установлена; actual payable dates есть только у совпавших с эмитентом событий.

## Проверки N0

Сейчас проверены команды просмотра репозитория из его корня:

```powershell
git status --short --branch
git log -1 --oneline
```

Диагностический скрипт N0 использует только стандартную библиотеку Python. Его повтор загружает ответы заново и выводит JSON в консоль; результаты поставщика и их хеши могут измениться. Для сохранения предусмотрен --output с новым путём, существующий receipt не перезаписывается. Это не воспроизведение сертифицированного снимка N1:

```powershell
python -X utf8 docs/n0/probe_sources.py
```

Проверка документов N0 без сети и изменения receipt (рассчитана на корень основного репозитория; после N1 проверка пустого журнала не проходит по построению, в worktree скрипт не находит каталог quant-research-plan):

```powershell
python -X utf8 docs/n0/verify_n0.py --no-write
```

Проверяются ссылки, точность копий, ограничения manifest, пустой журнал, состояние AAPL и иллюстративная арифметика формул. Это не тесты ещё отсутствующего портфельного движка. Проверка AAPL требует доступных исходных локальных каталогов; перенос проекта на другой компьютер потребует обновить этот аудиторский сценарий.

Сырые данные и окружения исключены из Git. Условия библиотеки не заменяют права на рыночные данные; внешняя публикация и платные источники требуют отдельного разрешения.

2023–2026 годы не объявлены независимым тестом: прежний просмотр H1/H2 неизвестен. Реально новые наблюдения начнутся только после будущей заморозки модели. Подробности — в протоколе.
