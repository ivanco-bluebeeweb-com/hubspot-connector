# Scenario Tests — HubSpot Connector

Обязательный журнал прогонов Plausible Scenario Testing (PST) по
`SCENARIO_TESTING_STANDARD.md`. Не переписывать прошлые записи — только
дописывать новые сверху.

---

## 2026-08-21 — первый прогон, Часть D (D1/D2/D3/D4) + честная граница Части B

**Контекст:** приложение — BYOK-коннектор (Private App Access Token,
пользователь подключает СВОЙ собственный HubSpot-портал). У меня нет
живых учётных данных тестового HubSpot-портала, поэтому **Часть B (живые
сценарии с реальными вызовами API против посеянных данных)** и
**D2 (idempotency против реального состояния портала)** честно
НЕ выполнены в этом прогоне — это ограничение окружения, не пропуск
по невнимательности. Зафиксировано явно, а не скрыто.

### D1 — Deploy Verification: ПРОЙДЕНО

- `deploy_app`/`bulk_deploy_apps` выполнен дважды в этой сессии (после
  data_model/event/effects/panels коммита, и после pricing-коммита) —
  оба раза `success_count=1, failure_count=0`. Живой deploy-валидатор
  платформы (единственный источник истины для `ui.*` kwargs, см.
  `known-bug-patterns.md` запись 2026-08-20 про Zapier/Make.com) принял
  весь код, включая новые `panels.py`/`panels_settings.py`, без единого
  CRITICAL.
- `imperal_sdk.validator.validate_manifest_dict()` против пересобранного
  `imperal.json` вернул пустой список — 0 ERROR, 0 WARN на всех 79
  функциях (40 read с `data_model=`, 39 write с
  `event=`/`effects=`/`data_model=`/docstring).
- Полный импорт `main.py` через отдельный процесс SDK venv прошёл чисто
  (79 функций зарегистрировано в `chat`, 5 панелей в `ext._panels`:
  `secrets`, `hubspot_connect`, `hubspot_connect_help`, `hubspot_center`,
  `hubspot_settings`).

### D2 — Idempotency: ЧАСТИЧНО (статический анализ only)

- Не выполнено против реального портала (см. ограничение выше).
- Статически проверено: `disconnect_hubspot` на несуществующий
  `connection_id` возвращает явный `ActionResult.fail`, не падает;
  `_resolve_connection`/`_conn` корректно обрабатывают пустой список
  подключений с понятным сообщением пользователю (не `IndexError`).

### D3 — Security (SSRF + secret leak): ПРОЙДЕНО

- SSRF: приложение не принимает произвольный URL для исходящих запросов
  от пользователя (все запросы идут на фиксированный `api.hubapi.com`,
  кроме `upload_file`, которое требует `source_url` — HubSpot сам
  фетчит файл на своей стороне через свой File Manager API, не эта
  extension; итоговый исходящий HTTP-запрос extension делает только на
  `api.hubapi.com`).
- Secret leak (grep на паттерн из записи 2026-08-19
  `known-bug-patterns.md`): `access_token` используется только в
  `handlers.py::connect_hubspot` (входной параметр, `ClientFail`
  сообщения об ошибке не включают его значение) и внутри
  `_connection_to_dict()`, которая явно НЕ включает `access_token` в
  возвращаемый словарь (только `id`/`title`/`portal_id`/`hub_domain`/
  `connected`) — проверено построчным чтением функции. В `panels.py`
  ввод токена идёт через `ui.Password(param_name="access_token")`, не
  `ui.Input`/`label=`, так что raw-значение не всплывает как открытый
  текст в форме.

### D4 — Regression grep (все известные паттерны из `known-bug-patterns.md`): ПРОЙДЕНО, 0 реальных совпадений

| Паттерн | Команда | Результат |
|---|---|---|
| `resp.status` вместо `.status_code` | `grep -rn 'resp\.status\b' *.py \| grep -v status_code` | 0 |
| Ручной `confirm: bool` антипаттерн | `grep -rn 'confirm.*bool' schemas.py`; `grep -rn 'params\.confirm' handlers*.py` | 0 |
| `sdl.Entity` без `id`/`title` дефолта | AST-скан всех классов-наследников `sdl.Entity` в `schemas.py` (29 классов) | 0 отсутствующих полей |
| Несуществующие `ui.*` kwargs (`copyable`, `confirm=` на Button/Call, `full_width` на Form, `label=` на Input) | `grep` по каждому паттерну в `panels*.py` | `full_width=True` на `ui.Button` (валидно, тот же паттерн что MuleSoft `_settings_button()`); `ui.Input` используется только с `param_name`/`placeholder` — корректный паттерн, не совпадение бага |
| `.pop(field, None)` перед `store.update()` | `grep -rn '\.pop(' *.py` | Только `sys.modules.pop(_mod, None)` в `main.py` — безобидная чистка кеша модулей, не наш класс |

### Часть B — живые сценарии: НЕ ВЫПОЛНЕНО (задокументированное ограничение)

Требует реального HubSpot Private App Access Token от подключённого
портала для прогона: создать контакт → связать со сделкой → залогировать
активность → батч-обновить стадию сделки → архивировать. Не выполнено в
этой сессии за отсутствием тестовых учётных данных. **Следующий шаг перед
реальной публикацией на большой охват пользователей:** прогнать этот
сценарий вручную (Влад подключает свой или тестовый HubSpot-портал через
`connect_hubspot` в панели) хотя бы один раз, чтобы поймать поведенческие
баги, которые статический анализ не видит (см. `SCENARIO_TESTING_STANDARD.md`
о том, зачем Часть B существует отдельно от статического аудита).

**Итог прогона:** Части D1/D3/D4 чистые, D2 частично (только статически),
Часть B заблокирована отсутствием живого портала — не сокрыто, а
зафиксировано как явное условие приёмки перед следующим шагом.
