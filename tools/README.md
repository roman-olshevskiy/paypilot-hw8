# Інструменти ДЗ 8

- calibrate_run.py — upstream6439a32 з адаптаціями; recorded answers,5 verdicts, majority, Wilson, групи й матриця; --validate-only не викликає модель. --draft дозволено лише з validate-only. --diagnostic приймає незмінні pre-labeled source pairs і все одно потребує глобального human freeze перед inference.
- judge.py у корені — guarded transport і durable raw capture; автоматичних inference retries немає.
- promote_labels.py — приймає явні людські рішення для всіх 30 IDs, не викликає модель і не комітить. Не перезаписує labels.
- freeze_labels.py — після локального коміту перевіряє bytes labels/rubric/forecast і зберігає SHA/commit.
- hw8_guard.py — HW8_PAID плюс перевірка людського freeze; одного прапорця недостатньо.
- compare_judges.py — вихідний скрипт для опції двох моделей; сам викликів не робить.

Усі .env/ключі локальні. JSON raw і reports не редагуються для бажаних вердиктів. Нові версії рубрики — новий файл і нове калібрування; --rubric приймає лише закомічений override з іншою версією.

## Фінальна кампанія

- capture_series.py + tests/test_series.py — нативний CLI з повним durable capture кожної відповіді/трейсу/стану; окремі trace каталоги профілів, без перезаписування.
- calibrate_run.py --resume — лише явне продовження ERROR з тих самих bytes/model/temperature/version; готові calls повторно не оплачуються. Перші 5 валідних outputs, протокольні ERROR окремо в cost і end-to-end consistency.
- diagnose_pairs.py — перші 5 сирих emissions на кожен pre-labeled reference case. Невалідні quotes/multiple JSON не стають валідними verdicts; це окремий діагностичний звіт, не 30-case calibration.
- hw8_budget.py — stop checks перед paid calls за durable usage. Ліміти решти Anthropic1.00/OpenRouter0.50; резерв під наступний запит, зупинка за невідомої ціни. Це не провайдерський hard ceiling.
- replay_saved.py — чистий clone, нативний CLI на fixtures,0 HTTP/LLM. Звіти первинних live прогонів не замінюються replay.
- final_analysis.py / reconcile_billing.py — лише offline перерахунок похідних JSON, не source captures і не labels.

Системну змінну TEMP не використовувати як параметр судді: HW8_JUDGE_TEMPERATURE=0.7. Поточна модель судді Haiku4.5 підтримує параметр; для зміни моделі потрібне нове калібрування. Початкова історія збережена віддаленим тегом `hw8-calibration-history`; він потрібен перевірці freeze після squash першого PR.

## Протокол і відновлення

Калібрування: перші 5 валідних verdicts на кейс; 1/2 відхилені протокольні виходи v1/v2 збережено, включено у витрати й end-to-end сталість. Діагностика D18/D25 — окремі 20 сирих emissions,7 із повним валідним протоколом; не змішується з 30 кейсами.

ERROR не перетворюється на PASS; звіти не перезаписуються. Calibration exit1 означає розбіжності, exit2 — помилку протоколу або інфраструктури; native exit1 — не всі кейси пройшли. Початкові зупинені звіти збережено. Продовження використовує вже готові результати й не обирає вердикт із суперечливих JSON.

## Платні команди відтворення

Не запускаються автоматично тестами. Ключ Anthropic — лише локально в .env за .env.example; ключ агента лишається в .env стенду. Judge=claude-haiku-4-5-20251001, HW8_JUDGE_TEMPERATURE=0.7; системний TEMP не використовується. Агент=OpenRouter Haiku5.5, без L07 proxy. Контекст customer_id/clock уже в кейсах.

~~~powershell
docker compose run --rm -e HW8_PAID=1 --entrypoint python eval tools/calibrate_run.py l09_labels
docker compose run --rm -e HW8_PAID=1 --entrypoint python eval tools/calibrate_run.py l09_labels --rubric rubrics/rubric.v2.md
docker compose run --rm -e HW8_PAID=1 eval --set l09_escalation --gate all --profile lesson-09 --traces
docker compose run --rm -e HW8_PAID=1 eval --set l09_escalation --gate all --profile clean --traces
~~~

Daily: ESC-001, runs=1; release: ESC-002 і ESC-J01–05, runs=5. Native runner судить лише останню із 5 свіжих відповідей judge-кейса, а calibrate_run — записану answer_under_test п’ять разів. Дані цих двох режимів не взаємозамінні.

