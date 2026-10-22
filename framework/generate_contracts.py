"""MeshFlow contract generator.

Turns every consumer view into a consumer-driven data contract (YAML):
  1. read the view's SQL and the producer tables' columns (metadata snapshot)
  2. parse the SQL with sqlglot and resolve every column to its source table
  3. write one YAML contract per view to MeshFlow/contracts/

Usage:
  python generate_contracts.py            # export fresh metadata from SQL Server, then generate
  python generate_contracts.py --offline  # use the existing metadata snapshot only
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import sqlglot
import yaml
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "metadata" / "metadata_snapshot.json"
CONTRACTS = ROOT / "contracts"

# SQL that the generator cannot analyze reliably (known limitation)
XML_PATTERN = re.compile(r"\.\s*(value|query|nodes|exist)\s*\(|WITH\s+XMLNAMESPACES", re.I)


def load_snapshot():
    return json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def build_schema(objects):
    """Shape the column metadata the way sqlglot expects: {schema: {table: {column: type}}}."""
    schema, lookup = {}, {}
    for full_name, obj in objects.items():
        sch, tab = full_name.split(".", 1)
        schema.setdefault(sch, {})[tab] = {c: "VARCHAR" for c in obj["columns"]}
        lookup[full_name.lower()] = (full_name, obj)
    return schema, lookup


def view_select(definition):
    """Return the SELECT part of a CREATE VIEW statement."""
    tree = sqlglot.parse_one(definition, read="tsql")
    return tree.expression if isinstance(tree, exp.Create) else tree


def uses_select_star(select):
    """True if any SELECT list contains * or table.* (COUNT(*) does not count)."""
    for sel in select.find_all(exp.Select):
        for e in sel.expressions:
            if isinstance(e, exp.Star) or (isinstance(e, exp.Column) and isinstance(e.this, exp.Star)):
                return True
    return False


def lookup_source(scope, alias):
    """Find which table or subquery an alias refers to, also in outer queries."""
    while scope is not None:
        if alias in scope.sources:
            return scope.sources[alias]
        scope = scope.parent
    return None


def extract_dependencies(select, schema, lookup):
    """Map each real source table to the set of its columns that the query uses."""
    qualified = qualify(select, schema=schema, dialect="tsql",
                        validate_qualify_columns=False, quote_identifiers=False)
    used = {}
    for scope in traverse_scope(qualified):
        for col in scope.columns:
            src = lookup_source(scope, col.table)
            if isinstance(src, exp.Table):
                key = f"{src.db}.{src.name}".lower()
                used.setdefault(key, set()).add(col.name.lower())
    deps = {}
    for key, cols in used.items():
        if key not in lookup:
            continue
        full_name, obj = lookup[key]
        real_cols = {c.lower(): c for c in obj["columns"]}
        deps[full_name] = (obj, sorted(real_cols[c] for c in cols if c in real_cols))
    return deps


def make_contract(view, deps, warnings, exported_at):
    consumer = f"{view['schema']}.{view['name']}"
    depends_on = []
    for table in sorted(deps):
        obj, cols = deps[table]
        depends_on.append({
            "table": table,
            "producer_domain": table.split(".")[0],
            "cross_domain": table.split(".")[0] != view["schema"],
            "columns": [{"name": c, "type": obj["columns"][c]["type"]} for c in cols],
        })
    return {
        "contract": consumer,
        "consumer_domain": view["schema"],
        "generated": "automatically",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": f"sys.sql_modules (metadata snapshot {exported_at})",
        "warnings": warnings,
        "depends_on": depends_on,
    }


def generate():
    snap = load_snapshot()
    schema, lookup = build_schema(snap["objects"])
    CONTRACTS.mkdir(exist_ok=True)
    summary = []
    for view in snap["views"]:
        name = f"{view['schema']}.{view['name']}"
        if XML_PATTERN.search(view["definition"]):
            summary.append((name, "SKIPPED", "uses XML methods (known limitation)"))
            continue
        try:
            select = view_select(view["definition"])
            warnings = []
            if uses_select_star(select):
                warnings.append("uses SELECT *: contract protects every column of the table")
            deps = extract_dependencies(select, schema, lookup)
        except Exception as e:  # keep going, but report it
            summary.append((name, "ERROR", str(e).splitlines()[0][:80]))
            continue
        contract = make_contract(view, deps, warnings, snap["exported_at"])
        path = CONTRACTS / f"{name}.yaml"
        path.write_text(yaml.safe_dump(contract, sort_keys=False, allow_unicode=True),
                        encoding="utf-8")
        n_tables = len(contract["depends_on"])
        n_cols = sum(len(d["columns"]) for d in contract["depends_on"])
        cross = sum(1 for d in contract["depends_on"] if d["cross_domain"])
        summary.append((name, "OK", f"{n_tables} tables ({cross} from other domains), {n_cols} columns"))

    print(f"\nContracts written to {CONTRACTS}\n")
    for name, status, info in summary:
        print(f"  {status:8} {name:48} {info}")
    ok = sum(1 for s in summary if s[1] == "OK")
    print(f"\n{ok} contracts generated, {len(summary) - ok} views skipped or failed")


if __name__ == "__main__":
    if "--offline" not in sys.argv:
        import export_metadata
        export_metadata.main()
    generate()
