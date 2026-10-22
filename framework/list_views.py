"""Step 1 test: connect to SQL Server and list every view with its SQL length."""
from db import connect, pick_driver

QUERY = """
SELECT s.name AS view_schema, v.name AS view_name, LEN(m.definition) AS sql_length
FROM sys.views AS v
JOIN sys.schemas AS s ON s.schema_id = v.schema_id
JOIN sys.sql_modules AS m ON m.object_id = v.object_id
ORDER BY s.name, v.name;
"""

print("Driver:", pick_driver())
with connect() as conn:
    rows = conn.cursor().execute(QUERY).fetchall()

print(f"Connected. Found {len(rows)} views:\n")
for schema, name, length in rows:
    print(f"  {schema + '.' + name:50} {length:6} characters of SQL")
