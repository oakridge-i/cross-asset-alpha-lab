# Состояние проекта

Дата: 6 октября 2026, Europe/Moscow. Этап N1 (данные) выполнен до вердикта; предложенный вердикт: данные не готовы к N2. Решение утверждает контролёр. Ветка codex/n1-data, не слита в main, remote отсутствует. Доходности H1/H2 не рассчитывались, гипотезы registered_not_tested, reserved performance не открыт.

N0 завершён ранее: протокол, проверка источников, receipt docs/n0/verification.json (35/35 на коммите N0).

## Выполненное в N1

- Пакет src/alpha_lab: загрузка Yahoo с неизменяемым снимком и журналом, нормализация в as-traded единицы, QA календаря и actions, загрузка материалов эмитентов, сверка распределений, offline replay. CLI `python -m alpha_lab {acquire,evidence,reconcile,audit,replay}`.
- Снимок Yahoo 20261006T103809-a4a22ec667 (десять ETF до 2026-10-05).
- Материалы эмитентов 20261006T122017-3048321309: SSGA xlsx, шесть страниц iShares, документы сплитов EEM 2008 и BIL 2017.
- Сверка 20261006T122119-c6bfb5c69b, QA 20261006T122144-73228a71eb с actual payable, replay 20261006T122200-a9fd9ddbda.
- Отчёт docs/n1/N1_REPORT.md, сводки docs/n1/source_evidence.json, docs/n1/quality.json, журнал запусков docs/n1/execution_record.md. Решения D012–D014.

## Проверки

| Проверка | Результат |
|---|---|
| pytest (`.venv/Scripts/python -m pytest -q -p no:cacheprovider --basetemp=$TEMP/n1pt`) | 66 passed |
| `.venv/Scripts/python -m pip check` | No broken requirements found |
| `git diff --check` | без замечаний |
| replay | replay_equal true, data_sha256 f9602513… совпадает с QA |
| QA | technical_pass true, 4869/4869 сессий у всех ETF, adjustment_breaks 0 |
| База сплитов EEM 2008-07-24 3:1, BIL 2017-11-30 1:2 | confirmed оба |
| Распределения | confirmed: EFA, EEM, IEF; unresolved: SPY, TLT, LQD, HYG, BIL; unverified_no_issuer_source: DBC, GLD |
| `python -X utf8 docs/n0/verify_n0.py --no-write` | ошибка: в worktree скрипт ищет quant-research-plan рядом с корнем (.worktrees/quant-research-plan) и падает с FileNotFoundError; проверка пустого журнала N0 после N1 также не может пройти. Скрипт N0 не менялся |

Последний проверенный коммит кода и журнала: fa8fe34. Документы N1 добавлены следующим коммитом.

## Ограничения

Данные не point-in-time, available_at является модельным допущением. Yahoo и эмитенты могут пересматривать историю; iShares публикует суммы до сплита в текущих единицах. Объём не подтверждён и не используется. Выборка ретроспективная. Допуск суммы распределения выбран после наблюдения расхождений (D013). Снимок Yahoo загружен кодом с незакоммиченными изменениями (хеш патча в журнале). Права на данные Yahoo не установлены, снимки в Git не входят.

## Следующий шаг

Контролёр утверждает или меняет вердикт N1 (D014) и выбирает способ закрыть блокирующие пункты N1_REPORT: история распределений DBC (ручная загрузка пользователем с сайта Invesco или годовые отчёты), документ об отсутствии распределений GLD, решение по пропуску Yahoo 2012-11-01 у HYG/LQD/TLT, по BIL 2022-03-01 и по трём расхождениям меньше 0.1 bps. До этого N2 на реальных данных не начинается.
