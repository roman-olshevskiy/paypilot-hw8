# Інструменти ДЗ8

- calibrate_run.py — upstream6439a32 з адаптаціями; recorded answers,5 verdicts, majority, Wilson, групи й матриця; --validate-only не викликає модель. --draft дозволено лише з validate-only. --diagnostic приймає незмінні pre-labeled source pairs і все одно потребує глобального human freeze перед inference.
- judge.py у корені — guarded transport і durable raw capture; автоматичних inference retries немає.
- promote_labels.py — приймає явні людські рішення для всіх30 IDs, не викликає модель і не комітить. Не перезаписує labels.
- freeze_labels.py — після локального коміту перевіряє bytes labels/rubric/forecast і зберігає SHA/commit.
- hw8_guard.py — HW8_PAID плюс перевірка людського freeze; одного прапорця недостатньо.
- compare_judges.py — вихідний скрипт для опції двох моделей; сам викликів не робить.

Усі .env/ключі локальні. JSON raw і reports не редагуються для бажаних вердиктів. Нові версії рубрики — новий файл і нове калібрування; --rubric приймає лише закомічений override з іншою версією.

## Фінальна кампанія

- capture_series.py + tests/test_series.py — нативний CLI з повним durable capture кожної відповіді/трейсу/стану; окремі trace каталоги профілів, без перезаписування.
- calibrate_run.py --resume — лише явне продовження ERROR з тих самих bytes/model/temperature/version; готові calls повторно не оплачуються. Перші5 валідних outputs, протокольні ERROR окремо в cost і end-to-end consistency.
- diagnose_pairs.py — перші5 сирих emissions на кожен pre-labeled reference case. Невалідні quotes/multiple JSON не стають валідними verdicts; це окремий діагностичний звіт, не30-case calibration.
- hw8_budget.py — stop checks перед paid calls за durable usage. Ліміти решти Anthropic1.00/OpenRouter0.50; резерв під наступний запит, зупинка за невідомої ціни. Це не провайдерський hard ceiling.
- replay_saved.py — чистий clone, нативний CLI на fixtures,0 HTTP/LLM. Звіти первинних live прогонів не замінюються replay.
- final_analysis.py / reconcile_billing.py — лише offline перерахунок похідних JSON, не source captures і не labels.

Системну змінну TEMP не використовувати як параметр судді: HW8_JUDGE_TEMPERATURE=0.7. Поточна модель судді Haiku4.5 підтримує параметр; для зміни моделі потрібне нове калібрування. Merge із збереженням історії, без squash, інакше freeze object може зникнути з clean clone.
