#!/usr/bin/env python3
"""Keep the Instagram queue full a few days ahead, from the pre-written scripts in story-bank/.

Run by .github/workflows/daily-refill.yml. No AI, no API keys:
  1. Count videos waiting to be posted (rendered, or scripted with a .caption file).
  2. If fewer than DAYS_AHEAD, move the next scripts, IN ORDER, from story-bank/ to stories/.
     Every script is checked with the renderer's own parser first; a broken one is skipped
     (renamed *.rejected) so it can never stall the queue.
  3. Print the stories that still need rendering to $GITHUB_OUTPUT (render=...).

  python refill_queue.py            do it
  python refill_queue.py --dry-run  show what it would do, change nothing
To add content: drop NAME.txt + NAME.caption into story-bank/. Order = file name order.
"""
import glob, os, re, shutil, subprocess, sys, tempfile
from datetime import datetime, timedelta, timezone

AHEAD = int(os.environ.get("DAYS_AHEAD", "5") or 5)
DRY = "--dry-run" in sys.argv
BANK = "story-bank"
TAGS = "#learnjapanese #japantravel #japanesephrases #nihongo #japaneseforbeginners"


def log(*a):
    print(*a, flush=True)


def stem(p):
    return os.path.splitext(os.path.basename(p))[0]


def posted_set():
    return {l.strip() for l in open("posted.txt", encoding="utf-8") if l.strip()} if os.path.exists("posted.txt") else set()


def pending():
    """Names that will post before the queue runs dry: same rule as pick_next.py, plus scripted-not-yet-rendered."""
    posted, out = posted_set(), set()
    for mp4 in glob.glob("output/*.mp4"):
        n = stem(mp4)
        if not n.startswith("lesson-") and n not in posted and os.path.exists(f"stories/{n}.txt"):
            out.add(n)
    for cap in glob.glob("stories/*.caption"):          # only refilled stories have a .caption sidecar
        n = stem(cap)
        if n not in posted and os.path.exists(f"stories/{n}.txt"):
            out.add(n)
    return sorted(out)


def to_render():
    return sorted(stem(c) for c in glob.glob("stories/*.caption")
                  if os.path.exists(f"stories/{stem(c)}.txt") and not os.path.exists(f"output/{stem(c)}.mp4"))


def check(path):
    """Validate with the renderer the workflow will use: parse the script and draw one frame (no voice, no ffmpeg)."""
    if re.search(r"^format:\s*story", open(path, encoding="utf-8").read(), re.I | re.M):
        cmd = [sys.executable, "story.py", path, "--check"]
    elif os.path.exists("tinyvideo.py"):
        cmd = [sys.executable, "tinyvideo.py", path, "--preview",
               os.path.join(tempfile.gettempdir(), "refill-check.png"), "--dummy-audio"]
    else:
        return True
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log(f"::warning::{path} rejected by the renderer: {(r.stdout + r.stderr).strip()[-300:]}")
    return r.returncode == 0


def next_name(slug, i):
    t = datetime.now(timezone.utc) + timedelta(minutes=i)
    return f"{t:%Y%m%d%H%M}-{slug}"


def add_from_bank(need):
    added = []
    for txt in sorted(glob.glob(f"{BANK}/*.txt")):
        if len(added) >= need:
            break
        slug = re.sub(r"^\d{12}-", "", stem(txt))
        name = next_name(slug, len(added))
        if DRY:
            log(f"[dry-run] would add {name}  <-  {os.path.basename(txt)}")
            added.append(name)
            continue
        cap = txt[:-4] + ".caption"
        shutil.copy(txt, f"stories/{name}.txt")
        if os.path.exists(cap):
            shutil.copy(cap, f"stories/{name}.caption")
        else:
            open(f"stories/{name}.caption", "w", encoding="utf-8").write(f"{slug.replace('-', ' ').title()} 🌸\n\n{TAGS}\n")
        if check(f"stories/{name}.txt"):
            os.remove(txt)
            if os.path.exists(cap):
                os.remove(cap)
            added.append(name)
        else:                                            # keep a broken script out of the queue and out of the bank
            os.remove(f"stories/{name}.txt")
            os.remove(f"stories/{name}.caption")
            os.rename(txt, txt[:-4] + ".rejected")
            if os.path.exists(cap):
                os.rename(cap, cap + ".rejected")
    return added


def main():
    waiting = pending()
    need = max(0, AHEAD - len(waiting))
    left = len(glob.glob(f"{BANK}/*.txt"))
    log(f"Waiting in queue: {len(waiting)} (target {AHEAD}); need {need} more; {left} scripts left in {BANK}/.")
    added = add_from_bank(need) if need else []
    if len(added) < need:
        log(f"::warning::Queue is short by {need - len(added)}: {BANK}/ has no more scripts. "
            f"Add NAME.txt + NAME.caption files to {BANK}/ to keep posting.")
    elif left - len(added) <= 7 and not DRY:
        log(f"::warning::Only {left - len(added)} scripts left in {BANK}/ (about that many days). Time to add more.")
    render = [] if DRY else to_render()
    log("Added:", added or "nothing", "| To render:", render or "nothing")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"render={' '.join(f'stories/{n}.txt' for n in render)}\nadded={len(added)}\n")


if __name__ == "__main__":
    main()
