# Pricing History — HubSpot Connector

## 2026-08-22 — повторное подтверждение цены (suspend → update_pricing → deploy → submit_for_review)

Тот же паттерн: `suspend_app` (было live) → первый `update_pricing`
вернул `'connect_hubspot'/'disconnect_hubspot'/'list_connections'
unexpectedly still priced` (расхождение только по free_tools) →
немедленный повтор с тем же payload прошёл без ошибки, цена подтверждена.
Задокументировано как задача #2275 (Imperal Cloud tracker). `deploy_app`
(21/22, commit dd198171) → `submit_for_review` → `pending_review`.

Обязательный журнал: каждое выставление или изменение цен на функции этого
приложения фиксируется здесь — что изменилось, почему, и на основании
чего. Не переписывать прошлые записи — только дописывать новые сверху.

---

## 2026-08-21 — первичное выставление цен, ДО submit_for_review (канонический порядок соблюдён)

**Порядок выполнен по канону, без нарушения:** код готов → пост-аудит
чистый (все 79 функций прошли `imperal_sdk.validator` с нулём
замечаний ERROR/WARN) → `deploy_app` → `update_pricing` (этот шаг) →
`submit_for_review` (ещё не вызван, следующий шаг). В отличие от
инцидента MuleSoft Connector (2026-08-20, см. его собственный
`PRICING_HISTORY.md`), здесь прайсинг выставлен ДО подачи на ревью —
урок применён.

**Метод применения — `developer.update_pricing` с явным
`revenue_split_dev=95`, подтверждённо рабочий способ (см. канонический
`PRICING_POLICY.md` §3).** `pricing_config` передан как настоящий JSON-
объект, не строка. `save_pricing` не использовался.

**Цены — фиксированная платформенная шкала {0, 8, 16, 20, 40, 60}, без
исключений. Тиры смоделированы по прецедентам Asana Connector (0/8/16)
и MuleSoft Connector (40/60 для value-add отчётов и bulk-операций):**

| Цена | Функции | Обоснование |
|---|---|---|
| 0 | `connect_hubspot`, `disconnect_hubspot`, `list_connections` (3) | Настройка доступа, не операция с данными портала HubSpot |
| 8 | 37 функций: все `list_*`/`get_*`, `search_objects`, `batch_read_objects`, `sync_check` | Простое чтение — не изменяет ничего в портале клиента |
| 16 | 33 функции: `create_*`/`update_*`/`archive_*` по всем 6 стандартным типам + generic `create_object`/`update_object`/`archive_object`, `associate_objects`, `remove_association`, `create_property`, `create_engagement`/`update_engagement`, `add_contacts_to_list`/`remove_contacts_from_list`, `upload_file`, `create_custom_object_schema`, `create_webhook_subscription`/`delete_webhook_subscription`/`set_webhook_target_url` | Стандартное одиночное write/CRUD-действие на одной записи или одной связи |
| 40 | `get_pipeline_health`, `find_duplicate_contacts` | Агрегированные value-add отчёты, сканирующие весь портал/пайплайн, а не одну запись — тот же тир, что `audit_cloudhub_environment`/`get_stale_applications` у MuleSoft |
| 60 | `batch_create_objects`, `batch_update_objects`, `batch_archive_objects`, `bulk_update_deal_stage` | Bulk-операции сразу над до 100 записями за один вызов — тот же тир, что `bulk_start_cloudhub_applications` и аналоги у MuleSoft |

Google Cloud/Workspace маркап ×1.8 (`PRICING_POLICY.md` §5) НЕ применяется
— HubSpot не Google-backed API.

`pricing_model = "per_action"`, `monthly_price = 0`,
`revenue_split_dev = 95` (partner-тир, тот же уровень, что у
Asana/MuleSoft/Workato Connector в этот период).

**Покрытие проверено программно перед применением:** множество функций
из `tool-prices.json["tool_prices"]` и множество реальных
`@chat.function(name=...)` по всем `handlers*.py` совпадают ровно (79 =
79, разница в обе стороны — пустое множество).

**Источник истины продублирован в `imperal.json["pricing"]`** этого
приложения (не только в runtime-вызове) — так цена видна прямо в
манифесте независимо от состояния платформенного API, по тому же
правилу, что и у Asana/MuleSoft/Make.com/n8n Connector.
