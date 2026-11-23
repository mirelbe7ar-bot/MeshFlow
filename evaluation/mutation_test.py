"""MeshFlow evaluation: mutation testing.

For every column and table of the five domains, schema changes ("mutations") are
generated. For each mutation:
  1. PREDICT  - the MeshFlow change checker says PASS or BLOCK (and names consumers)
  2. APPLY    - the change is applied to the real database INSIDE A TRANSACTION
  3. TRUTH    - every consumer view is run; the change is truly breaking if a view
                fails or returns different results than before
  4. RESET    - the transaction is rolled back, so the database is never changed

Results are written row by row to evaluation/results/mutations.csv, so the run can
be stopped and continued later (already tested mutations are skipped).

Usage (from the MeshFlow folder):
  python evaluation\\mutation_test.py --dry-run      # only generate + predict, no database
  python evaluation\\mutation_test.py --limit 20     # quick test on 20 mutations
  python evaluation\\mutation_test.py                # full run
"""
import csv
import hashlib
import re
import sys
import time
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "framework"))
import json
import yaml
import check_change  # the MeshFlow checker

SNAPSHOT = ROOT / "metadata" / "metadata_snapshot.json"
CONTRACTS = ROOT / "contracts"
OUT = ROOT / "evaluation" / "results" / "mutations.csv"
DOMAINS = {"Sales", "Production", "Purchasing", "HumanResources", "Person"}
NO_RETYPE = {"xml", "hierarchyid", "geography", "geometry", "varbinary", "image", "timestamp"}
FIELDS = ["id", "domain", "table", "column", "kind", "sql", "predicted", "predicted_strict",
          "predicted_consumers", "check_ms", "refused", "db_error", "broken_views",
          "broken_xml_views", "truly_breaking", "outcome"]

# ------------------------------------------------------------------ generating mutations

def base(t):
    m = re.match(r"([a-z0-9]+)(?:\((.*)\))?$", t)
    return (m.group(1), m.group(2)) if m else (t, None)


def widened(t):
    b, a = base(t)
    if b == "tinyint": return "smallint"
    if b == "smallint": return "int"
    if b == "int": return "bigint"
    if b == "smallmoney": return "money"
    if b in ("nvarchar", "varchar") and a and a != "max": return f"{b}(max)"
    if b == "nchar" and a: return f"nvarchar({a})"
    if b in ("decimal", "numeric") and a and "," in a:
        p, s = (int(x) for x in a.split(","))
        if p + 2 <= 38: return f"{b}({p + 2},{s})"
    return None


def retyped(t):
    """A non-widening type change of the kind producers make (e.g. number -> text)."""
    b, a = base(t)
    if b in NO_RETYPE: return None
    if b in ("nvarchar", "nchar") and a and a != "max": return f"varchar({a})"
    if b in ("varchar", "char"): return None
    return "nvarchar(100)"


def generate(snapshot):
    muts = []
    for name, obj in sorted(snapshot["objects"].items()):
        if obj["kind"] != "table": continue
        schema, table = name.split(".", 1)
        if schema not in DOMAINS: continue
        for col, info in obj["columns"].items():
            null = "NULL" if info.get("nullable", True) else "NOT NULL"
            t = info["type"]
            muts.append(("rename_column", schema, table, col,
                         f"EXEC sp_rename '{schema}.{table}.{col}', '{col}_mut', 'COLUMN';"))
            muts.append(("drop_column", schema, table, col,
                         f"ALTER TABLE {schema}.{table} DROP COLUMN {col};"))
            r = retyped(t)
            if r:
                muts.append(("type_change", schema, table, col,
                             f"ALTER TABLE {schema}.{table} ALTER COLUMN {col} {r} {null};"))
            wdn = widened(t)
            if wdn:
                muts.append(("type_widening", schema, table, col,
                             f"ALTER TABLE {schema}.{table} ALTER COLUMN {col} {wdn} {null};"))
        muts.append(("add_column", schema, table, "", f"ALTER TABLE {schema}.{table} ADD mut_new_col int NULL;"))
        muts.append(("drop_table", schema, table, "", f"DROP TABLE {schema}.{table};"))
        muts.append(("rename_table", schema, table, "", f"EXEC sp_rename '{schema}.{table}', '{table}_mut';"))
    return [dict(id=i + 1, kind=k, domain=s, table=f"{s}.{t}", column=c, sql=q)
            for i, (k, s, t, c, q) in enumerate(muts)]

# ------------------------------------------------------------------ ground truth helpers

def canon(v):
    if v is None: return "\x00"
    if isinstance(v, Decimal): v = v.normalize()
    if isinstance(v, float): v = round(v, 9)
    if isinstance(v, (bytes, bytearray)): return v.hex()
    return str(v)


def signature(cur, view):
    """Column names + hash of all rows (order-independent, type-independent values)."""
    cur.execute(f"SELECT * FROM {view}")
    cols = tuple(d[0] for d in cur.description)
    rows = sorted("\x1f".join(canon(v) for v in row) for row in cur.fetchall())
    h = hashlib.sha256("\x1e".join(rows).encode("utf-8")).hexdigest()
    return cols, len(rows), h


def main():
    dry = "--dry-run" in sys.argv
    limit = None
    if "--limit" in sys.argv: limit = int(sys.argv[sys.argv.index("--limit") + 1])

    snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    muts = generate(snap)
    contract_views = sorted(p.stem for p in CONTRACTS.glob("*.yaml")
                            if (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("generated") == "automatically")
    all_views = sorted(f"{v['schema']}.{v['name']}" for v in snap["views"])
    xml_views = [v for v in all_views if v not in contract_views]
    print(f"{len(muts)} mutations, {len(contract_views)} consumer views with contracts, "
          f"{len(xml_views)} views without contracts (reported separately)")

    if "--fresh" in sys.argv and OUT.exists():           # start again, keep the old file
        OUT.rename(OUT.with_name(f"mutations_old_{int(time.time())}.csv"))
    done = set()
    if OUT.exists():
        with OUT.open(encoding="utf-8", newline="") as f:
            done = {int(r["id"]) for r in csv.DictReader(f)}
    todo = [m for m in muts if m["id"] not in done]
    if limit: todo = todo[:limit]
    print(f"{len(done)} already tested, {len(todo)} to test now")

    if dry:
        from collections import Counter
        print(Counter(m["kind"] for m in muts))
        for m in muts[:5] + muts[-3:]:
            ov, res = check_change.check(m["sql"])
            print(m["id"], m["kind"], m["sql"], "->", ov, [c for r in res for c in r["consumers"]][:5])
        return

    import db
    conn = db.connect()
    conn.autocommit = False
    cur = conn.cursor()
    cur.execute("SET LOCK_TIMEOUT 60000")

    print("Measuring the baseline of every view ...")
    base_sig = {}
    for v in all_views:
        base_sig[v] = signature(cur, v)
    conn.rollback()

    new_file = not OUT.exists()
    f = OUT.open("a", encoding="utf-8", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS)
    if new_file: w.writeheader()

    start = time.time()
    for n, m in enumerate(todo, 1):
        t0 = time.perf_counter()
        pred, res = check_change.check(m["sql"])
        check_ms = round((time.perf_counter() - t0) * 1000, 1)
        pred_strict, _ = check_change.check(m["sql"], strict=True)
        consumers = sorted({c for r in res for c in r["consumers"]})

        row = dict(m, predicted=pred, predicted_strict=pred_strict,
                   predicted_consumers=";".join(consumers), check_ms=check_ms,
                   refused="no", db_error="", broken_views="", broken_xml_views="",
                   truly_breaking="", outcome="")
        try:
            cur.execute(m["sql"])
            while cur.nextset(): pass
        except Exception as e:
            msg = str(e)
            msg = msg.split("[SQL Server]")[-1] if "[SQL Server]" in msg else msg
            row.update(refused="yes", db_error=msg.replace("\n", " ")[:250], outcome="REFUSED")
            conn.rollback()
            w.writerow(row); f.flush()
            continue

        broken, broken_xml = [], []
        for v in all_views:
            try:
                cur.execute("SAVE TRANSACTION before_view")
                ok = signature(cur, v) == base_sig[v]
            except Exception:
                ok = False
                try:
                    state = cur.execute("SELECT XACT_STATE()").fetchone()[0]
                except Exception:
                    state = -1
                if state == -1:                      # transaction is doomed: start again
                    conn.rollback()
                    cur.execute(m["sql"])
                    while cur.nextset(): pass
                else:
                    try: cur.execute("ROLLBACK TRANSACTION before_view")
                    except Exception: pass
            if not ok:
                (broken if v in contract_views else broken_xml).append(v)
        conn.rollback()

        truly = bool(broken)
        outcome = {(True, "BLOCK"): "TP", (False, "BLOCK"): "FP",
                   (True, "PASS"): "FN", (False, "PASS"): "TN"}[(truly, pred)]
        row.update(broken_views=";".join(broken), broken_xml_views=";".join(broken_xml),
                   truly_breaking="yes" if truly else "no", outcome=outcome)
        w.writerow(row); f.flush()

        if n % 25 == 0 or n == len(todo):
            el = time.time() - start
            print(f"  {n}/{len(todo)} done, {el / 60:.1f} min, about {el / n * (len(todo) - n) / 60:.0f} min left")

    f.close()
    conn.close()
    print(f"Results saved to {OUT}")


if __name__ == "__main__":
    main()
