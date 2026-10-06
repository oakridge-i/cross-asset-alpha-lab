# Состояние проекта

Дата: 6 октября 2026, Europe/Moscow. Этап N1 (данные): блокирующие пункты D015 закрыты на скорректированном vintage, предложен вердикт D019: данные готовы к N2 (предложен, утверждает контролёр; до утверждения N2 на реальных данных не начинается). Прежний вердикт D015 («не готовы») остаётся записью истории. Ветка claude/n1-closure (от main на коммите 799eef9; codex/n1-data слита и удалена), не слита в main, remote отсутствует. Доходности H1/H2 не рассчитывались, гипотезы registered_not_tested, reserved performance не открыт.

N0 завершён ранее: протокол, проверка источников, receipt docs/n0/verification.json (35/35 на коммите N0).

## Выполненное в N1

- Пакет src/alpha_lab: загрузка Yahoo с неизменяемым снимком и журналом, нормализация в as-traded единицы, QA календаря и actions, загрузка материалов эмитентов, сверка распределений, слой исправлений, offline replay. CLI `python -m alpha_lab {acquire,evidence,reconcile,corrections,audit,replay}`.
- Снимок Yahoo 20261006T103809-a4a22ec667 (десять ETF до 2026-10-05).
- Материалы эмитентов 20261006T122017-3048321309: SSGA xlsx, шесть страниц iShares, документы сплитов EEM 2008 и BIL 2017.
- Сверка 20261006T122119-c6bfb5c69b, QA 20261006T122144-73228a71eb с actual payable, replay 20261006T122200-a9fd9ddbda и повторный replay 20261006T131812-09887a01da после исправлений финального ревью.
- Отчёт docs/n1/N1_REPORT.md, сводки docs/n1/source_evidence.json, docs/n1/quality.json, журнал запусков docs/n1/execution_record.md. Решения D012–D015.
- Финальное ревью ветки: ошибок в расчётах не найдено; добавлены тесты отказа replay при подмене, сохранения данных при сбое загрузки Yahoo, журналирования нечитаемых входов, хеши входных manifest в журнале.

## Закрытие блокирующих пунктов N1 (6 октября 2026)

- Источники эмитентов: DBC из локального захвата Invesco JSON, полученного в браузере встроенной панели Claude desktop (sha256 7337eeb7…, загрузка разрешена пользователем; D017); GLD из проспекта и FAQ SSGA (D018). Evidence 20261006T172354-1c0a8ca2d8, 12 источников.
- Сверка по исходным данным Yahoo 20261006T172415-ce65adb53e: DBC confirmed, GLD confirmed_no_distributions, EFA/EEM/IEF confirmed, SPY/TLT/LQD/HYG/BIL unresolved с теми же семью событиями.
- Исправления 20261006T172434-fbb5c9f554 по решению пользователя (D016): 3 add, 3 replace, 1 remove. QA скорректированного vintage 20261006T172442-80ef993493 (technical_pass true, 4869/4869 сессий, adjustment_breaks 0), сверка скорректированного vintage 20261006T172453-4d72af092f (все десять тикеров confirmed или confirmed_no_distributions), replay 20261006T172504-6b932ef79b (replay_equal true).
- Прежний derived-снимок 20261006T122144-73228a71eb текущим кодом не воспроизводится (в нормализованной таблице появились dividend_basis и dividend_correction_source, corrections.json вошёл в derived-снимок); его точное воспроизведение записано в запуске 20261006T131812-09887a01da на коммите 977eaf6.
- Отчёт docs/n1/N1_REPORT.md, раздел «Закрытие блокирующих пунктов»; docs/n1/source_evidence.json, docs/n1/quality.json (копия quality.json нового vintage), docs/n1/execution_record.md. Решения D016–D019.

## Проверки

| Проверка | Результат |
|---|---|
| pytest (`PYTHONPATH=src .venv/Scripts/python -m pytest -q -p no:cacheprovider --basetemp=$TEMP/c5pt`) | 122 passed (ветка claude/n1-closure после правок финального ревью; на коммите 977eaf6 было 79) |
| `.venv/Scripts/python -m pip check` | No broken requirements found |
| Окружение | из .venv удалены openpyxl 3.1.5 и et_xmlfile 2.0.0: их нет в requirements.lock, закоммиченный код их не импортирует, они остались от раннего незакоммиченного скрипта; после удаления `pip freeze --all` совпадает с lock-файлом. Новый временный venv вне репозитория: установка из requirements.lock, pip check, 66 passed, `PYTHONPATH=src python -m alpha_lab --help` работает; venv удалён |
| `git diff --check` | без замечаний |
| replay | скорректированный vintage 20261006T172442-80ef993493: replay_equal true. Прежний снимок f9602513…: replay_equal true на коммите 977eaf6 (запуск 20261006T131812-09887a01da), текущим кодом не воспроизводится |
| QA | скорректированный vintage: technical_pass true, 4869/4869 сессий у всех ETF, adjustment_breaks 0 |
| База сплитов EEM 2008-07-24 3:1, BIL 2017-11-30 1:2 | confirmed оба |
| Распределения | исходные данные Yahoo: confirmed EFA, EEM, IEF, DBC, GLD (confirmed_no_distributions), unresolved SPY, TLT, LQD, HYG, BIL; скорректированный vintage: все десять confirmed или confirmed_no_distributions |
| `python -X utf8 docs/n0/verify_n0.py --no-write` | ошибка: в worktree скрипт ищет quant-research-plan рядом с корнем (.worktrees/quant-research-plan) и падает с FileNotFoundError; проверка пустого журнала N0 после N1 также не может пройти. Скрипт N0 не менялся |

Последний проверенный коммит кода: 02af65e (тесты 122 passed, pip check, git diff --check; после него только документы). Правки финального ревью: проверка исправлений remove и replace на событие Yahoo в сессии, проверка происхождения vintage исправлений от аудируемого снимка в audit.

## Ограничения

Данные не point-in-time, available_at является модельным допущением. Семь исправлений Yahoo (D016) приняты по решению пользователя об авторитетности эмитента, независимой проверки у них нет. Основание GLD (D018) слабее формулировки «распределений не было никогда». Полнота DBC до 2007-12-17 по документу эмитента не доказана (D017). Yahoo и эмитенты могут пересматривать историю; iShares публикует суммы до сплита в текущих единицах. Объём не подтверждён и не используется. Выборка ретроспективная. Допуск суммы распределения выбран после наблюдения расхождений (D013). Снимок Yahoo загружен кодом с незакоммиченными изменениями (хеш патча в журнале). Права на данные Yahoo не установлены, снимки в Git не входят.

## Следующий шаг

Контролёр утверждает или отклоняет вердикт D019 отдельной записью. После утверждения N2 использует только скорректированный vintage data/derived/20261006T172442-80ef993493 с его corrections.json.
