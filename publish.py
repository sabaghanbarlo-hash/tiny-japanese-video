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


def _req(method, path, body=None):
    req = urllib.request.Request(f"https://backend.composio.dev{path}",
                                 data=json.dumps(body).encode() if body is not None else None,
                                 method=method,
                                 headers={"x-api-key": KEY, "Content-Type": "application/json"})
    try:
        return 200, json.load(urllib.request.urlopen(req, timeout=400))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:600]


def resolve_identity():
    """Composio needs the connected account AND the user that owns it. Look both up from the API key."""
    code, r = _req("GET", "/api/v3/connected_accounts?toolkit_slugs=instagram&statuses=ACTIVE&limit=50")
    items = (r.get("items") if isinstance(r, dict) else None) or []
    print(f"Found {len(items)} active Instagram connection(s) for this API key.", flush=True)
    if not items:
        sys.exit("No active Instagram connection was found for this COMPOSIO_API_KEY. "
                 "Make sure the key comes from the same Composio project where Instagram is connected.")
    pick = next((i for i in items if i.get("id") == ACC), None) or items[0]
    return pick.get("id"), pick.get("user_id")


ACC_ID, USER_ID = resolve_identity()


def call(slug, args):
    # "version": "latest" is required when calling the REST API directly, otherwise Composio uses an
    # old base version of the toolkit that does not contain these Instagram tools ("Tool not found").
    body = {"arguments": args, "version": "latest", "connected_account_id": ACC_ID}
    if USER_ID:
        body["user_id"] = USER_ID
    code, r = _req("POST", f"/api/v3/tools/execute/{slug}", body)
    if code == 400 and "EntityIdRequired" in str(r) and USER_ID:
        body["entity_id"] = body.pop("user_id")
        code, r = _req("POST", f"/api/v3/tools/execute/{slug}", body)
    if code != 200:
        sys.exit(f"{slug} failed: HTTP {code} {r}")
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
print("container:", cid)
p = call("INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH", {"ig_user_id": "me", "creation_id": cid, "max_wait_seconds": 300})
print("published:", find_id(p.get("data")))
