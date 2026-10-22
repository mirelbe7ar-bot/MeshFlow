# MeshFlow

Prototype for the bachelor thesis *Automatically Derived Consumer-Driven Data Contracts*
(German International University, Business Informatics).

Consumer data products (SQL views) are turned into data contracts automatically,
and every producer schema change is checked against those contracts before release.

| Folder | Content |
| --- | --- |
| `consumer_views/` | SQL of the 8 consumer views written for the thesis |
| `framework/` | Generator, checker and database helpers (Python) |
| `metadata/` | Snapshot of the database metadata used to build the contracts |
| `contracts/` | One generated YAML contract per consumer view |
| `migrations/` | Producers' proposed schema changes (checked by the CI gate) |
| `scenarios/` | Example changes for the demonstration scenarios |
| `.github/workflows/` | The CI gate (GitHub Actions) |

Dataset: AdventureWorks 2022 (Microsoft sample database) on SQL Server 2025.
