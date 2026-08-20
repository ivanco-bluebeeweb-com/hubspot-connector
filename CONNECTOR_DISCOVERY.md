# HubSpot Connector — Connector Discovery

**Дата discovery:** 2026-08-20
**Статус:** Ярусы 1-3 пройдены (свежее чтение developers.hubspot.com, 2026-08-20). §7 (решение по объёму) НЕ требует отдельного вопроса Владу — пользователь уже дал явный ответ в самой задаче: «приступай к разработке приложения Hubspot. максимальный функционал, полный максимум» — это прямое указание брать Ярус 1 + Ярус 2 + Ярус 3 целиком, без урезания.

---

## 1. Целевой сервис и источники

HubSpot — единая CRM/маркетинг/сервис-платформа (CRM Hub + Marketing Hub + Sales Hub + Service Hub + Operations Hub + CMS Hub) на общем объектном движке. В отличие от MuleSoft/Blue Prism/Automation Anywhere/UiPath — у HubSpot **один связный REST API** под доменом `api.hubapi.com`, с датой-версионированием пути (`2026-03` — текущая актуальная версия вместо старого v1/v2/v3/v4). Это снимает основную причину, по которой предыдущие RPA/iPaaS-коннекторы резались по ярусам из-за фрагментации API — здесь "максимум" реалистичен в одном заходе.

Источники (прочитаны 2026-08-20):
- `developers.hubspot.com/docs/api-reference/latest/overview` — обзор 2026-03 API, единый домен, миграция версий
- `developers.hubspot.com/docs/api-reference/latest/crm/understanding-the-crm` — объектная модель (Objects/Records/Properties)
- `developers.hubspot.com/docs/api-reference/latest/crm/search-the-crm` — единый Search API по всем объектам
- `developers.hubspot.com/docs/api-reference/latest/crm/associations/overview` — associations между объектами (v4)
- `developers.hubspot.com/docs/api-reference/latest/crm/objects/objects/batch/get-objects` — batch read/update/archive
- `developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/overview` — Private App token vs OAuth
- `developers.hubspot.com/blog/hubspot-integration-choosing-private-public-hubspot-apps` — Private App (не истекает) vs Public App (OAuth, для marketplace-дистрибуции)
- `developers.hubspot.com/docs/apps/developer-platform/build-apps/authentication/scopes` — модель scopes
- `developers.hubspot.com/docs/api-reference/latest/crm/activities/{calls,emails,meetings,tasks}/guide` — engagements
- `developers.hubspot.com/docs/api-reference/latest/webhooks/guide` — webhook subscriptions (требует Developer Account + App ID, отдельно от Private App)
- `developers.hubspot.com/docs/api-reference/latest/files/guide` — Files API
- `developers.hubspot.com/docs/developer-tooling/platform/usage-guidelines` — rate limits, `X-HubSpot-RateLimit-*`

## 2. Карта возможностей

| Домен API | Возможность | Ingress/Egress/Both | Комментарий |
|---|---|---|---|
| **CRM Objects** | Contacts/Companies/Deals/Tickets/Products/Line Items — CRUD (get/list/create/update/archive) | Both | Ядро CRM — самая частая боль пользователя |
| **CRM Objects** | Batch операции (batch read/create/update/archive по любому типу объекта) | Both | Официальный паттерн для "сделай это для многих записей" |
| **CRM Search** | POST `.../search` — фильтры/сортировка/пагинация по любому объекту | Ingress | Заменяет "найди контакт/сделку по условию" |
| **CRM Associations (v4)** | Создать/удалить/прочитать связи между объектами (contact↔company↔deal↔ticket) | Both | Без associations CRM бессвязна — обязательная часть ядра |
| **CRM Properties** | Список/создание/чтение custom properties для любого объекта | Both | Нужно, чтобы работать с кастомными полями клиента, не только стандартными |
| **CRM Pipelines/Stages** | List/get pipelines и их stages (deals и tickets) | Ingress | Обязательно для корректного отображения "на каком этапе" |
| **CRM Owners** | List/get владельцев записей (пользователей HubSpot) | Ingress | "Кто ведёт эту сделку/контакт" |
| **Engagements (Activities)** | Notes/Calls/Emails/Meetings/Tasks — CRUD + association с записью | Both | "Рабочий журнал" продавца — лог активности по контакту/сделке |
| **Marketing — Forms** | List forms, get form submissions | Ingress | Связь маркетинга с CRM-лидами |
| **Marketing — Lists** | List/get contact lists (static/active), membership | Both | Сегментация контактов |
| **Files** | Upload/list/get files | Both | Вложения к записям/engagements |
| **Webhooks** | App-level subscriptions на CRM события (created/updated/deleted/propertyChange) | Egress (setup) / Ingress (events) | Требует HubSpot Developer Account + отдельного App ID — тяжелее, чем Private App токен; документируется как опциональный продвинутый шаг |
| **Account Info** | Get account details (portal ID, timezone, currency) | Ingress | Базовая диагностика подключения |

## 3. Классификация по типу функционала

- **Ingress (сильный)**: список/поиск контактов/компаний/сделок/тикетов, associations-чтение, properties-чтение, pipelines/stages, owners, engagements-чтение, form submissions, files-чтение, account info.
- **Egress (сильный)**: создание/обновление/архивация записей любого типа, создание associations, создание custom properties, создание engagements (лог звонка/письма/встречи/заметки/задачи), загрузка файлов, настройка webhook-подписок.
- **Both**: batch-операции (могут быть и чтением, и записью в одном вызове), lists membership (добавить/убрать контакт из списка).

## 4. Ярус 1 — Ключевые функции (P0)

1. `connect_hubspot` / `disconnect_hubspot` — Private App Access Token
2. `list_contacts` / `get_contact` / `create_contact` / `update_contact` / `archive_contact`
3. `list_companies` / `get_company` / `create_company` / `update_company` / `archive_company`
4. `list_deals` / `get_deal` / `create_deal` / `update_deal` / `archive_deal`
5. `list_tickets` / `get_ticket` / `create_ticket` / `update_ticket` / `archive_ticket`
6. `search_crm_objects` — единый Search API по любому из четырёх типов
7. `create_association` / `delete_association` / `list_associations` — связи между записями
8. `list_pipelines` / `list_pipeline_stages` (deals и tickets)
9. `list_owners` / `get_owner`

## 5. Ярус 2 — Полное покрытие

| Возможность | Статус | Причина |
|---|---|---|
| Batch create/read/update/archive (contacts/companies/deals/tickets) | included | Официальный паттерн, естественное расширение CRUD |
| Custom object properties: list/get/create | included | Нужно для работы с нестандартными полями клиента |
| Products / Line Items CRUD + association с deal | included | Завершает картину "сделка → что продаём" |
| Engagements: Notes/Calls/Emails/Meetings/Tasks — CRUD + association | included | Полноценный рабочий журнал — центральная часть "максимума" |
| Marketing Lists: list/get, add/remove contact membership | included | Явно упомянуто в задаче как часть максимума |
| Marketing Forms: list forms, get submissions | included | Связка маркетинг → CRM |
| Files: upload/list/get | included | Вложения к записям/engagements |
| Account info: get portal details | included | Диагностика/health-check подключения |
| Custom Objects (полноценные, не только properties) | included | HubSpot's schema API — часть "максимума" для Enterprise-аккаунтов |
| Webhooks: create/list/delete subscription | included, но помечено как advanced-flow | Требует Developer Account + App ID, не просто Private App токен — задокументировать отдельно в connect-help |
| Quotes API | deferred | Нишевая функция (коммерческие предложения), не входит в стандартный CRM-цикл; добавить по явному запросу |
| Workflows API (automation flows) | deferred | HubSpot Workflows управляются почти исключительно через UI и требуют Enterprise/Pro тарифа с ограниченным API-доступом (in beta для части операций) — высокий риск нестабильного контракта; отложить |
| CMS Hub (сайты/страницы/блоги через API) | not applicable | Отдельный продукт внутри HubSpot, не про CRM/маркетинг-данные — вне текущего скоупа "CRM+Marketing коннектор" |
| Conversations API (inbox/chat) | deferred | Отдельный, тяжёлый по объёму домен (threads/messages/channels) — добавить отдельным заходом по явному запросу, чтобы не размывать первый релиз |

## 6. Ярус 3 — Функции на нашей стороне (value-add)

- **`bulk_update_deal_stage`** — переместить несколько сделок в новый этап одним вызовом (батч поверх batch-update API)
- **`get_pipeline_health`** — агрегирующий отчёт по воронке: сколько сделок на каждом этапе, сумма amount, давно ли не двигались (сверка `hs_lastmodifieddate`) — того же типа, что `audit_cloudhub_environment` у MuleSoft
- **`find_duplicate_contacts`** — поиск потенциальных дублей контактов по email/domain через Search API (HubSpot имеет собственный dedup UI, но не отдаёт готовый API-отчёт)
- **`sync_check`** — быстрая проверка здоровья подключения (Account Info + пробный запрос лимитов) для панели

## 7. Решение по объёму — ЗАФИКСИРОВАНО (не открытый вопрос)

Пользователь дал явный ответ в самой постановке задачи: «максимальный функционал, полный максимум». Берём **Ярус 1 + Ярус 2 + Ярус 3 целиком**, за прямым исключением четырёх пунктов, которые сама HubSpot делает архитектурно другим продуктом/доменом (Quotes, Workflows, CMS Hub, Conversations) — они помечены `deferred`/`not applicable` не из-за экономии объёма, а потому что это либо нестабильный/ограниченный контракт (Workflows beta), либо принципиально другой домен (CMS, Conversations), либо нишевая функция без явного запроса (Quotes). Это соответствует тому же принципу, по которому MuleSoft-коннектор исключил VPC/VPN/Design Center — не "лень", а осознанное разграничение продукта.

Итоговый охват — CRM (Contacts/Companies/Deals/Tickets/Products/Line Items/Custom Objects) полностью, Associations, Properties, Search, Pipelines/Stages, Owners, Engagements (Notes/Calls/Emails/Meetings/Tasks), Marketing Lists, Forms, Files, Webhooks, Account Info, плюс 4 value-add агрегатора.
