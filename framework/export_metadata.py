"""Export the database metadata the contract generator needs.

Reads, from SQL Server's own metadata:
  1. every view's SQL text        (sys.sql_modules)
  2. every table's columns+types  (INFORMATION_SCHEMA.COLUMNS)
and saves both as JSON in MeshFlow/metadata/, so each run is documented
and the generator can be tested on exactly this snapshot.
"""
import json
from datetime import datetime
from pathlib import Path

from db import connect, SERVER, DATABASE

OUT = Path(__file__).resolve().parent.parent / "metadata"

VIEWS_SQL = """
SELECT s.name, v.name, m.definition
FROM sys.views AS v
JOIN sys.schemas AS s ON s.schema_id = v.schema_id
JOIN sys.sql_modules AS m ON m.object_id = v.object_id
ORDER BY s.name, v.name;
"""

COLUMNS_SQL = """
SELECT c.TABLE_SCHEMA, c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE,
       c.CHARACTER_MAXIMUM_LENGTH, c.NUMERIC_PRECISION, c.NUMERIC_SCALE,
       c.IS_NULLABLE, t.TABLE_TYPE
FROM INFORMATION_SCHEMA.COLUMNS AS c
JOIN INFORMATION_SCHEMA.TABLES  AS t
  ON t.TABLE_SCHEMA = c.TABLE_SCHEMA AND t.TABLE_NAME = c.TABLE_NAME
ORDER BY c.TABLE_SCHEMA, c.TABLE_NAME, c.ORDINAL_POSITION;
"""


def full_type(data_type, char_len, precision, scale):
    """Turn SQL Server's type parts into one readable type, e.g. nvarchar(50)."""
    if char_len is not None:
        return f"{data_type}({'max' if char_len == -1 else char_len})"
    if data_type in ("decimal", "numeric"):
        return f"{data_type}({precision},{scale})"
    return data_type


def main():
    OUT.mkdir(exist_ok=True)
    with connect() as conn:
        cur = conn.cursor()
        views = [{"schema": s, "name": n, "definition": d}
                 for s, n, d in cur.execute(VIEWS_SQL).fetchall()]
        columns = {}
        for sch, tab, col, dt, ln, pr, sc, nul, ttype in cur.execute(COLUMNS_SQL).fetchall():
            t = columns.setdefault(f"{sch}.{tab}", {"kind": "view" if ttype == "VIEW" else "table",
                                                     "columns": {}})
            t["columns"][col] = {"type": full_type(dt, ln, pr, sc), "nullable": nul == "YES"}

    snapshot = {"server": SERVER, "database": DATABASE,
                "exported_at": datetime.now().isoformat(timespec="seconds"),
                "views": views, "objects": columns}
    path = OUT / "metadata_snapshot.json"
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    tables = sum(1 for o in columns.values() if o["kind"] == "table")
    cols = sum(len(o["columns"]) for o in columns.values() if o["kind"] == "table")
    print(f"Exported {len(views)} views, {tables} tables and {cols} table columns")
    print(f"Saved to {path}")


if __name__ == "__main__":
    main()
