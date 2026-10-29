# ДЗ №8 · Judge Trust Statement

**Людську розмітку підтверджено; пілот у роботі.** Першу спробу зупинено до inference через конфлікт системного TEMP; усунення й повтор записані окремо. Основа — повна копія L09 6439a32; стенд shared74f1995.

- [Вимога й робочий набір](docs/requirement-split.md), [7 кейсів](sets/l09_escalation.jsonl): поріг daily/1, контроль release/5, п’ять judge release/5.
- [Рубрика v1](rubrics/rubric.v1.md), [changelog](rubrics/CHANGELOG.md).
- [30 чернеткових міток](evals/sets/l09_labels.draft.jsonl):10 очевидних PASS,10 очевидних FAIL,10 спірних. Це власні синтетичні відповіді, не captures стенду; людські label підтверджено 2026-10-29.
- [Прогноз](docs/forecast-before-runs.md), [метод і відхилення кіта](docs/preparation.md).
- [Початковий README L09](sources/L09-README.md), [provenance](evidence/provenance.json), [готовність](evidence/environment/readiness.json).

## Без оплати

~~~powershell
docker compose run --rm eval python -m unittest discover -s tests -v
docker compose run --rm --entrypoint python eval tools/calibrate_run.py evals/sets/l09_labels.draft.jsonl --validate-only --draft
docker compose run --rm eval --set l09_escalation --dry-run
~~~

Для іншого розташування стенду задати STAND_DIR. Значення ключів лише в локальному .env; .env.example не містить секретів. Службові read-only тести health/catalog запускаються окремо з HW8_ENV=1. Суддя: claude-haiku-4-5-20251001, HW8_JUDGE_TEMPERATURE=0.7; кандидат змінений до оплати через API-обмеження Haiku5.5.

## Після людського review — без генерацій

1. Явно підтвердити або виправити всі30 запропонованих міток; фінальні рішення записати в локальний review JSON (`human_review_confirmed: true`, `labels: {ID: PASS/FAIL}`, за потреби `reasons`).
2. Виконати `python tools/promote_labels.py <review.json>`: створюється канонічний evals/sets/l09_labels.jsonl. Інструмент відмовляється перезаписати наявні фінальні labels.
3. Після локального review закомітити labels, rubric і прогноз ДО першого судді; `python tools/freeze_labels.py` перевіряє їхні байти у коміті та записує freeze. Автокоміту немає.

**Крок7 — пілот.** Навіть HW8_PAID=1 без підтверджених закомічених labels не дозволяє /chat чи judge inference.

## Майбутні платні команди — зараз не виконувати

Після freeze і окремого переходу до пілота:

~~~powershell
docker compose run --rm -e HW8_PAID=1 --entrypoint python eval tools/calibrate_run.py l09_labels
docker compose run --rm -e HW8_PAID=1 eval --set l09_escalation --gate release --profile clean --traces
~~~

Калібрування судить записану answer_under_test п’ять разів. Native working runner генерує5 агентських відповідей на judge-кейс і судить лише останню; це не вимірювання самоузгодженості судді. Звіти калібрування повертають exit1 за розбіжностей і exit2 за помилок, зберігаючи часткові дані. SKIP не є PASS.
