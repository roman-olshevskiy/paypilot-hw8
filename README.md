# ДЗ №8 · Judge Trust Statement

**Результати готові до локального review. У LMS ще не надіслано.** Основна заява коротка; деталі — у додатках. Повна копія L09 6439a32, стенд shared74f1995; [provenance](evidence/provenance.json), [початковий README](sources/L09-README.md).

- [Judge Trust Statement](judge-trust-statement.md) · [калібрування, матриці й невдале виправлення](docs/calibration-report.md).
- [30 людських міток](evals/sets/l09_labels.jsonl) · [freeze](evidence/labels-freeze.json) · [порядок комітів](evidence/chronology.json).
- [Рубрика v1](rubrics/rubric.v1.md) — обрана; [v2](rubrics/rubric.v2.md) — відхилена; [changelog](rubrics/CHANGELOG.md).
- [7 робочих кейсів](sets/l09_escalation.jsonl) · [розщеплення вимоги](docs/requirement-split.md) · [прогони](docs/run-index.md).
- [Витрати](evidence/final-billing-reconciliation.json) · [всі первинні виклики](evidence/judge-calls).

## Результат

| Показник | v1 | v2 |
|---|---|---|
| Agreement із людськими мітками | 25/30 | 24/30 |
| Пропуски / хибні тривоги | 2 /3 | 3 /3 |
| Сталість п’яти валідних verdicts | 30/30 | 30/30 |

Висока сталість не усуває систематичної помилки. v2 не прийнята. Факт ескалації перевіряє код; v1 використовується лише як допоміжний сигнал із людським review.

T-14: ескалація clean10/10, lesson-09 0/10; контроль0/10 в обох. Native working gate: **clean6/7, lesson-09 3/7**, без SKIP. Clean FAIL ESC-J03 — виявлене розкриття внутрішньої причини, не виправлений еталон заради зеленого статусу.

Калібрування: перші5 валідних verdicts на кейс; 1/2 відхилені протокольні виходи v1/v2 збережено, включено у витрати й end-to-end сталість. Діагностика D18/D25 — окремі20 сирих emissions,7 із повним валідним протоколом; не змішується з30 кейсами.

## Запуск без оплати

Потрібен Docker; контейнер містить Git для перевірки freeze. STAND_DIR типово ../paypilot-stand-shared.

~~~powershell
docker compose build eval
docker compose run --rm eval python -m unittest discover -s tests -v
docker compose run --rm --entrypoint python eval tools/calibrate_run.py l09_labels --validate-only
docker compose run --rm eval --set l09_escalation --dry-run
~~~

[Replay із чистого клону](evidence/clean-clone-replay.json) використовує записані fixtures, не нові модельні виклики. [Інструменти й обмеження](tools/README.md).

## Платні команди відтворення

Не запускаються автоматично тестами. Ключ Anthropic — лише локально в .env за .env.example; ключ агента лишається в .env стенду. Judge=claude-haiku-4-5-20251001, HW8_JUDGE_TEMPERATURE=0.7; системний TEMP не використовується. Агент=OpenRouter Haiku5.5, без L07 proxy. Контекст customer_id/clock уже в кейсах.

~~~powershell
docker compose run --rm -e HW8_PAID=1 --entrypoint python eval tools/calibrate_run.py l09_labels
docker compose run --rm -e HW8_PAID=1 --entrypoint python eval tools/calibrate_run.py l09_labels --rubric rubrics/rubric.v2.md
docker compose run --rm -e HW8_PAID=1 eval --set l09_escalation --gate all --profile lesson-09 --traces
docker compose run --rm -e HW8_PAID=1 eval --set l09_escalation --gate all --profile clean --traces
~~~

Daily: ESC-001, runs1; release: ESC-002 і ESC-J01–05, runs5. Native runner судить лише останню із5 свіжих відповідей judge-кейса, а calibrate_run — записану answer_under_test п’ять разів. Дані цих двох режимів не взаємозамінні.

ERROR не перетворюється на PASS; звіти не перезаписуються. Calibration exit1 — розбіжності, exit2 — протокол/інфраструктура; native exit1 — не всі кейси пройшли. Початкові зупинені reports збережено; продовження не повторювали готові результати й не обирали з двох суперечливих JSON.

**Git-історію людської розмітки треба зберегти:** PR зливати merge-комітом, без squash/rebase; freeze-коміт потрібен для перевірки та умови «мітки до судді».
