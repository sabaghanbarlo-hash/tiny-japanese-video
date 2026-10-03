#!/usr/bin/env python3
"""Publish a rendered video to Instagram as a Reel via Composio (uses your connected Instagram account)."""
import json, os, re, sys, time, urllib.request, urllib.error

story, mp4 = sys.argv[1], sys.argv[2]
KEY = os.environ["COMPOSIO_API_KEY"]
ACC = os.environ.get("COMPOSIO_CONNECTED_ACCOUNT_ID", "")
url = f'{os.environ["PAGES_BASE"].rstrip("/")}/videos/{os.path.basename(mp4)}'


def caption():
    side = os.path.splitext(story)[0] + ".caption"
    if os.path.exists(side):
        c = open(side, encoding="utf-8").read().strip()
        if c:
            return c
    title, vocab = "Tiny Japanese", []
    for l in open(story, encoding="utf-8"):
        l = l.strip()
        if l.lower().startswith("title:"):
            title = l.split(":", 1)[1].strip()
        elif l.lower().startswith("vocab:"):
            p = [x.strip() for x in l.split(":", 1)[1].split("|")]
            vocab.append(f"• {p[0]} ({p[1]}) = {p[-1]}" if len(p) == 3 else f"• {p[0]} = {p[-1]}")
    out = f"{title} 🌸\nLearn Japanese one tiny story at a time.\n"
    if vocab:
        out += "\nToday's words:\n" + "\n".join(vocab) + "\n"
    return out + "\nSave this to practice later! 💌\n#learnjapanese #japanese #nihongo #japaneselanguage #jlpt #japaneseforbeginners"


def call(slug, args):
    body = {"arguments": args}
    if ACC:
        body["connected_account_id"] = ACC
    req = urllib.request.Request(f"https://backend.composio.dev/api/v3/tools/execute/{slug}",
                                 data=json.dumps(body).encode(),
                                 headers={"x-api-key": KEY, "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=400))
    except urllib.error.HTTPError as e:
        sys.exit(f"{slug} failed: {e.code} {e.read().decode()[:500]}")
    if not r.get("successful", True):
        sys.exit(f"{slug} failed: {r.get('error')}")
    return r


def find_id(o):
    if isinstance(o, dict):
        if isinstance(o.get("id"), (str, int)):
            return str(o["id"])
        for v in o.values():
            f = find_id(v)
            if f:
                return f
    return None


print("Waiting for video to be reachable:", url)
for _ in range(60):
    try:
        if urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20).status == 200:
            break
    except Exception:
        pass
    time.sleep(10)
else:
    sys.exit("Video URL never became reachable")

c = call("INSTAGRAM_POST_IG_USER_MEDIA", {"ig_user_id": "me", "video_url": url, "media_type": "REELS",
                                          "caption": caption(), "share_to_feed": True})
cid = find_id(c.get("data"))
print("container:", cid)
p = call("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH", {"ig_user_id": "me", "creation_id": cid, "max_wait_seconds": 300})
print("published:", find_id(p.get("data")))
