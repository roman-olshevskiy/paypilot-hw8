# US-05 §4: дія і формулювання

US-05 із лекції про vulnerable customer/material impact не містить числового порога. Конкретні умови бере Tool rules base.v1 (stand74f1995): settled fraud понад EUR10000, прохання про людину, дія поза tools, customer-level restriction. Не підміняємо всю вимогу порогом.

| Частина | Перевірка | Рівень | Gate/runs | Кейси |
|---|---|---|---|---|
| Наявність обов’язкової ескалації T-14 | tool_sequence/must_include | 3 | daily/1 | ESC-001 |
| Контроль нижче порога | tool_sequence/must_exclude | 3 | release/5 | ESC-002 |
| Формулювання передачі людині | judge, human oracle | 7 | release/5 | ESC-J01–ESC-J05 |

Daily/1 для ESC-001 — свідомий виняток лекції: перевірка спана детермінована, але його наявність породжує модель. Частоти clean/lesson-09 знімаються окремою лабораторною серією, не підміняються одним PASS.

ESC-J03 спирається на seed: CUS-0006 має compliance_hold=1, TX-0601 — EUR310, service_not_rendered. Рубрика не перевіряє, чи дію виконано: це окремий tool/trace факт. Вимога vulnerable customer не покрита — немає даних/дефекту. Усі calibration fixtures авторські синтетичні, а working inputs використовують seed; живих відповідей на цьому етапі немає.
