"""MeshFlow change checker (option A: read the producer's migration script).

Reads a producer's migration file, works out which schema changes it makes,
compares them with every consumer contract, and decides PASS or BLOCK.

Supported changes (6):  column rename / drop / type change / add,
                        table drop / rename.
Anything it cannot interpret is BLOCKED for manual review (fail-safe).

Usage:
  python check_change.py <migration.sql> [--strict] [--json]
Exit code: 0 = PASS, 1 = BLOCK   (used by the CI gate)
"""
import json
import re
import sys
from pathlib import Path

import sqlglot
import yaml
from sqlglot import exp

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "contracts"
SNAPSHOT = ROOT / "metadata" / "metadata_snapshot.json"

# ---------------------------------------------------------------- loading

def load_contracts():
    """Index contracts as {table: {column: [consumer, ...]}} (lower-case keys)."""
    index, names = {}, {}
    for path in sorted(CONTRACTS.glob("*.yaml")):
        c = yaml.safe_load(path.read_text(encoding="utf-8"))
        for dep in c["depends_on"]:
            t = dep["table"].lower()
            names[t] = dep["table"]
            cols = index.setdefault(t, {})
            for col in dep["columns"]:
                cols.setdefault(col["name"].lower(), set()).add(c["contract"])
    return index, names


def load_schema():
    """Current table columns and types from the metadata snapshot (lower-case keys)."""
    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    return {name.lower(): {c.lower(): (c, info["type"]) for c, info in obj["columns"].items()}
            for name, obj in snap["objects"].items() if obj["kind"] == "table"}

# ---------------------------------------------------------------- reading the script

def split_statements(text):
    """Split a script into statements: on GO lines, then with sqlglot on ';'."""
    text = re.sub(r"--[^\n]*", "", text)                     # remove -- comments
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)        # remove /* */ comments
    for batch in re.split(r"^\s*GO\s*$", text, flags=re.M | re.I):
        if batch.strip():
            yield batch


def norm_type(t):
    """Make type names comparable: 'NUMERIC(10, 2)' -> 'decimal(10,2)'."""
    t = t.lower().replace(" ", "")
    t = re.sub(r"^numeric", "decimal", t)
    t = re.sub(r"^integer$", "int", t)
    return t


def table_name(tbl):
    return f"{tbl.db}.{tbl.name}" if tbl.db else tbl.name


def parse_changes(text):
    """Turn a migration script into a list of change dicts."""
    changes = []
    for batch in split_statements(text):
        try:
            statements = sqlglot.parse(batch, read="tsql")
        except Exception as e:
            changes.append({"kind": "unrecognized", "sql": batch.strip()[:120],
                            "reason": f"could not parse: {str(e).splitlines()[0][:80]}"})
            continue
        for st in statements:
            if st is None:
                continue
            changes.extend(interpret(st))
    return changes


def interpret(st):
    sql = st.sql(dialect="tsql")[:120]
    if isinstance(st, exp.Use):
        return []                                            # USE database: not a change

    if isinstance(st, exp.Execute) and st.this.name.lower() in ("sp_rename", "sys.sp_rename"):
        args = [a.name for a in st.expressions]
        if len(args) >= 2:
            old, new = args[0].replace("[", "").replace("]", ""), args[1]
            kind = args[2].upper() if len(args) > 2 else "OBJECT"
            parts = old.split(".")
            if kind == "COLUMN" and len(parts) == 3:
                return [{"kind": "rename_column", "table": f"{parts[0]}.{parts[1]}",
                         "column": parts[2], "new_name": new, "sql": sql}]
            if kind == "OBJECT" and len(parts) == 2:
                return [{"kind": "rename_table", "table": old, "new_name": new, "sql": sql}]

    if isinstance(st, exp.Drop) and str(st.args.get("kind", "")).upper() == "TABLE":
        return [{"kind": "drop_table", "table": table_name(t), "sql": sql}
                for t in st.args.get("tables") or [st.this]]

    if isinstance(st, exp.Alter) and str(st.args.get("kind", "")).upper() == "TABLE":
        table, out = table_name(st.this), []
        for action in st.args.get("actions") or []:
            if isinstance(action, exp.Drop) and str(action.args.get("kind", "")).upper() == "COLUMN":
                for col in action.args.get("tables") or []:
                    out.append({"kind": "drop_column", "table": table, "column": col.name, "sql": sql})
            elif isinstance(action, exp.AlterColumn) and action.args.get("dtype") is not None:
                out.append({"kind": "type_change", "table": table, "column": action.this.name,
                            "new_type": norm_type(action.args["dtype"].sql(dialect="tsql")), "sql": sql})
            elif isinstance(action, exp.ColumnDef):
                out.append({"kind": "add_column", "table": table, "column": action.this.name, "sql": sql})
            else:
                out.append({"kind": "unrecognized", "table": table, "sql": sql,
                            "reason": f"unsupported ALTER TABLE action ({type(action).__name__})"})
        if out:
            return out

    return [{"kind": "unrecognized", "sql": sql, "reason": "not one of the 6 supported change types"}]

# ---------------------------------------------------------------- policy

INT_ORDER = ["tinyint", "smallint", "int", "bigint"]
STRINGS = {"char": "varchar", "varchar": "varchar", "nchar": "nvarchar", "nvarchar": "nvarchar"}


def split_type(t):
    m = re.match(r"([a-z0-9]+)(?:\((.*)\))?$", t)
    return (m.group(1), m.group(2)) if m else (t, None)


def is_widening(old, new):
    """True if every value of the old type fits the new type without loss."""
    (ob, oa), (nb, na) = split_type(old), split_type(new)
    if ob in INT_ORDER and nb in INT_ORDER:
        return INT_ORDER.index(nb) > INT_ORDER.index(ob)
    if ob in STRINGS and nb in STRINGS and STRINGS[ob] in ("varchar", nb) and nb in ("varchar", "nvarchar"):
        if STRINGS[ob] == "nvarchar" and nb == "varchar":
            return False                                     # unicode -> non-unicode can lose characters
        if na == "max":
            return True
        if oa == "max":
            return False
        return oa is not None and na is not None and int(na) >= int(oa)
    if ob == nb == "decimal" and oa and na:
        (op, os_), (np_, ns) = [tuple(int(x) for x in a.split(",")) for a in (oa, na)]
        return ns >= os_ and (np_ - ns) >= (op - os_)
    if ob == "smallmoney" and nb == "money":
        return True
    return False


def evaluate(change, contracts, names, schema, strict):
    """Return (decision, reason, affected consumers) for one change."""
    kind, table = change["kind"], change.get("table", "")
    t = table.lower()
    if kind == "unrecognized":
        return "BLOCK", f"unrecognized change, needs manual review ({change['reason']})", []
    if t not in schema:
        return "BLOCK", f"table {table} not found in the current schema, needs manual review", []

    table_consumers = sorted(set().union(*contracts.get(t, {}).values())) if contracts.get(t) else []

    if kind in ("drop_table", "rename_table"):
        if table_consumers:
            return "BLOCK", f"{len(table_consumers)} consumer(s) read this table", table_consumers
        return "PASS", "no consumer reads this table", []

    col = change["column"].lower()
    if kind == "add_column":
        if col in schema[t]:
            return "BLOCK", f"column {change['column']} already exists, needs manual review", []
        return "PASS", "adding a column does not affect existing consumers", []

    if col not in schema[t]:
        return "BLOCK", f"column {change['column']} not found in {table}, needs manual review", []
    consumers = sorted(contracts.get(t, {}).get(col, []))
    if not consumers:
        return "PASS", "no consumer uses this column", []

    if kind in ("drop_column", "rename_column"):
        return "BLOCK", f"{len(consumers)} consumer(s) use this column", consumers

    if kind == "type_change":
        old = norm_type(schema[t][col][1])
        new = change["new_type"]
        if old == new:
            return "PASS", "type is unchanged", []
        if is_widening(old, new):
            if strict:
                return "BLOCK", f"widening {old} -> {new} (blocked in strict mode)", consumers
            return "PASS", f"widening {old} -> {new} is safe for consumers", []
        return "BLOCK", f"type change {old} -> {new} can break consumers", consumers

    return "BLOCK", "needs manual review", []

# ---------------------------------------------------------------- main

def describe(c):
    k = c["kind"]
    if k == "rename_column": return f"Rename column {c['table']}.{c['column']} -> {c['new_name']}"
    if k == "drop_column":   return f"Drop column {c['table']}.{c['column']}"
    if k == "type_change":   return f"Change type of {c['table']}.{c['column']} -> {c['new_type']}"
    if k == "add_column":    return f"Add column {c['table']}.{c['column']}"
    if k == "drop_table":    return f"Drop table {c['table']}"
    if k == "rename_table":  return f"Rename table {c['table']} -> {c['new_name']}"
    return f"Unrecognized statement: {c['sql']}"


def check(script_text, strict=False):
    contracts, names = load_contracts()
    schema = load_schema()
    results = []
    for change in parse_changes(script_text):
        decision, reason, consumers = evaluate(change, contracts, names, schema, strict)
        results.append({**change, "decision": decision, "reason": reason, "consumers": consumers})
    overall = "BLOCK" if any(r["decision"] == "BLOCK" for r in results) else "PASS"
    if not results:
        overall, results = "BLOCK", [{"kind": "unrecognized", "sql": "", "decision": "BLOCK",
                                      "reason": "no schema change found in the script", "consumers": []}]
    return overall, results


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    path = Path(args[0])
    overall, results = check(path.read_text(encoding="utf-8-sig"), strict="--strict" in sys.argv)

    if "--json" in sys.argv:
        print(json.dumps({"file": str(path), "result": overall, "changes": results}, indent=2, default=list))
    else:
        print(f"\nMeshFlow change check: {path.name}" + ("  [strict mode]" if "--strict" in sys.argv else ""))
        print("=" * 70)
        for r in results:
            print(f"\n[{r['decision']}] {describe(r)}")
            print(f"        {r['reason']}")
            for consumer in r["consumers"]:
                print(f"          - {consumer}")
        print("\n" + "=" * 70)
        print(f"RESULT: {overall}" + ("  (change can be released)" if overall == "PASS"
                                       else "  (fix the change or agree it with the listed consumers)"))
    sys.exit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()
