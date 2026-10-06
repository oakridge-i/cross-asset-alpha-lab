# Отчёт N0: проверка предпосылок

6 октября 2026 года, Europe/Moscow. Задача: проверить осуществимость нулевого бюджета и превратить общий план в протокол до результатов стратегий. Доходности H1/H2, выбор модели и оптимизация не запускались.

## Что сделано и зачем

Прочитаны NEW_CHAT_BRIEF, MASTER_PLAN, NEW_PROJECT_SETUP, AGENTS.template и итоговые документы AAPL. Создан отдельный локальный репозиторий; обязательные документы и пустой реестр попыток. Сохранены копии исходных задания/настройки и плана; AGENTS скопирован точно. Протокол уточняет формулы, веса, cash, время, selection и критерии выводов, чтобы код не принимал экономические решения задним числом.

Для работы использованы Superpowers using-superpowers/brainstorming/verification-before-completion и scoped analyze-data-quality. N0 — подготовка исследовательской спецификации; продуктовый Python-пакет и N1–N8 ещё не реализованы. Implementation plan навыка writing-plans будет нужен для следующего программного этапа; он не выдаётся за выполненную реализацию.

## Источники и границы

Проверка непосредственно query1.finance.yahoo.com/v8/finance/chart: по одному дневному запросу на каждый из десяти ETF от 1990 до исключающего 2026-10-06, events div/splits/capitalGains. Конечная наблюдаемая сессия у всех 2026-10-05. В исходной проверке все HTTP200; есть Adj Close, USD и America/New_York. Дубликатов timestamp и нечисловых/неположительных OHLC в возвращённых строках не найдено. Это не проверяет отсутствующие между ними сессии, точность рынка, объём или весь event history. Receipt [source_probe.json](source_probe.json), исполняемая проверка [probe_sources.py](probe_sources.py). Повторный расширенный receipt [source_probe_extended.json](source_probe_extended.json) добавляет OHLC-отношения, поля объёма, порядок дат и годовые counts actions.

| ETF | Первые OHLC | Строк в исходном ответе | Dividend events | Split events |
|---|---|---:|---:|---:|
| SPY |1993-01-29|8478|136|0|
| EFA |2001-08-27|6313|47|1|
| EEM |2003-04-14|5907|47|2|
| IEF |2002-07-30|6085|291|0|
| TLT |2002-07-30|6085|289|0|
| LQD |2002-07-30|6085|290|0|
| HYG |2007-04-11|4903|233|0|
| GLD |2004-11-18|5503|0|0|
| DBC |2006-02-06|5198|9|0|
| BIL |2007-05-30|4869|128|1|

Grain: одна строка на ticker/session, события отдельным потоком. Количество distributions не доказывает их полноту; особенно sparse BIL128 требует проверки истории распределений/нулевых месяцев у эмитента. Никакого вывода «ежемесячно значит обязано быть ненулевое событие каждый месяц» не сделано.

Расширенный повтор завершился с exit0. У всех десяти рядов 0 нарушений порядка/дубликатов, положительности и отношений Low<=Open/Close<=High; volume заполнен и неотрицателен. Общий пересекающийся набор содержит 4869 наблюдаемых сессий, на 2008-12-31 доступно 402 предшествующих доходности — больше 252 требуемых. В BIL отсутствуют ненулевые dividend events за 2010/2012–2015/2021; источник ещё не сверён с нулевыми выплатами эмитента. Эти годы не объявлены ошибкой данных автоматически. Проверка биржевого календаря не выполнялась; отсутствие OHLC-проблем в возвращённых строках не доказывает отсутствие пропущенных сессий.

Общий начало 2007-05-30 ограничивает годовой прогрев. Полный development стартует 2009, тогда для yearly2014 доступны пять предшествующих полных лет. Это решение по источнику, не по доходности. Обновлённый протокол сохраняет предварительные WF2014–2022 и reserved2023–2025. Ответ пользователя о прежнем просмотре «Не уверен / не помню» означает неизвестную экспозицию; термин независимый holdout не применяется.

## Эмитенты: что подтверждено

Текущие классы/мандаты и даты inception прочитаны в первичных источниках; показатели доходности эмитентов не использовались для отбора ETF. Веб-страницы являются текущими материалами, не полным архивом historical mandates.

- [SPY — SSGA](https://www.ssga.com/us/en/individual/etfs/state-street-spdr-sp-500-etf-trust-spy): S&P500, inception1993-01-22.
- [EFA — iShares](https://www.ishares.com/us/products/239623/ishares-msci-eafe-etf): развитые equity вне США/Канады, inception2001-08-14.
- [EEM — iShares](https://www.ishares.com/us/products/239637/ishares-msci-emerging-markets-etf): emerging markets, inception2003-04-07.
- [IEF — iShares](https://www.ishares.com/us/products/239456/ishares-710-year-treasury-bond-etf): Treasury7–10years, inception2002-07-22.
- [TLT — iShares](https://www.ishares.com/us/products/239454/ishares-20-year-treasury-bond-etf): Treasury20+years, inception2002-07-22.
- [LQD — iShares](https://www.ishares.com/us/products/239566/ishares-iboxx-investment-grade-corporate-bond-etf): investment-grade corporate, inception2002-07-22.
- [HYG — iShares](https://www.ishares.com/us/products/239565/ishares-iboxx-high-yield-corporate-bond-etf): high-yield corporate, inception2007-04-04.
- [GLD — эмитент](https://www.spdrgoldshares.com/usa/gld/): physical gold less expenses, inception/listing2004-11-18. Там же раскрыта замена London PM Fix на LBMA Gold Price PM с 2015-03-20.
- [DBC — Invesco](https://www.invesco.com/us/en/financial-products/etfs/invesco-db-commodity-index-tracking-fund.html): commodity futures плюс collateral income; inception2006-02-03 подтверждён результатом поиска по официальной странице и [factsheet эмитента](https://www.invesco.com/us-rest/contentdetail?contentId=1fd207c649400410VgnVCM10000046f1bf0aRCRD). Прямое открытие factsheet перенаправлялось на country-splash/404; полноценный локальный PDF не сохранён. Отдельный материал [Commodity ETFs and ETPs](https://www.invesco.com/us/en/solutions/invesco-etfs/commodity-investing.html) подтверждает methodology update с 2025-11-10. Официальный product source также раскрывает смену managing owner2015-02-23.
- [BIL — SSGA](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-bloomberg-1-3-month-t-bill-etf-bil): T-bills1–3months, inception/listing2007-05-25, monthly distributions.

У девяти инструментов, кроме GLD, первая дата источника позднее inception; это пропуски начального охвата, не доказательство плохой последующей истории. Начальную доступность определяет конкретная таблица, а не предположение о полноте с inception.

У iShares публичные distribution tables включают Ex-Date, Record Date, Payable Date и amount (например [EFA](https://www.ishares.com/us/products/239623/ishares-msci-eafe-etf), раздел Distributions). Их доступность сейчас не подтверждает архив всех выплат 2007–2026. SSGA предоставляет distribution schedules; глубина архива для BIL/SPY ещё не установлена.

## Ограничения и реакция

| Риск | Свидетельство / уверенность | Влияние | Принятое действие |
|---|---|---|---|
| Нет payable dates в chart | Все ненулевые dividend event имеют только amount/date; высокая | Нельзя считать ex-date сразу свободными деньгами | Receivable, actual dates где есть, missing proxy+10 calendar days; stress0/30. |
| Split/price basis не сертифицирована | EEM3:1 в 2008, BIL1:2 в 2017 в receipt; высокая для наличия события, семантика OHLC ещё не проверена | Двойной сплит и неверные количества могут разрушить NAV | N1 блокирует N2 до сверки; auto_adjust=False недостаточно. |
| BIL sparse actions |128 ненулевых событий за 19 лет; высокая для count, причина неизвестна | Возможна неполнота доходности cash reference | Годовой event profile и сверка эмитента; не подменять отсутствие события нулём автоматически. |
| Retrospective vendor data | Снимок получен сейчас, нет исторических archived vintages | Availability assumptions и исторические revisions | Causal prefixes, hashes, vintage; не заявлять true point-in-time. |
| Нет opening auction/spread archive | Дневной Open,10bps задано планом | Реальное исполнение отличается | Модельное next-open, расходы/lag/резерв stress, нет real-trading claims. |
| Fixed survivors | Universe составлен сегодня | Survivorship/selection bias | Только эта выборка; class exclusions и раскрытие. |
| Mandates изменялись | DBC index2025, owner2015; GLD reference2015 | Неизменный ticker не гарантирует неизменный экономический объект | Описать события, before/after и without-DBC; не подклеивать индекс. |
| Право использования/распространения не установлено полностью | README yfinance предупреждает о personal-use/terms; прямые terms не прочитаны | Техническая доступность не равна лицензии | Только локальная учебная работа; raw в gitignore; публикация/paid отдельны. |
| Нет независимости reserved | Ответ пользователя «Не уверен / не помню» | Ограничена сила статистических выводов | Зарезервированная историческая проверка, будущий prospective stream. |

N0 определяет последствия этих пробелов, а не объявляет их устранёнными. Полный QA с календарями, OHLC-consistency, revisions, контрольными ценами/событиями и stop rules — N1. Пока не подтверждённые нулевые distributions и split basis запрещают переход к экономическим выводам.

## Документация адаптера и литература

[Официальный download](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html) описывает отдельные настройки auto_adjust/actions/repair/keepna и исключающий end; поэтому defaults не принимаются молча. [yfinance README](https://github.com/ranaroussi/yfinance) говорит об учебном/исследовательском применении, personal use и самостоятельной проверке прав Yahoo. Лицензия кода не даёт автоматически права на данные. Доступ к полным Yahoo terms через web не удался; это зарегистрированный неизвестный вопрос, не положительное юридическое заключение.

Исследовательская мотивация: [Time Series Momentum](https://www.aqr.com/Insights/Research/Journal-Article/Time-Series-Momentum), [Value and Momentum Everywhere](https://www.aqr.com/insights/research/journal-article/value-and-momentum-everywhere). Отдельные диагностики множественного поиска: [Deflated Sharpe Ratio](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf), [Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). Они поддерживают дисциплину сравнения и отбора; не подтверждают прибыльность этих шести вариантов. Во время N0 новые гипотезы из литературы не добавлены.

## Следующий конкретный шаг

N1: зафиксировать Python-окружение и source adapter, DATA_CONTRACT.md, неизменяемый локальный snapshot с manifest, coverage/calendar/actions QA, контроль EEM2008 и BIL2017, coverage payable dates с фактическими/proxy флагами. Проверить контрольные события/цены у эмитентов; вопросы split basis, distribution полноты и material revisions должны иметь явный verdict. Производственные H1/H2 NAV, оптимизация и reserved-performance reports не входят в N1.

Критерии завершения N0 и результаты каждого — [STATUS.md](../../STATUS.md); машинное свидетельство финальной проверки — [verification.json](verification.json). N0 — завершённая спецификация с раскрытыми ограничениями, не готовый набор сертифицированных данных N1.
