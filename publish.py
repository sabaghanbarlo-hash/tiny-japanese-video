#!/usr/bin/env python3
"""Publish a rendered video to Instagram as a Reel via Composio.

Usage: publish.py STORY MP4 [--check]
  --check  only verify the API key + Instagram connection, post nothing.
"""
import json, os, re, sys, time, urllib.request, urllib.error

args = [a for a in sys.argv[1:] if not a.startswith("--")]
CHECK = "--check" in sys.argv
story, mp4 = (args + ["", ""])[:2]
KEY = os.environ["COMPOSIO_API_KEY"].strip()
BASE = "https://backend.composio.dev"
url = f'{os.environ.get("PAGES_BASE", "").rstrip("/")}/videos/{os.path.basename(mp4)}'


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


def _req(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={("x-consumer-api-key" if KEY.startswith("ck_") else "x-api-key"): KEY, "Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=400)
        raw = r.read().decode()
        code = r.status
    except urllib.error.HTTPError as e:
        raw, code = e.read().decode(), e.code
    try:
        return code, json.loads(raw)
    except Exception:
        return code, raw


def resolve_identity():
    code, r = _req("GET", "/api/v3/connected_accounts?limit=100")
    allitems = (r.get("items") if isinstance(r, dict) else None) or []
    print(f"Composio answered HTTP {code}. Connections visible to this API key: {len(allitems)}", flush=True)
    if code != 200:
        sys.exit(f"The Composio API key was rejected: {str(r)[:300]}")

    def slug(i):
        t = i.get("toolkit")
        return (t.get("slug") if isinstance(t, dict) else t) or ""

    for i in allitems:
        print("  -", slug(i), "|", i.get("status"), "|", i.get("id"), flush=True)
    items = [i for i in allitems if slug(i).lower() == "instagram" and str(i.get("status", "")).upper() == "ACTIVE"]
    if not items:
        sys.exit("This API key works, but no ACTIVE Instagram connection is visible to it (see the list above).")
    pick = items[0]
    return pick.get("id"), pick.get("user_id")


ACC_ID, USER_ID = resolve_identity()


def call(slug, args):
    body = {"arguments": args, "version": "latest", "connected_account_id": ACC_ID}
    if USER_ID:
        body["user_id"] = USER_ID
    code, r = _req("POST", f"/api/v3/tools/execute/{slug}", body)
    if code == 400 and "EntityIdRequired" in str(r) and USER_ID:
        body["entity_id"] = body.pop("user_id")
        code, r = _req("POST", f"/api/v3/tools/execute/{slug}", body)
    if code != 200:
        sys.exit(f"{slug} failed: HTTP {code} {str(r)[:500]}")
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


if CHECK:
    info = call("INSTAGRAM_GET_USER_INFO", {"ig_user_id": "me", "fields": "id,username,account_type"})
    print("CHECK OK. Instagram account:", json.dumps(info.get("data"), ensure_ascii=False), flush=True)
    sys.exit(0)

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

c = call("INSTAGRAM_POST_IG_USER_MEDIA", {"ig_user_id": "me", "video_url": url, "media_type": "REELS",
                                          "caption": caption(), "share_to_feed": True})
cid = find_id(c.get("data"))
print("container:", cid, flush=True)
p = call("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH", {"ig_user_id": "me", "creation_id": cid, "max_wait_seconds": 300})
print("published:", find_id(p.get("data")), flush=True)
