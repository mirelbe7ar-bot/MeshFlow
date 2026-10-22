import re, sys, glob, os
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.scope import traverse_scope

def lookup(scope, alias):
    s = scope
    while s is not None:
        if alias in s.sources:
            return s.sources[alias]
        s = s.parent
    return None

def deps(sql):
    tree = sqlglot.parse_one(sql, read="tsql")
    used = {}
    for scope in traverse_scope(tree):
        for col in scope.columns:
            src = lookup(scope, col.table)
            if isinstance(src, exp.Table):
                key = f"{src.db}.{src.name}"
                used.setdefault(key, set()).add(col.name)
    return used

for f in sorted(glob.glob(sys.argv[1] + "/*.sql")):
    text = open(f, encoding="utf-8-sig").read()
    m = re.search(r"CREATE\s+OR\s+ALTER\s+VIEW\s+(\S+)\s+AS\s+(.*?)\n\s*GO\b", text, re.S | re.I)
    name, body = m.group(1), m.group(2)
    print(f"\n== {name}")
    try:
        for t, cols in sorted(deps(body).items()):
            print(f"   {t:38} {', '.join(sorted(cols))}")
    except Exception as e:
        print("   ERROR:", e)
