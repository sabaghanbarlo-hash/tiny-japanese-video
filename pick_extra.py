#!/usr/bin/env python3
"""Print the next script to post from bank-<pool>/ (pool = practice | mistake); prints nothing if the bank is empty.

A script counts as DONE once it was handed over AND its video exists in output/. If the render failed (for example a
GitHub hiccup) the script is simply picked again, up to 3 tries, so one bad run never loses a reel.
Used by .github/workflows/daily-extra.yml; hand-overs are listed in posted-extra.txt.
"""
import collections, glob, os, sys

pool = sys.argv[1]
tries = collections.Counter()
if os.path.exists("posted-extra.txt"):
    tries.update(l.strip() for l in open("posted-extra.txt", encoding="utf-8") if l.strip())
left = []
for f in sorted(glob.glob(f"bank-{pool}/*.txt")):
    stem = os.path.splitext(os.path.basename(f))[0]
    done = tries[stem] >= 1 and os.path.exists(os.path.join("output", stem + ".mp4"))
    if not done and tries[stem] < 3:
        left.append(f)
if left:
    print(left[0])
rest = max(len(left) - 1, 0)
print(f"{pool}: {rest} scripts left after this one", file=sys.stderr)
if rest <= 2:
    print(f"::warning::Only {rest} {pool} scripts left in bank-{pool}/ - time to add more.", file=sys.stderr)
