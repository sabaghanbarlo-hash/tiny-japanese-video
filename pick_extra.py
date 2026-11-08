#!/usr/bin/env python3
"""Print the next unused script from bank-<pool>/ (pool = practice | mistake); prints nothing if the bank is empty.

Used by .github/workflows/daily-extra.yml. Used scripts are listed in posted-extra.txt.
"""
import glob, os, sys

pool = sys.argv[1]
used = set()
if os.path.exists("posted-extra.txt"):
    used = {l.strip() for l in open("posted-extra.txt", encoding="utf-8") if l.strip()}
left = [f for f in sorted(glob.glob(f"bank-{pool}/*.txt")) if os.path.splitext(os.path.basename(f))[0] not in used]
if left:
    print(left[0])
rest = max(len(left) - 1, 0)
print(f"{pool}: {rest} scripts left after this one", file=sys.stderr)
if rest <= 2:
    print(f"::warning::Only {rest} {pool} scripts left in bank-{pool}/ - time to add more.", file=sys.stderr)
