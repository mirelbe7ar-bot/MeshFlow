# Mutation testing results

- Mutations generated: 1846
- Refused by SQL Server (never reach a consumer): 1265
- Applied and measured: 581
- Truly breaking: 117

## Confusion matrix (default mode)

| | Truly breaking | Truly safe |
|---|---|---|
| Predicted breaking (BLOCK) | TP = 117 | FP = 8 |
| Predicted safe (PASS) | FN = 0 | TN = 456 |

## Main measures

| Measure | Default mode | Strict mode | Target |
|---|---|---|---|
| Recall | 100.0% | 100.0% | at least 95% |
| Precision | 93.6% | 88.0% | at least 90% |
| F1 | 96.7% | 93.6% | – |
| Consumer accuracy (TP with exactly the right consumers) | 100.0% | | – |
| Average check time | 50.1 ms | | a few seconds |

Changes that broke only views without contracts (XML views, known limitation): 11

## By change type (default mode)

| Change type | Applied | Refused | TP | FP | FN | TN | Recall | Precision |
|---|---|---|---|---|---|---|---|---|
| add_column | 68 | 0 | 0 | 0 | 0 | 68 | – | – |
| drop_column | 50 | 415 | 10 | 0 | 0 | 40 | 100.0% | 100.0% |
| drop_table | 29 | 39 | 9 | 0 | 0 | 20 | 100.0% | 100.0% |
| rename_column | 299 | 166 | 72 | 0 | 0 | 227 | 100.0% | 100.0% |
| rename_table | 62 | 6 | 26 | 0 | 0 | 36 | 100.0% | 100.0% |
| type_change | 37 | 410 | 0 | 8 | 0 | 29 | – | 0.0% |
| type_widening | 36 | 229 | 0 | 0 | 0 | 36 | – | – |

## By producer domain (default mode)

| Domain | Applied | TP | FP | FN | TN | Recall | Precision |
|---|---|---|---|---|---|---|---|
| HumanResources | 48 | 17 | 2 | 0 | 29 | 100.0% | 89.5% |
| Person | 93 | 46 | 3 | 0 | 44 | 100.0% | 93.9% |
| Production | 203 | 16 | 1 | 0 | 186 | 100.0% | 94.1% |
| Purchasing | 51 | 17 | 1 | 0 | 33 | 100.0% | 94.4% |
| Sales | 186 | 21 | 1 | 0 | 164 | 100.0% | 95.5% |
