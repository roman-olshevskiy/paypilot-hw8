# Прогони й докази ДЗ8

Усі серії окремі; labels і відповіді не змінювалися після судді.

## Калібрування

- [v1, завершена когорта30](../reports/calibration-l09_labels-20261029T142704481494Z-02244a87.json); джерельний ERROR — [окремо](../reports/calibration-l09_labels-20261029T142020036786Z-51c9c04e.json).

- [v2, завершена когорта30](../reports/calibration-l09_labels-20261029T143819958028Z-f23d6ab6.json); попередні ERROR — [report](../reports/calibration-l09_labels-20261029T143029033067Z-ed659b53.json), [report](../reports/calibration-l09_labels-20261029T143558519430Z-af33160a.json).

- [Діагностичні4 пари ×5 сирих виходів](../reports/diagnostic-pairs-20261029T143539150040Z.json); незавершені початкові calibrate reports не є фінальною30-кейсовою когортою.

- [Метод, протокол і таблиці](calibration-report.md).

## Native L09

| Серія | Профіль | Chat | Native reports/captures |
|---|---|---|---|
| frequency | clean | 20 | [native](../evidence/runs/20261029T142020485983Z-frequency-clean-d181f1/native-results.json), [full captures](../evidence/runs/20261029T142020485983Z-frequency-clean-d181f1/agent-captures.json) |
| frequency | lesson-09 | 20 | [native](../evidence/runs/20261029T142314034191Z-frequency-lesson-09-7c0674/native-results.json), [full captures](../evidence/runs/20261029T142314034191Z-frequency-lesson-09-7c0674/agent-captures.json) |
| working | clean | 31 | [native](../evidence/runs/20261029T143913419317Z-working-clean-ec2efb/native-results.json), [full captures](../evidence/runs/20261029T143913419317Z-working-clean-ec2efb/agent-captures.json) |
| working | lesson-09 | 31 | [native](../evidence/runs/20261029T144243715820Z-working-lesson-09-1bbca9/native-results.json), [full captures](../evidence/runs/20261029T144243715820Z-working-lesson-09-1bbca9/agent-captures.json) |

## Пілот

- [Пілот і дві виправлені передумови](pilot-review.md);8 chats +3 judge calls, включені у загальну вартість.

- Частоти основної серії:40 chats. Working гейт:62 chats +10 judge calls. Разом110 chats і336 judge provider calls (303 основного калібрування,20 діагностичних,10 working,3 pilot).

- [Білінг](../evidence/final-billing-reconciliation.json); [сирі judge-відповіді](../evidence/judge-calls).

## Межа clean

ESC-J03 на clean FAIL через T3. Дослівна цитата судді:

> The eligibility check found a customer-level restriction on your account

Цитата перевірена як substring фактичної відповіді, а не твердження про прихований стан. Набір збережено червоним; еталон/рубрику не послаблено. На lesson-09 ця сама перевірка теж FAIL. Факт виконання ескалації й обіцянки у тексті — різні перевірки.
