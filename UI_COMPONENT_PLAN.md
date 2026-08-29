# HubSpot Connector — UI component plan

Источники: `ui-primitives-reference.md`, `UI_INTERFACE_STANDARD.md`, `concepts/panels.md`.
Основано на `POST_CONNECT_EXPERIENCE.md` этого приложения.

## 1. Компоненты

| Экран | Примитивы | Почему именно эти |
|---|---|---|
| Sidebar (left) | `ui.Column`(align="start") + `ui.Text`(portal name/domain) + `ui.Divider` + navigation `ui.ListItem`(без avatar/badge декора — просто title) + `ui.Button`("App settings") | Без карточек по стандарту; ListItem кликабелен и достаточен для навигации без визуального оформления. |
| Pipeline Board (center, `center_overlay=True`) | `ui.Stats`(Open/Won/Lost + total value) + `ui.Tabs`(по object type: Contacts/Companies/Deals/Tickets) → внутри каждой вкладки `ui.DataTable` | HubSpot один портал держит 4 разных объекта — `Tabs` разводит их без 4 отдельных панелей. |
| Deal/Contact Detail | Back-button + `ui.KeyValue`(properties) + `ui.Accordion`(sections: Associations, Engagements/Timeline, Files) + `ui.Timeline`(engagements: call/email/meeting/note) | `Accordion` даёт collapsible-доступ к разным related-блокам записи без перегрузки экрана; `Timeline` для engagement-истории (это буквально хронология с иконками по типу активности). |
| Pipeline Health Chart | `ui.Chart`(type="bar", x_key="stage") | Числовая сводка "сделки по стадиям" лучше визуализируется столбцами, чем таблицей. |
| Duplicate Contacts Finder | `ui.List`(selectable=True, bulk_actions=[Merge]) | `find_duplicate_contacts` возвращает группы — `selectable` list с bulk-действием "Merge" прямое попадание. |
| Property/Object Schema Viewer | `ui.Tree`(nodes=object→properties) | Схема кастомных объектов иерархична (объект → группы полей → поля). |
| App Settings | `ui.Accordion`([Connections+Disconnect, Webhooks CRUD, Default Pipeline Select]) | Централизованные настройки по стандарту. |

## 2. User flow

1. **SESSION INIT** → `__panel__hs_sidebar` (left) рендерит портал + навигацию
   (Contacts/Companies/Deals/Tickets/Pipeline Health).
2. Root ставит `auto_action=ui.Call("__panel__hs_center", view="deals")` только если
   `not active_view` — первый визит сразу открывает самую частую вкладку (Deals), не
   пустой центр.
3. **Клик по вкладке в Tabs** внутри уже открытого center panel — это client-side
   переключение `ui.Tabs`, НЕ отдельный `ui.Call` (Tabs сам хранит `default_tab`); но
   при первом рендере каждой вкладки данные уже должны быть в `content` — значит
   handler одного `__panel__hs_center` при вызове обязан подгружать данные всех 4
   вкладок сразу (или лениво по `on_change` — SDK референс не описывает `on_change`
   у `ui.Tabs`, поэтому безопасный вариант — подгрузка всех вкладок за один fetch).
4. **Клик по строке DataTable** (любой вкладки) → `ui.Call("__panel__hs_detail",
   object_type="deal", record_id=...)` — отдельный center panel id для Detail (не тот
   же `hs_center`, т.к. Detail и List — разные center overlay, между которыми back-button
   переключается явным `ui.Call("__panel__hs_center", view="deals")`).
5. **"Merge duplicates"** (bulk_actions на List) → `@chat.function merge_hubspot_contacts`
   (обёртка над `list_associations`+ручным merge) → `ActionResult(refresh_panels=
   ["hs_center"])`.
6. **App settings** → center overlay, Accordion с 3 секциями, каждое поле — отдельный
   save-вызов с зелёным toast.

## 3. Конкретные экраны/карточки

- **Sidebar**: Portal name (Text) → Divider → "Contacts" / "Companies" / "Deals" /
  "Tickets" / "Pipeline Health" (ListItem, каждый — `on_click=ui.Call("__panel__hs_center",
  view=...)`) → Divider → "App settings" (Button secondary, последний).
- **Center — Pipeline Board**: Header("Deals", subtitle="42 open · $128,400") → Stats
  (Open/Won/Lost) → Tabs([Contacts, Companies, Deals, Tickets] — каждый DataTable с
  колонками, релевантными объекту: Deals → Name/Stage/Amount/Close Date).
- **Center — Deal Detail**: Back("← Назад к Deals") → Header(deal.name) → KeyValue
  (Stage/Amount/Close Date/Owner) → Accordion([Associations: List контактов/компаний],
  [Engagements: Timeline], [Files: List]) → Row(Edit, Move Stage, Log Activity).
- **Pipeline Health**: Chart(type="bar", data=stage_counts) + KeyValue(win rate/avg deal
  age) — отдельный `view="pipeline_health"` того же `hs_center` panel.
- **App Settings**: Accordion([Connections: список порталов + Disconnect],
  [Webhooks: List + create/delete Form], [Defaults: Select default pipeline]).
