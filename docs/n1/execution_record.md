# Запуски N1

Источник: experiments/EXPERIMENT_LOG.jsonl, 36 строк на 6 октября 2026 года, по паре событий started и completed/failed на каждый из 18 запусков. Строки журнала не изменялись и не удалялись. Каталоги результатов лежат в data/ и в Git не входят; в таблице указан data_sha256 (хеш manifest каталога).

| run_id | Назначение | Статус | Родитель | git SHA | dirty | Ошибка или результат |
|---|---|---|---|---|---|---|
| 20261006T103539-85096ec568 | N1 acquisition | failed | — | 1643651 | true | OperationalError: unable to open database file (кеш yfinance) |
| 20261006T103621-754f18207b | N1 acquisition | failed | 20261006T103539-85096ec568 | 1643651 | true | SSLError curl (77): CA-файл по пути с кириллицей; частичный снимок data/snapshots/20261006T103621-754f18207b, a22999ba… |
| 20261006T103625-5202b05cbc | N1 issuer evidence acquisition | completed | — | 1643651 | true | data/evidence/20261006T103625-5202b05cbc, 4156d547…; код не был закоммичен, заменён запуском 20261006T122017-3048321309 |
| 20261006T103702-af69d7e5e6 | N1 acquisition | failed | 20261006T103621-754f18207b | 1643651 | true | NotImplementedError: Option unsupported: 40309 (curl CAINFO_BLOB); частичный снимок 54f97843… |
| 20261006T103809-a4a22ec667 | N1 acquisition | completed | 20261006T103702-af69d7e5e6 | 1643651 | true | data/snapshots/20261006T103809-a4a22ec667, 09edd925…; используемый снимок Yahoo |
| 20261006T104336-dff9099c6b | N1 offline QA | completed | — | 80f75c9 | true | data/derived/20261006T104336-dff9099c6b, d4cde5cf…; без actual payable; заменён запуском 20261006T122144-73228a71eb |
| 20261006T104437-36dd8f9b4a | N1 issuer distribution reconciliation | completed | — | 80f75c9 | true | data/reconciliation/20261006T104437-36dd8f9b4a, b87b4209…; код не был закоммичен, заменён запуском 20261006T122119-c6bfb5c69b |
| 20261006T122017-3048321309 | N1 issuer evidence acquisition | completed | 20261006T103625-5202b05cbc | 590281e | false | data/evidence/20261006T122017-3048321309, 0a9bcea6…; 9 источников, все ok; заменён запуском 20261006T172354-1c0a8ca2d8 |
| 20261006T122119-c6bfb5c69b | N1 issuer distribution reconciliation | completed | 20261006T104437-36dd8f9b4a | c78a319 | false | data/reconciliation/20261006T122119-c6bfb5c69b, cb69e4fc…; предупреждения: unresolved SPY, TLT, LQD, HYG, BIL; нет источника GLD, DBC; заменён запуском 20261006T172415-ce65adb53e |
| 20261006T122144-73228a71eb | N1 offline QA | completed | 20261006T104336-dff9099c6b | 8e677d1 | false | data/derived/20261006T122144-73228a71eb, f9602513…; technical_pass true, data_ready_for_n2 false; код до коммита 72d862e, с текущим кодом не воспроизводится (см. ниже); заменён запуском 20261006T172442-80ef993493 |
| 20261006T122200-a9fd9ddbda | N1 offline replay | completed | 20261006T122144-73228a71eb | cdaaf85 | false | replay_equal true (data_sha256 равен хешу проверяемого QA-снимка по конструкции) |
| 20261006T131812-09887a01da | N1 offline replay | completed | 20261006T122200-a9fd9ddbda | 977eaf6 | false | повтор после исправлений финального ревью; replay_equal true, source_manifest_sha256 09edd925… |
| 20261006T172354-1c0a8ca2d8 | N1 issuer evidence acquisition | completed | 20261006T122017-3048321309 | e4d1669 | false | data/evidence/20261006T172354-1c0a8ca2d8, e7bea822…; 12 источников, все completed; добавлены локальный снимок DBC (sha256 7337eeb7…, проверен при копировании) и два документа GLD |
| 20261006T172415-ce65adb53e | N1 issuer distribution reconciliation | completed | 20261006T122119-c6bfb5c69b | 13bc576 | false | data/reconciliation/20261006T172415-ce65adb53e, f329ac0a…; DBC confirmed, GLD confirmed_no_distributions, EFA/EEM/IEF confirmed; unresolved SPY, TLT, LQD, HYG, BIL с теми же семью событиями |
| 20261006T172434-fbb5c9f554 | N1 issuer corrections | completed | 20261006T172415-ce65adb53e | 8f9e0b4 | false | data/corrections/20261006T172434-fbb5c9f554, da623293…; 7 исправлений: 3 add, 3 replace, 1 remove; corrections.json b8f2ef25… |
| 20261006T172442-80ef993493 | N1 offline QA (скорректированный vintage) | completed | 20261006T122144-73228a71eb | 86b0715 | false | data/derived/20261006T172442-80ef993493, f8934610…; technical_pass true, 4869/4869 сессий, adjustment_breaks 0, actual payable у всех событий, кроме BIL 2008-03-03 |
| 20261006T172453-4d72af092f | N1 issuer distribution reconciliation (скорректированный vintage) | completed | 20261006T172415-ce65adb53e | 5416938 | false | data/reconciliation/20261006T172453-4d72af092f, cded7286…; все десять тикеров confirmed или confirmed_no_distributions, предупреждений нет |
| 20261006T172504-6b932ef79b | N1 offline replay (скорректированный vintage) | completed | 20261006T172442-80ef993493 | 56fdf27 | false | replay_equal true, source_manifest_sha256 09edd925…; data_sha256 равен хешу проверяемого derived-снимка по конструкции |

Закоммиченный до исправления configs/n1.json не содержал ключа `"http_backend": "requests_verified_TLS"`, который есть в конфигурации запуска 20261006T103809-a4a22ec667 (config_sha256 285a4643…, у файла был 0cbb6d67…). Ключ добавлен в файл, канонический хеш файла теперь равен 285a4643….

Первые семь запусков выполнены кодом, который в момент запуска не был закоммичен (dirty_tree true, хеш патча в журнале). Снимок Yahoo 20261006T103809-a4a22ec667 остаётся входом: его байты проверяются по manifest при каждом audit/reconcile, повторная загрузка не делалась. Evidence, reconciliation и QA перезапущены закоммиченным кодом.

Коммиты c78a319, 8e677d1, cdaaf85, fa8fe34, 13bc576, 8f9e0b4, 86b0715, 5416938, 56fdf27 и c41e57e содержат только новые строки журнала. Они сделаны между запусками, чтобы каждый следующий запуск начинался с чистого дерева.

## Команды новых запусков

Git Bash, корень worktree, Python 3.14.0 из .venv. Пакет не установлен в окружение, поэтому путь к src задаётся через PYTHONPATH.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab evidence --root . --parent 20261006T103625-5202b05cbc
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T122017-3048321309 --root . --parent 20261006T104437-36dd8f9b4a
PYTHONPATH=src .venv/Scripts/python -m alpha_lab audit data/snapshots/20261006T103809-a4a22ec667 --payable data/reconciliation/20261006T122119-c6bfb5c69b/payable.json --root . --parent 20261006T104336-dff9099c6b
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T122144-73228a71eb --root . --parent 20261006T122144-73228a71eb
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T122144-73228a71eb --root . --parent 20261006T122200-a9fd9ddbda
```

Первая попытка evidence без PYTHONPATH завершилась ошибкой интерпретатора `No module named alpha_lab` до входа в код проекта; запуск не начался и в журнал не попал.

Вывод replay: `{"replay_equal": true}`.

## Закрытие блокирующих пунктов: команды и порядок

Выполнено 6 октября 2026 года на ветке claude/n1-closure, каждый запуск на чистом дереве. Журнал после каждого запуска коммитился отдельно (`chore: log N1 <назначение> run <run_id>`), затем следующий запуск. Вход Yahoo тот же, 20261006T103809-a4a22ec667, не перезагружался. Локальный снимок DBC лежит в data/manual/dbc-invesco-distribution.json, его sha256 записан в configs/n1_evidence.json; метод получения описан в docs/n1/N1_REPORT.md и в data/manual/dbc-invesco-distribution.capture.json.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab evidence --root . --parent 20261006T122017-3048321309
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T172354-1c0a8ca2d8 --root . --parent 20261006T122119-c6bfb5c69b
PYTHONPATH=src .venv/Scripts/python -m alpha_lab corrections data/reconciliation/20261006T172415-ce65adb53e --root . --parent 20261006T172415-ce65adb53e
PYTHONPATH=src .venv/Scripts/python -m alpha_lab audit data/snapshots/20261006T103809-a4a22ec667 --payable data/corrections/20261006T172434-fbb5c9f554/payable.json --corrections data/corrections/20261006T172434-fbb5c9f554/corrections.json --root . --parent 20261006T122144-73228a71eb
PYTHONPATH=src .venv/Scripts/python -m alpha_lab reconcile data/snapshots/20261006T103809-a4a22ec667 data/evidence/20261006T172354-1c0a8ca2d8 --corrections data/corrections/20261006T172434-fbb5c9f554/corrections.json --root . --parent 20261006T172415-ce65adb53e
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T172442-80ef993493 --root . --parent 20261006T172442-80ef993493
```

Вывод replay: `{"replay_equal": true}`. Каждая команда завершилась с первой попытки, повторов и неудачных запусков в этой серии нет.

## Replay после исправлений ревью (7 октября 2026)

После исправлений R1–R4, RR1–RR2 и мелких замечаний ревью итоговый vintage повторно воспроизведён на коммите 591352a с чистым деревом: запуск 20261007T064823-b7b806e0ce, родитель 20261006T172504-6b932ef79b (предыдущий replay того же vintage), `{"replay_equal": true}`, data_sha256 f89346107cf7da6ca052693d188b8a576a08d42024c86865b0a42a63b1d294f2.

```bash
PYTHONPATH=src .venv/Scripts/python -m alpha_lab replay data/derived/20261006T172442-80ef993493 --root . --parent 20261006T172504-6b932ef79b
```

## Воспроизводимость прежнего derived-снимка

Снимок 20261006T122144-73228a71eb не воспроизводится текущим кодом: нормализованная таблица получила колонки dividend_basis и dividend_correction_source, а corrections.json стал частью derived-снимка, поэтому побайтное сравнение с ним не может совпасть. Его точное воспроизведение зафиксировано до этого изменения: запуск 20261006T131812-09887a01da на коммите 977eaf6 (replay_equal true). Повторно этот снимок не воспроизводился, его вывод в N2 не передаётся: в N2 идёт скорректированный vintage 20261006T172442-80ef993493.
