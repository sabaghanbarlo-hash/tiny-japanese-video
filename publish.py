#!/usr/bin/env python3
"""Publish a rendered video to Instagram as a Reel via Composio (MCP, consumer key).

Usage: publish.py STORY MP4 [--check]
  --check  only verify the key + Instagram connection, post nothing.
"""
import json, os, re, sys, time, urllib.request, urllib.error

args = [a for a in sys.argv[1:] if not a.startswith("--")]
CHECK = "--check" in sys.argv
story, mp4 = (args + ["", ""])[:2]
KEY = os.environ["COMPOSIO_API_KEY"].strip()
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


MCP_URL = "https://connect.composio.dev/mcp"
_session = {"id": None, "n": 0}


def _mcp_post(payload):
    headers = {"x-consumer-api-key": KEY, "Content-Type": "application/json",
               "Accept": "application/json, text/event-stream"}
    if _session["id"]:
        headers["Mcp-Session-Id"] = _session["id"]
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers=headers, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=400)
    except urllib.error.HTTPError as e:
        sys.exit(f"Composio MCP said HTTP {e.code}: {e.read().decode()[:500]}")
    sid = r.headers.get("Mcp-Session-Id")
    if sid:
        _session["id"] = sid
    raw = r.read().decode()
    if not raw.strip():
        return None
    if "data:" in raw and not raw.lstrip().startswith("{"):
        msgs = [l[5:].strip() for l in raw.splitlines() if l.startswith("data:")]
        for m in reversed(msgs):
            try:
                return json.loads(m)
            except Exception:
                continue
        return None
    return json.loads(raw)


def _mcp_rpc(method, params=None, notify=False):
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        _session["n"] += 1
        msg["id"] = _session["n"]
    return _mcp_post(msg)


def _mcp_start():
    r = _mcp_rpc("initialize", {"protocolVersion": "2025-03-26", "capabilities": {},
                                "clientInfo": {"name": "tiny-japanese-video", "version": "1.0"}})
    if not r or "error" in r:
        sys.exit(f"Composio MCP initialize failed: {str(r)[:400]}")
    _mcp_rpc("notifications/initialized", notify=True)
    print("Connected to Composio MCP.", flush=True)


def _mcp_tool(slug, args):
    r = _mcp_rpc("tools/call", {"name": "COMPOSIO_MULTI_EXECUTE_TOOL",
                                "arguments": {"tools": [{"tool_slug": slug, "arguments": args}],
                                              "sync_response_to_workbench": False}})
    if not r or "error" in r:
        sys.exit(f"{slug} failed: {str(r)[:500]}")
    res = r.get("result", {})
    text = "".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
    try:
        top = json.loads(text)
    except Exception:
        sys.exit(f"{slug}: unreadable answer from Composio: {text[:500]}")
    if res.get("isError") or not top.get("successful", True):
        sys.exit(f"{slug} failed: {str(top.get('error') or top)[:600]}")
    items = (top.get("data") or {}).get("results") or []
    if not items:
        sys.exit(f"{slug}: empty answer from Composio: {text[:400]}")
    resp = items[0].get("response", {})
    if not resp.get("successful", True):
        sys.exit(f"{slug} failed: {str(resp.get('error') or resp)[:600]}")
    return resp


def call(slug, args):
    return _mcp_tool(slug, args)


_mcp_start()


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
