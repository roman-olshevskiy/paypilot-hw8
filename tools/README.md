# Інструменти ДЗ8

- calibrate_run.py — upstream6439a32 з адаптаціями; recorded answers,5 verdicts, majority, Wilson, групи й матриця; --validate-only не викликає модель. --draft дозволено лише з validate-only. --diagnostic приймає незмінні pre-labeled source pairs і все одно потребує глобального human freeze перед inference.
- judge.py у корені — guarded transport і durable raw capture; автоматичних inference retries немає.
- promote_labels.py — приймає явні людські рішення для всіх30 IDs, не викликає модель і не комітить. Не перезаписує labels.
- freeze_labels.py — після локального коміту перевіряє bytes labels/rubric/forecast і зберігає SHA/commit.
- hw8_guard.py — HW8_PAID плюс перевірка людського freeze; одного прапорця недостатньо.
- compare_judges.py — вихідний скрипт для опції двох моделей; сам викликів не робить.

Усі .env/ключі локальні. JSON raw і reports не редагуються для бажаних вердиктів. Нові версії рубрики — новий файл і нове калібрування; --rubric приймає лише закомічений override з іншою версією.
