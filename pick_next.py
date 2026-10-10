#!/usr/bin/env python3
"""Print the next video (as stories/<name>.txt) that has not been posted yet; empty if the queue is empty."""
import glob, os
posted = set()
if os.path.exists("posted.txt"):
    posted = {l.strip() for l in open("posted.txt") if l.strip()}
for mp4 in sorted(glob.glob("output/*.mp4")):
    name = os.path.splitext(os.path.basename(mp4))[0]
    if name not in posted and os.path.exists(f"stories/{name}.txt"):
        print(f"stories/{name}.txt")
        break
