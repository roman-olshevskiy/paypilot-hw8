# Інструменти ДЗ8

## Чинний підрахунок · 30.10.2026

- `recount_raw.py` — офлайн-перерахунок перших 5 сирих спроб на кейс у межах первинної калібрувальної серії, без пілота. Невалідна цитата/JSON — MISS без заміни. Джерела й SHA256 кожної спроби — у `reports/calibration-raw-recount.json`.
- `calibrate_run.py` — recorded answers, рівно 5 спроб, більшість ≥3 валідних голосів, Wilson по кейсах, групи та матриця. MISS займає слот і ніколи не збігається з PASS/FAIL. `--validate-only` безкоштовний; `--draft` дозволено лише з ним. `--resume` вимкнено: він не може замінити невалідний вихід.
- `judge.py` — стандартні `judge(...)` і `verdict(...)`, Anthropic/Ollama, дослівна цитата й durable raw capture до парсингу, без автоматичних повторів.
- `promote_labels.py` / `freeze_labels.py` — явне людське підтвердження, commit/bytes/SHA перевірка. Історія збережена тегом `hw8-calibration-history` після squash першого PR.
- `capture_series.py` + `tests/test_series.py` — нативний CLI з capture кожної відповіді/трейсу/стану, окремими каталогами профілів.
- `diagnose_pairs.py` — перші 5 сирих виходів supplied-кейсів; їхня чинна оцінка з MISS також у перерахунку.
- `final_analysis.py` / `reconcile_billing.py` — офлайн-похідні метрики й звірка раніше збереженого білінгу, не модельні виклики.
- `replay_saved.py` — native CLI на записаних fixtures, 0 HTTP/LLM. `verify_docker_clone.py --remote` — офлайн-тести зі свіжого GitHub-клону; потрібна запушена гілка.
- `compare_judges.py` — upstream-інструмент порівняння двох моделей; сам викликів не робить.

## Протокол і відновлення

Первинна кампанія помилково відбирала 5 валідних виходів і продовжувала ERROR. Її reports та raw captures залишено незмінними як докази, а метрики замінено офлайн-перерахунком. Для v1/v2 додаткові 1/2 пізніші виходи не входять у нові 150 спроб, але залишаються у витратах.

Тепер протокольний ValueError — виміряний MISS, не причина додаткового виклику. Інфраструктурна помилка зупиняє серію, exit2. Exit1 означає розбіжність або протокольний MISS; native exit1 — не всі кейси пройшли. Звіти не перезаписуються. Кожен release-вердикт ескалації PASS/FAIL/ERROR перевіряє людина незалежно від 5/5.

## Платні команди відтворення

Нових платних прогонів для цього доопрацювання не потрібно. Команди нижче — для свідомого майбутнього відтворення. Ключ Anthropic зберігається лише в локальному `.env`; ключ агента — у стенді. Judge: `claude-haiku-4-5-20251001`, `HW8_JUDGE_TEMPERATURE=0.7`; системний `TEMP` не використовується.

~~~powershell
docker compose run --rm -e HW8_PAID=1 --entrypoint python eval tools/calibrate_run.py l09_labels
docker compose run --rm -e HW8_PAID=1 --entrypoint python eval tools/calibrate_run.py l09_labels --rubric rubrics/rubric.v2.md
docker compose run --rm -e HW8_PAID=1 eval --set l09_escalation --gate all --profile lesson-09 --traces
docker compose run --rm -e HW8_PAID=1 eval --set l09_escalation --gate all --profile clean --traces
~~~

HW8 CLI вимагає `HW8_PAID=1`, human freeze та бюджет. `hw8_budget.py` перевіряє ліміти кампанії до запиту за durable usage; це не провайдерський hard ceiling. Daily ESC-001: runs=1; release ESC-002 і ESC-J01–05: runs=5. Native runner оцінює останню із 5 свіжих відповідей; калібрування — одну записану відповідь у 5 спробах.

## Сумісність L10

Стандартний API `judge(...)` / `verdict(...)` працює **без HW8_PAID**: приватний freeze ДЗ8 не є частиною контракту L10. Якщо задано `HW8_CAMPAIGN_GUARD=1` або `HW8_PAID`, діє захист кампанії ДЗ8. Сумісність Ollama перевірена mocked transport без ключів, freeze і реальних inference. Реального L10-калібрування ще не було.
