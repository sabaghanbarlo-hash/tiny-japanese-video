#!/usr/bin/env python3
"""Keep the Instagram queue full a few days ahead.

Run by .github/workflows/daily-refill.yml. Steps:
  1. Count videos that are waiting to be posted (rendered, or scripted with a .caption file).
  2. If fewer than DAYS_AHEAD, add stories: first from story-bank/, then (only if
     ANTHROPIC_API_KEY is set) written fresh by Claude. Every script is checked with
     the renderer's own parser before it is accepted.
  3. Print the list of stories that still need rendering to $GITHUB_OUTPUT (render=...).

  python refill_queue.py            do it
  python refill_queue.py --dry-run  show what it would do, change nothing
"""
import glob, json, os, re, shutil, subprocess, sys, tempfile, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

AHEAD = int(os.environ.get("DAYS_AHEAD", "5") or 5)
DRY = "--dry-run" in sys.argv
BANK = "story-bank"
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
SCENES = ("cafe station sakura restaurant store bookstore classroom home airport street park beach hospital ramen "
          "shrine fuji matsuri arcade aquarium onsen snow bakery rainy karaoke rooftop izakaya commute sushi bamboo "
          "autumn castle sunset flowers").split()
TAGS = "#learnjapanese #japantravel #japanesephrases #nihongo #japaneseforbeginners"
CTA = ("Send this to someone going to Japan ✈️\n"
       "What situation in Japan scares you most? Tell me and it becomes the next reel 👇")
JP = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")


def log(*a):
    print(*a, flush=True)


def posted_set():
    return {l.strip() for l in open("posted.txt", encoding="utf-8") if l.strip()} if os.path.exists("posted.txt") else set()


def stem(p):
    return os.path.splitext(os.path.basename(p))[0]


def pending():
    """Names that will be posted before the queue runs dry (same rule as pick_next.py, plus scripted-not-yet-rendered)."""
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
    """Validate with the same renderer the workflow will use: parse the script and draw one frame (no voice, no ffmpeg)."""
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
        dst = f"stories/{name}.txt"
        if DRY:
            log(f"[dry-run] would add {name} from bank"); added.append(name); continue
        shutil.copy(txt, dst)
        cap = txt[:-4] + ".caption"
        if os.path.exists(cap):
            shutil.copy(cap, f"stories/{name}.caption")
        else:
            open(f"stories/{name}.caption", "w", encoding="utf-8").write(f"{slug.replace('-', ' ').title()} 🌸\n\n{TAGS}\n")
        if check(dst):
            os.remove(txt)
            if os.path.exists(cap):
                os.remove(cap)
            added.append(name)
        else:
            os.remove(dst); os.remove(f"stories/{name}.caption")
            os.rename(txt, txt[:-4] + ".rejected")   # keep it out of the bank until someone fixes it
            if os.path.exists(cap):
                os.rename(cap, cap + ".rejected")
    return added


def used_titles():
    out = []
    for f in glob.glob("stories/*.txt"):
        for l in open(f, encoding="utf-8"):
            if l.lower().startswith("title:"):
                out.append(l.split(":", 1)[1].strip()); break
    return sorted(set(out))


PROMPT = """You write one short script for Tiny Japanese, an Instagram Reels series teaching practical Japanese to English-speaking travelers. Characters: Mika (cheerful, a little shy) and Alex (friendly, supportive). Alex may play a shop/restaurant worker.

Rules:
- A real travel-survival situation in Japan a tourist will face. NOT one of these already-used titles: {used}
- 5 or 6 spoken lines total, alternating Mika/Alex. Beginner (JLPT N5), polite form, hiragana/katakana only (no kanji). Put a space after each phrase chunk exactly like: すみません、これを ください。
- Exactly 3 vocab items taken from the story: jp, romaji (Hepburn), en.
- "hook": the first line of the Instagram caption, max 70 characters, ends with one emoji, creates curiosity or names a stake. Vary the pattern ("Nobody tells you...", "Many ... in Japan ...", "Say this before ...", a number, a question). Never use all caps words.
- "value": one short sentence (max 70 chars).
- "scene": one of {scenes}
- Natural, correct Japanese only. If unsure of a phrase, choose a simpler one.

Return ONLY JSON: {{"title": str, "scene": str, "hook": str, "value": str, "lines": [{{"speaker": "Mika"|"Alex", "jp": str, "en": str}}], "vocab": [{{"jp": str, "romaji": str, "en": str}}]}}"""


def llm_story(titles):
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None
    body = json.dumps({"model": MODEL, "max_tokens": 1500, "messages": [
        {"role": "user", "content": PROMPT.format(used="; ".join(titles[-60:]) or "none", scenes=", ".join(SCENES))}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {
        "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        txt = "".join(b.get("text", "") for b in json.load(urllib.request.urlopen(req, timeout=120))["content"])
        return json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
    except (urllib.error.URLError, ValueError, KeyError) as e:
        log(f"::warning::Claude call failed: {str(e)[:200]}")
        return None


def valid(d, titles):
    try:
        L, V = d["lines"], d["vocab"]
        return bool(d["title"] not in titles and d["scene"] in SCENES and 4 <= len(L) <= 7 and len(V) == 3
                and all(x["speaker"] in ("Mika", "Alex") and JP.search(x["jp"]) and x["en"].strip() for x in L)
                and all(JP.search(v["jp"]) and v["romaji"].strip() and v["en"].strip() for v in V)
                and 0 < len(d["hook"]) <= 90 and d["value"].strip())
    except (KeyError, TypeError):
        return False


def write_llm(d, name, episode):
    txt = [f"title: {d['title']}", "cast: mika, alex", f"episode: {episode}", f"scene: {d['scene']}", ""]
    txt += [f"{x['speaker']}: {x['jp']} | {x['en']}" for x in d["lines"]] + [""]
    txt += [f"vocab: {v['jp']} | {v['romaji']} | {v['en']}" for v in d["vocab"]]
    cap = [d["hook"], d["value"], "", "Today's phrases:"] + [f"• {v['jp']} ({v['romaji']}) = {v['en']}" for v in d["vocab"]]
    cap += ["", "Save this for your trip 🔖", CTA, "", TAGS]
    open(f"stories/{name}.txt", "w", encoding="utf-8").write("\n".join(txt) + "\n")
    open(f"stories/{name}.caption", "w", encoding="utf-8").write("\n".join(cap) + "\n")


def add_from_llm(need):
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return []
    added, titles, fails = [], used_titles(), 0
    ep = 1 + max([int(m.group(1)) for f in glob.glob("stories/*.txt") for l in open(f, encoding="utf-8")
                  for m in [re.match(r"episode:\s*(\d+)", l)] if m] or [0])
    for _ in range(need * 2):                      # at most two attempts per story
        if len(added) >= need or fails >= 3:
            break
        d = llm_story(titles)
        if not d or not valid(d, titles):
            fails += 1
            log("::warning::Claude story rejected (invalid shape or repeated title)")
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", d["title"].lower()).strip("-")[:40] or "story"
        name = next_name(slug, len(added))
        if DRY:
            log(f"[dry-run] would write {name}"); added.append(name); continue
        write_llm(d, name, ep)
        if check(f"stories/{name}.txt"):
            added.append(name); titles.append(d["title"]); ep += 1
        else:
            os.remove(f"stories/{name}.txt"); os.remove(f"stories/{name}.caption")
    return added


def main():
    waiting = pending()
    need = max(0, AHEAD - len(waiting))
    log(f"Waiting in queue: {len(waiting)} (target {AHEAD}); need {need} more.")
    added = add_from_bank(need) if need else []
    if len(added) < need:
        added += add_from_llm(need - len(added))
    if len(added) < need:
        log(f"::warning::Queue is short by {need - len(added)}: story-bank is empty and no ANTHROPIC_API_KEY secret "
            f"(or the model returned nothing usable). Add stories to {BANK}/ or add the secret.")
    render = [] if DRY else to_render()
    log("Added:", added or "nothing", "| To render:", render or "nothing")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"render={' '.join(f'stories/{n}.txt' for n in render)}\nadded={len(added)}\n")


if __name__ == "__main__":
    main()
