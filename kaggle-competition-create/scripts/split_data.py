#!/usr/bin/env python3
"""Build Kaggle competition files from one labeled CSV (stdlib only).

Usage:
  python3 -I split_data.py --src raw.csv --target label --out build \
      [--id-col id] [--drop COL ...] [--test-frac 0.3] [--seed 42] \
      [--usage-split] [--no-header] [--columns a,b,c,...] [--target-map M=1,B=0]

Writes:
  <out>/data/train.csv              anonymous id + features + target
  <out>/data/test.csv               anonymous id + features
  <out>/data/sample_submission.csv  id + constant first class value (alphabetically)
  <out>/private/solution.csv        id + target (+ Usage Public/Private when --usage-split)

Original ids (--id-col) and --drop columns are removed; new ids are 0..N-1 (train first, then test).
Split is stratified on the target and shuffled with --seed.
"""
import argparse, csv, os, random, sys
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--target", required=True, help="target column name (or index with --no-header)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--id-col", default=None, help="original id column to drop")
    ap.add_argument("--drop", nargs="*", default=[])
    ap.add_argument("--test-frac", type=float, default=0.3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--usage-split", action="store_true", help="add Usage column (Public/Private ~50/50, stratified)")
    ap.add_argument("--no-header", action="store_true")
    ap.add_argument("--columns", default=None, help="comma-separated column names when --no-header")
    ap.add_argument("--target-map", default=None, help="e.g. M=1,B=0 to remap target values")
    a = ap.parse_args()

    rows = list(csv.reader(open(a.src, newline="")))
    if a.no_header:
        if not a.columns:
            sys.exit("--columns required with --no-header")
        header = a.columns.split(",")
    else:
        header, rows = rows[0], rows[1:]
    assert all(len(r) == len(header) for r in rows), "ragged rows"
    tidx = int(a.target) if a.target.isdigit() and a.no_header else header.index(a.target)
    tname = header[tidx]
    drop = {header.index(c) for c in a.drop}
    if a.id_col:
        drop.add(header.index(a.id_col))
    feat_idx = [i for i in range(len(header)) if i != tidx and i not in drop]
    tmap = dict(kv.split("=", 1) for kv in a.target_map.split(",")) if a.target_map else {}
    lab = lambda r: tmap.get(r[tidx], r[tidx])

    rng = random.Random(a.seed)
    groups = defaultdict(list)
    for r in rows:
        groups[lab(r)].append(r)
    train, test = [], []
    for k in sorted(groups):
        g = groups[k]
        rng.shuffle(g)
        n_test = round(len(g) * a.test_frac)
        test += g[:n_test]
        train += g[n_test:]
    rng.shuffle(train)
    rng.shuffle(test)

    os.makedirs(os.path.join(a.out, "data"), exist_ok=True)
    os.makedirs(os.path.join(a.out, "private"), exist_ok=True)

    def w(path, hdr, recs):
        with open(path, "w", newline="") as f:
            c = csv.writer(f)
            c.writerow(hdr)
            c.writerows(recs)

    fh = [header[i] for i in feat_idx]
    nid = 0
    tr, te, sol = [], [], []
    for r in train:
        tr.append([nid] + [r[i] for i in feat_idx] + [lab(r)]); nid += 1
    for r in test:
        te.append([nid] + [r[i] for i in feat_idx]); sol.append([nid, lab(r)]); nid += 1

    default = sorted(groups)[0]
    w(os.path.join(a.out, "data", "train.csv"), ["id"] + fh + [tname], tr)
    w(os.path.join(a.out, "data", "test.csv"), ["id"] + fh, te)
    w(os.path.join(a.out, "data", "sample_submission.csv"), ["id", tname], [[r[0], default] for r in sol])

    if a.usage_split:
        by = defaultdict(list)
        for r in sol:
            by[r[1]].append(r)
        out = []
        for k in sorted(by):
            g = by[k]; rng.shuffle(g); h = len(g) // 2
            out += [r + ["Public"] for r in g[:h]] + [r + ["Private"] for r in g[h:]]
        out.sort(key=lambda r: int(r[0]))
        w(os.path.join(a.out, "private", "solution.csv"), ["id", tname, "Usage"], out)
    else:
        w(os.path.join(a.out, "private", "solution.csv"), ["id", tname], sol)

    # validation (ids compared with headers removed)
    ids_te = [r[0] for r in te]
    assert ids_te == [r[0] for r in sol]
    assert not (set(map(str, ids_te)) & {str(r[0]) for r in tr})
    assert all(c != "" for r in tr + te for c in r), "empty cells present"
    print(f"train={len(tr)} test={len(te)} features={len(fh)} target={tname} "
          f"classes={ {k: len(v) for k, v in groups.items()} } validation=OK")


if __name__ == "__main__":
    main()
