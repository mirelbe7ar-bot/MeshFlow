"""Analyze the mutation testing results (evaluation/results/mutations.csv).

Writes evaluation/results/summary.md, fn_fp_cases.csv and (if matplotlib is
installed) two charts. Usage:  python evaluation\\analyze.py
"""
import csv
from collections import Counter, defaultdict
from pathlib import Path

RES = Path(__file__).resolve().parent / "results"
rows = list(csv.DictReader((RES / "mutations.csv").open(encoding="utf-8", newline="")))


def metrics(rs, key="predicted"):
    c = Counter()
    for r in rs:
        if r["refused"] == "yes": continue
        truly = r["truly_breaking"] == "yes"
        pred = r[key] == "BLOCK"
        c[("TP" if pred else "FN") if truly else ("FP" if pred else "TN")] += 1
    tp, fp, fn, tn = c["TP"], c["FP"], c["FN"], c["TN"]
    rec = tp / (tp + fn) if tp + fn else None
    pre = tp / (tp + fp) if tp + fp else None
    f1 = 2 * pre * rec / (pre + rec) if rec and pre else None
    return dict(TP=tp, FP=fp, FN=fn, TN=tn, recall=rec, precision=pre, f1=f1)


pct = lambda x: "–" if x is None else f"{x * 100:.1f}%"
applied = [r for r in rows if r["refused"] == "no"]
refused = [r for r in rows if r["refused"] == "yes"]
m, ms = metrics(rows), metrics(rows, "predicted_strict")
tps = [r for r in applied if r["truly_breaking"] == "yes" and r["predicted"] == "BLOCK"]
exact = sum(1 for r in tps if set(filter(None, r["predicted_consumers"].split(";"))) == set(filter(None, r["broken_views"].split(";"))))
times = [float(r["check_ms"]) for r in rows]
xml_only = sum(1 for r in applied if r["broken_xml_views"] and r["truly_breaking"] == "no")

out = ["# Mutation testing results", "",
       f"- Mutations generated: {len(rows)}",
       f"- Refused by SQL Server (never reach a consumer): {len(refused)}",
       f"- Applied and measured: {len(applied)}",
       f"- Truly breaking: {sum(1 for r in applied if r['truly_breaking'] == 'yes')}", "",
       "## Confusion matrix (default mode)", "",
       "| | Truly breaking | Truly safe |", "|---|---|---|",
       f"| Predicted breaking (BLOCK) | TP = {m['TP']} | FP = {m['FP']} |",
       f"| Predicted safe (PASS) | FN = {m['FN']} | TN = {m['TN']} |", "",
       "## Main measures", "", "| Measure | Default mode | Strict mode | Target |", "|---|---|---|---|",
       f"| Recall | {pct(m['recall'])} | {pct(ms['recall'])} | at least 95% |",
       f"| Precision | {pct(m['precision'])} | {pct(ms['precision'])} | at least 90% |",
       f"| F1 | {pct(m['f1'])} | {pct(ms['f1'])} | – |",
       f"| Consumer accuracy (TP with exactly the right consumers) | {pct(exact / len(tps) if tps else None)} | | – |",
       f"| Average check time | {sum(times) / len(times):.1f} ms | | a few seconds |", "",
       f"Changes that broke only views without contracts (XML views, known limitation): {xml_only}", "",
       "## By change type (default mode)", "", "| Change type | Applied | Refused | TP | FP | FN | TN | Recall | Precision |",
       "|---|---|---|---|---|---|---|---|---|"]
by_kind = defaultdict(list)
for r in rows: by_kind[r["kind"]].append(r)
for k, rs in sorted(by_kind.items()):
    mk = metrics(rs)
    out.append(f"| {k} | {sum(1 for r in rs if r['refused'] == 'no')} | {sum(1 for r in rs if r['refused'] == 'yes')} | "
               f"{mk['TP']} | {mk['FP']} | {mk['FN']} | {mk['TN']} | {pct(mk['recall'])} | {pct(mk['precision'])} |")
out += ["", "## By producer domain (default mode)", "", "| Domain | Applied | TP | FP | FN | TN | Recall | Precision |", "|---|---|---|---|---|---|---|---|"]
by_dom = defaultdict(list)
for r in rows: by_dom[r["domain"]].append(r)
for d, rs in sorted(by_dom.items()):
    md = metrics(rs)
    out.append(f"| {d} | {sum(1 for r in rs if r['refused'] == 'no')} | {md['TP']} | {md['FP']} | {md['FN']} | {md['TN']} | {pct(md['recall'])} | {pct(md['precision'])} |")
(RES / "summary.md").write_text("\n".join(out) + "\n", encoding="utf-8")

cases = [r for r in applied if r["outcome"] in ("FN", "FP")]
with (RES / "fn_fp_cases.csv").open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(cases)

try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(4.5, 4), dpi=200)
    grid = [[m["TP"], m["FP"]], [m["FN"], m["TN"]]]
    ax.imshow(grid, cmap="Greys", alpha=0.35)
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{['TP', 'FP', 'FN', 'TN'][i * 2 + j]}\n{grid[i][j]}", ha="center", va="center", fontsize=12)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Truly breaking", "Truly safe"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Blocked", "Passed"])
    fig.savefig(RES / "confusion_matrix.png", bbox_inches="tight", facecolor="white")
    kinds = sorted(by_kind)
    fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
    rec = [(metrics(by_kind[k])["recall"] or 0) * 100 for k in kinds]
    pre = [(metrics(by_kind[k])["precision"] or 0) * 100 for k in kinds]
    x = range(len(kinds))
    ax.bar([i - 0.2 for i in x], rec, 0.4, label="Recall", color="#555555")
    ax.bar([i + 0.2 for i in x], pre, 0.4, label="Precision", color="#bbbbbb")
    ax.set_xticks(list(x)); ax.set_xticklabels([k.replace("_", "\n") for k in kinds], fontsize=8)
    ax.set_ylabel("%"); ax.set_ylim(0, 105); ax.legend()
    fig.savefig(RES / "by_change_type.png", bbox_inches="tight", facecolor="white")
except ImportError:
    print("matplotlib not installed: charts skipped (pip install matplotlib)")
print("\n".join(out[:30]))
print(f"\nSaved: {RES / 'summary.md'}")
