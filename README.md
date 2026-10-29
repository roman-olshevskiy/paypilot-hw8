# ДЗ №8 · Judge Trust Statement

**Готово до здачі. У LMS ще не надіслано.** Основна заява коротка; деталі — у додатках. Повна копія L09 6439a32, стенд shared74f1995; [provenance](evidence/provenance.json), [початковий README](sources/L09-README.md).

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

T-14: ескалація clean 10/10, lesson-09 0/10; контроль 0/10 в обох. Native working gate: **clean 6/7, lesson-09 3/7**, без SKIP. ESC-J03 на clean виявив розкриття внутрішньої причини; еталон збережено.

## Запуск без оплати

Потрібен Docker; контейнер містить Git для перевірки freeze. STAND_DIR типово ../paypilot-stand-shared.

~~~powershell
docker compose build eval
docker compose run --rm eval python -m unittest discover -s tests -v
docker compose run --rm --entrypoint python eval tools/calibrate_run.py l09_labels --validate-only
docker compose run --rm eval --set l09_escalation --dry-run
~~~

[Replay із чистого клону](evidence/clean-clone-replay.json) використовує записані fixtures, не нові модельні виклики. [Інструменти й обмеження](tools/README.md).

## Платне відтворення

[Налаштування та команди](tools/README.md#платні-команди-відтворення). Потрібен явний `HW8_PAID=1` і перевірений freeze. Native runner оцінює останню з п’яти свіжих відповідей; калібрування оцінює записану відповідь п’ять разів.

[Протокол ERROR і продовження](tools/README.md#протокол-і-відновлення).

Історію до прогонів збережено тегом `hw8-calibration-history`, оскільки перший PR злитий через squash. Звичайний `git clone` отримує тег; після shallow clone виконайте `git fetch origin tag hw8-calibration-history`. Не видаляйте цей тег: перевірка freeze використовує початкові Git-об’єкти.
