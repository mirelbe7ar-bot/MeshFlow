# migrations/

Producers put their proposed schema changes here, one `.sql` file per change
(for example `2026-10-27_rename_listprice.sql`).

When a pull request adds or edits a file in this folder, the MeshFlow CI gate
runs `framework/check_change.py` on it and blocks the pull request if the
change would break a consumer contract.

Example scripts for the 12 demonstration scenarios live in `scenarios/`.
