# Запуски N1

Источник: experiments/EXPERIMENT_LOG.jsonl, 22 строки на 6 октября 2026 года, по паре событий started и completed/failed на каждый из 11 запусков. Строки журнала не изменялись и не удалялись. Каталоги результатов лежат в data/ и в Git не входят; в таблице указан data_sha256 (хеш manifest каталога).

| run_id | Назначение | Статус | Родитель | git SHA | dirty | Ошибка или результат |
|---|---|---|---|---|---|---|
| 20261006T103539-85096ec568 | N1 acquisition | failed | — | 1643651 | true | OperationalError: unable to open database file (кеш yfinance) |
| 20261006T103621-754f18207b | N1 acquisition | failed | 20261006T103539-85096ec568 | 1643651 | true | SSLError curl (77): CA-файл по пути с кириллицей; частичный снимок data/snapshots/20261006T103621-754f18207b, a22999ba… |
| 20261006T103625-5202b05cbc | N1 issuer evidence acquisition | completed | — | 1643651 | true | data/evidence/20261006T103625-5202b05cbc, 4156d547…; код не был закоммичен, заменён запуском 20261006T122017-3048321309 |
| 20261006T103702-af69d7e5e6 | N1 acquisition | failed | 20261006T103621-754f18207b | 1643651 | true | NotImplementedError: Option unsupported: 40309 (curl CAINFO_BLOB); частичный снимок 54f97843… |
| 20261006T103809-a4a22ec667 | N1 acquisition | completed | 20261006T103702-af69d7e5e6 | 1643651 | true | data/snapshots/20261006T103809-a4a22ec667, 09edd925…; используемый снимок Yahoo |
| 20261006T104336-dff9099c6b | N1 offline QA | completed | — | 80f75c9 | true | data/derived/20261006T104336-dff9099c6b, d4cde5cf…; без actual payable; заменён запуском 20261006T122144-73228a71eb |
| 20261006T104437-36dd8f9b4a | N1 issuer distribution reconciliation | completed | — | 80f75c9 | true | data/reconciliation/20261006T104437-36dd8f9b4a, b87b4209…; код не был закоммичен, заменён запуском 20261006T122119-c6bfb5c69b |
| 20261006T122017-3048321309 | N1 issuer evidence acquisition | completed | 20261006T103625-5202b05cbc | 590281e | false | data/evidence/20261006T122017-3048321309, 0a9bcea6…; 9 источников, все ok |
| 20261006T122119-c6bfb5c69b | N1 issuer distribution reconciliation | completed | 20261006T104437-36dd8f9b4a | c78a319 | false | data/reconciliation/20261006T122119-c6bfb5c69b, cb69e4fc…; предупреждения: unresolved SPY, TLT, LQD, HYG, BIL; нет источника GLD, DBC |
| 20261006T122144-73228a71eb | N1 offline QA | completed | 20261006T104336-dff9099c6b | 8e677d1 | false | data/derived/20261006T122144-73228a71eb, f9602513…; technical_pass true, data_ready_for_n2 false |
| 20261006T122200-a9fd9ddbda | N1 offline replay | completed | 20261006T122144-73228a71eb | cdaaf85 | false | replay_equal true, data_sha256 совпадает с QA-запуском |

Первые семь запусков выполнены кодом, который в момент запуска не был закоммичен (dirty_tree true, хеш патча в журнале). Снимок Yahoo 20261006T103809-a4a22ec667 остаётся входом: его байты проверяются по manifest при каждом audit/reconcile, повторная загрузка не делалась. Evidence, reconciliation и QA перезапущены закоммиченным кодом.

Коммиты c78a319, 8e677d1, cdaaf85 и fa8fe34 содержат только новые строки журнала. Они сделаны между запусками, чтобы каждый следующий запуск начинался с чистого дерева.

## Команды новых запусков

Git Bash, корень worktree, Python 3.14.0 из .venv. Пакет не установлен в окружение, поэтому путь к src задаётся через PYTHONPATH.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab evidence --root . --parent 20261006T103625-5202b05cbc
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T122017-3048321309 --root . --parent 20261006T104437-36dd8f9b4a
PYTHONPATH=src .venv/Scripts/python -m alpha_lab audit data/snapshots/20261006T103809-a4a22ec667 --payable data/reconciliation/20261006T122119-c6bfb5c69b/payable.json --root . --parent 20261006T104336-dff9099c6b
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T122144-73228a71eb --root . --parent 20261006T122144-73228a71eb
```

Первая попытка evidence без PYTHONPATH завершилась ошибкой интерпретатора `No module named alpha_lab` до входа в код проекта; запуск не начался и в журнал не попал.

Вывод replay: `{"replay_equal": true}`.
