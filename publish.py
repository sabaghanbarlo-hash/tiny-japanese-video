#!/usr/bin/env python3
"""Publish a rendered video to Instagram as a Reel using the official Instagram API (no third parties)."""
import json, os, re, sys, time, urllib.parse, urllib.request, urllib.error

story, mp4 = sys.argv[1], sys.argv[2]
TOKEN = os.environ["IG_ACCESS_TOKEN"].strip()
API = "https://graph.instagram.com/v23.0"
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
    return out + "\nSave this to practice later! 💌\n#learnjapanese #japanese #nihongo #japaneselanguage #jlpt #japanesefortbeginners"


def api(method, path, data=None):
    data = dict(data or {}, access_token=TOKEN)
    if method == "GET":
        req = urllib.request.Request(f"{API}{path}?{urllib.parse.urlencode(data)}")
    else:
        req = urllib.request.Request(f"{API}{path}", data=urllib.parse.urlencode(data).encode(), method="POST")
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sys.exit(f"Instagram said no ({method} {path}): HTTP {e.code} {e.read().decode()[:600]}")


print("Waiting for video to be reachable:", url, flush=True)
for _ in range(60):
    try:
        if urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=20).status == 200:
            break
    except Exception:
        pass
    time.sleep(10)
else:
    sys.exit("Video URL never became reachable")

me = api("GET", "/me", {"fields": "username,account_type"})
print("Posting as:", me.get("username"), "|", me.get("account_type"), flush=True)
c = api("POST", "/me/media", {"media_type": "REELS", "video_url": url, "caption": caption(), "share_to_feed": "true"})
cid = c["id"]
print("container:", cid, flush=True)
for _ in range(60):
    st = api("GET", f"/{cid}", {"fields": "status_code,status"})
    print("processing:", st.get("status_code"), flush=True)
    if st.get("status_code") == "FINISHED":
        break
    if st.get("status_code") in ("ERROR", "EXPIRED"):
        sys.exit(f"Instagram could not process the video: {st}")
    time.sleep(10)
else:
    sys.exit("Instagram took too long to process the video")
pub = api("POST", "/me/media_publish", {"creation_id": cid})
print("published:", pub.get("id"), flush=True)
