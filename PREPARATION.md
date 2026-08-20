# HubSpot Connector — Preparation

**Статус:** Фаза 1 (Discovery + архитектурные решения) завершена. Влад
подтвердил объём релиза 2026-08-20 — «максимальный функционал, полный
максимум» (Ярус 1+2+3, см. `CONNECTOR_DISCOVERY.md` §7 для точной границы).
**Владелец продукта:** vlad@bluebeeweb.com
**Дата подготовки:** 2026-08-20, v0.1
**Vikunja task:** #2197 (BBW Imperal Apps), [App Development].

**Почему сейчас:** HubSpot — крупнейшая CRM/маркетинг-платформа SMB/mid-market
сегмента. В портфеле Imperal есть Asana/Trello/Notion (task/project) и
Sales/Brand Strategy Hub (внутренняя лёгкая CRM-логика самого Imperal), но
нет ни одного внешнего CRM-коннектора к реальным данным клиента о контактах/
сделках/тикетах. В отличие от предыдущей серии iPaaS/RPA-коннекторов
(MuleSoft/n8n/Make.com/Power Automate/UiPath/Automation Anywhere/Blue Prism),
у HubSpot один связный REST API (`api.hubapi.com`, версия `2026-03`) — это
позволяет реализовать «максимум» без фрагментации по нескольким разным
API-семьям.

**Процесс-стандарт применяется без изменений** (закреплён в
`PRICING_POLICY.md` после инцидента с MuleSoft 2026-08-20): `deploy_app` →
`update_pricing` (на статусе `suspended`) → `submit_for_review`, никогда в
другом порядке.

---

## 1. Паспорт приложения

**Название в Marketplace (display_name): «HubSpot»**. Внутренний
app_id/папка: `hubspot-connector`.

**HubSpot Connector** — коннектор к CRM/Marketing Hub HubSpot через
единый REST API (`api.hubapi.com`, `2026-03`). BYOK: пользователь
подключает свой собственный HubSpot-аккаунт через Private App Access
Token (создаётся внутри самого HubSpot-портала, Settings → Integrations
→ Private Apps — не истекает, ротируется вручную владельцем). Imperal
ничего не хостит и не проксирует помимо самого запроса к api.hubapi.com.

## 2. Почему Private App Token, а не публичный OAuth (см. `CONNECTOR_DISCOVERY.md`)

HubSpot поддерживает два режима аутентификации для стороннего кода:
- **Private App Access Token** — создаётся владельцем ОДНОГО портала внутри
  самого HubSpot UI, токен не истекает, требует только назначить нужные
  scopes при создании приложения. Идеальный BYOK-паттерн: не требует от
  Imperal хостинга OAuth-callback, ровно та же архитектура, что уже
  подтверждена для n8n/Make.com/MuleSoft/Power Automate.
- **Public App (OAuth 2.0, authorization code + refresh token)** — нужен
  только для распространения приложения через сам HubSpot Marketplace на
  МНОЖЕСТВО чужих порталов централизованно. Это требует создания
  Developer Account + App ID на стороне HubSpot и хостинга OAuth-обмена —
  не нужен для BYOK-модели, где каждый пользователь подключает свой
  собственный портал напрямую.

Решение: Private App Access Token как основной и единственный путь
аутентификации, аналогично тому, как Slack Connector использует Bot Token,
а не App Distribution OAuth.

## 3. Почему один секрет с JSON-массивом («порталов»), не плоский токен

HubSpot-аккаунты организованы как отдельные «порталы» (portal/hub id) —
агентство или пользователь с несколькими брендами вполне может вести
несколько порталов. Тот же структурный паттерн, что уже решён для
MuleSoft (`mulesoft_connections`), Slack (`workspaces`) и Power Automate
(`connections`): один секрет `hubspot_connections` хранит JSON-массив
`{id, label, access_token, portal_id}`. Параметр `connection_id` на
каждом инструменте адресует конкретный портал (по умолчанию — единственный
подключённый, если он один).

## 4. Архитектура кода (файлы)

Смоделировано по MuleSoft/Aidentika (последние два эталона):
- `app.py` — Extension/ChatExtension декларация, секрет, health_check
- `schemas.py` — общие Pydantic-модели (NoParams, ConnectHubspotParams,
  общие CRM-параметры)
- `hubspot_client.py` — HTTP-клиент: аутентификация Bearer-токеном,
  единая обёртка над `/crm/objects/{objectType}/...` (генерик по типу
  объекта — так официально устроен и сам HubSpot API), обработка
  401 (неверный токен) / 403 (не хватает scope) / 429 (rate limit,
  `X-HubSpot-RateLimit-*` заголовки) / 404.
- `handlers_crm.py` — Contacts/Companies/Deals/Tickets/Products/Line
  Items CRUD (тонкие обёртки над generic client-функцией) + Search +
  Batch + Associations + Properties + Pipelines + Owners
- `handlers_engagements.py` — Notes/Calls/Emails/Meetings/Tasks
- `handlers_marketing.py` — Lists, Forms, Files, Custom Objects, Webhooks
- `handlers_admin.py` — connect/disconnect/account info + Ярус 3
  value-add агрегаторы (`get_pipeline_health`, `find_duplicate_contacts`,
  `bulk_update_deal_stage`, `sync_check`)
- `panels.py` / `panels_settings.py` — UI (список подключённых порталов,
  форма подключения, без карточек — по UI_INTERFACE_STANDARD)
- `main.py` — entrypoint, как у всех предыдущих коннекторов

## 5. Объём — см. `CONNECTOR_DISCOVERY.md` §7 (зафиксировано, не открытый вопрос)

Ярус 1+2+3 целиком, за прямым исключением Quotes/Workflows/CMS Hub/
Conversations (архитектурно другой домен или нестабильный контракт —
не экономия объёма).
