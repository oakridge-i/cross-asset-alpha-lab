# Проверка AAPL перед возможным переносом

6 октября 2026, read-only. Источник C:\Quantitive\model 1 aapl; release worktree <workspace>\aapl-finalization.

| Проверка | Фактическое состояние |
|---|---|
| Основной каталог | main, HEAD ed4fd39518f1f58ad4065512bec8223443186bf3, clean |
| Local origin/main | ed4fd39518f1f58ad4065512bec8223443186bf3 |
| Локальный v0.6.0 peeled |4d69932382af4a7bcaddfb4621f0973ea2d820c2|
| Release worktree |codex/aapl-final-release, HEAD4d69932382af4a7bcaddfb4621f0973ea2d820c2, clean|
| Прямой remote refs check |main ed4fd39518f1f58ad4065512bec8223443186bf3; annotated tag0300c8182c64a9c0b40fae1b4cb258340ae62c45, peeled4d69932382af4a7bcaddfb4621f0973ea2d820c2|

Чтение git старого каталога использовало одноразовый `-c safe.directory`, без глобальной настройки. Первое HTTPS git ls-remote не прошло Windows schannel; повтор с `-c http.sslBackend=openssl` прошёл, проверка TLS не выключалась. Fetch, pull, checkout и mutation старого проекта не выполнялись. Remote main проверен напрямую; состояние merge PR отдельно через GitHub API не запрашивалось.

Прочитаны [итоговый отчёт](../../../aapl-finalization/docs/final/research_report.md), [reproduction](../../../aapl-finalization/docs/final/reproduction.md), [review](../../../aapl-finalization/docs/final/review.md), [execution record](../../../aapl-finalization/docs/final/execution_record.md), release_manifest и final_tests.log.

149 passed в 96.44s — сохранённая проверка AAPL, прочитанная в логе, не новая проверка в этом чате. Из сохранённых документов: два frozen searches, offline repeats,72cost/lag scenarios на снимок,202320daily rows. В updated общем периоде CAGR nested ensemble4.74% vs50%AAPL11.43%; убедительное преимущество/alpha не установлены. Эти числа не использовались для подбора нового протокола по результатам H1/H2.

release_manifest описывает состояние локального выпуска до последующей публикации; поле remote_mutations=false не означает, что PR/main сегодня не опубликованы. Прямое сравнение refs подтверждает более позднее состояние из briefing. Старый preview принадлежит 91e769e и не переносится как свежий результат.

## Материал для выборочного переноса

| Источник в release | Возможная польза | Повторная проверка нового контракта |
|---|---|---|
|src/quant_backtest/research_config.py|YAML/config validation pattern|Новая schema, universe, available_at, next-open параметры. Не копировать старые defaults.|
|src/quant_backtest/data_quality.py и closeout.py|Snapshot/manifest/hash и effective-period pattern|OHLC/actions, split basis, сохранение raw/vintage, качество по каждому ETF, не только adjusted close.|
|src/quant_backtest/metrics.py|Drawdown, aligned excess returns, формулы метрик|Единое sample ddof=1 и sessions-CAGR; в legacy есть отдельная calendar-CAGR функция, её нельзя смешать с report формулой.|
|tests/test_a1_accounting.py, test_a2_financial_invariants.py|Ручные финансовые инварианты|Несколько активов, actual BIL, receivable/cash, Open и order quantities вместо close allocations.|
|tests/test_closeout.py|Replays/effective snapshot regression|Новый формат multi-asset NAV/trades/position receipts; retain original и effective hash.|
|tests/test_methodology_v05.py, test_m1_foundation.py|Материал для тестов причинности|Future price/action/source-vintage не меняют past decisions; calendar вместо искусственного freq=B.|
|src/quant_backtest/reports.py, reporting scripts|Вывод source-backed таблиц|Новый contract полей и явный статус exploratory/reserved/prospective.|

Просмотрены имена модулей/тестов, фактические metrics.py и research_data.py; таблица — кандидаты на дальнейший аудит, не сертификат каждого указанного модуля. Полный исходный код этих модулей будет прочитан перед переносом. Сырые snapshots не скопированы в новый repo.

Не переносить автоматически engine.py/costs.py/continuous.py и research orchestration. AAPL next-close, синтетическая денежная доходность BIL, другое sizing/settlement; эти предположения не удовлетворяют новому RESEARCH_PROTOCOL. Ни одна строка продуктового кода AAPL на N0 не перенесена.

При будущем переносе записывать original repo, tag, SHA, path, фактический diff, лицензию и новые проверки. Применимость формулы важнее сохранения интерфейса старого проекта.
