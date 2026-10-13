#!/usr/bin/env python3
"""Tiny Japanese Stories Studio: sequence JSON -> 1080x1920 Story slides (JPEG) + Story clips (MP4) + manifest + QC report.

Reuses tinyvideo.py (fonts, Mika & Alex, scenes, edge-tts voices). All Japanese/English text is drawn from the
sequence JSON as live text at render time (never baked into generated art), so edit the JSON and re-render.

  python storystudio.py render [--sequence ID] [--dummy-audio] [--no-video]
"""
import argparse, glob, json, os, random, re, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw
import tinyvideo as tv
from tinyvideo import W, H, BRAND, font, wrap, balanced, card_image, vgrad, blossoms, sprite, SCENES, CHARS, FPS, write_wav

ROOT = os.path.dirname(os.path.abspath(__file__))
SEQ_DIR = os.path.join(ROOT, "ig-stories", "sequences")
OUT_DIR = os.path.join(ROOT, "ig-stories", "out")
CFG_PATH = os.path.join(ROOT, "ig-stories", "config.json")
SAFE_TOP, SAFE_BOTTOM = 250, 1580          # Instagram covers the top/bottom of Stories with its own UI
INK, SOFT = (52, 40, 44), (90, 78, 80)
LETTERS = "ABCD"
TYPES = {"intro", "word", "convo", "quiz", "reveal"}


def load_cfg():
    cfg = {"account_alias": "Tiny Japanese", "handle": "@tinyjapanes", "timezone": "UTC",
           "cta_default": "More free lessons: link in bio", "voice_rate": "-12%"}
    if os.path.exists(CFG_PATH):
        cfg.update(json.load(open(CFG_PATH, encoding="utf-8")))
    return cfg


# ---------- drawing helpers ----------
def static_bg(scene):
    sc = SCENES.get(scene, SCENES["sakura"])
    img = vgrad(W, H, sc["top"], sc["bot"])
    blossoms(ImageDraw.Draw(img), random.Random(11), (0, SAFE_TOP - 60, W, SAFE_BOTTOM), 46)
    return img


def place(img, card, y, warns, what):
    """Paste a card (centered); returns y for the next card and records safe-zone problems."""
    img.paste(card, ((W - card.width) // 2, y), card)
    bottom = y + card.height - 40
    if y + 40 < SAFE_TOP - 10:
        warns.append(f"{what}: starts at y={y + 40}, inside the top UI zone (<{SAFE_TOP})")
    if bottom > SAFE_BOTTOM:
        warns.append(f"{what}: reaches y={bottom}, inside the bottom UI zone (>{SAFE_BOTTOM})")
    return y + card.height - 40 + 10


def lines_parts(text_lines, size, color, adv, bold=True, maxw=840):
    f = font(size, bold)
    return [(t, f, color, adv) for raw in text_lines for t in wrap(raw, f, maxw)]


def footer(img, cfg, y=1505):
    ImageDraw.Draw(img).text((W / 2, y), cfg["handle"], font=font(36), fill=BRAND, anchor="mm")


def fit(text, start, stop, maxw=840, bold=True):
    return next((s for s in range(start, stop, -10) if font(s, bold).getlength(text) <= maxw), stop)


# ---------- static slide types ----------
def slide_intro(sl, seq, cfg):
    warns, img = [], static_bg(seq.get("scene", "sakura"))
    cy, sc = 780, SCENES.get(seq.get("scene", "sakura"), SCENES["sakura"])
    top = cy + 585
    d = ImageDraw.Draw(img)
    d.rectangle((0, top, W, H), fill=sc["floor"])
    for name in ("Mika", "Alex"):
        s = sprite(name, 0, False)
        img.paste(s, (CHARS[name]["x"], cy), s)
    band = Image.new("RGBA", (W, 175), (0, 0, 0, 0)); g = ImageDraw.Draw(band)
    g.rectangle((0, 55, W, 125), fill=sc["table"]); g.rectangle((0, 125, W, 175), fill=sc["edge"])
    img.paste(band, (0, top - 55), band)
    parts = lines_parts(sl["headline"], 72, INK, 92) + [("", None, None, 18)] + lines_parts([sl.get("sub", "")], 40, BRAND, 56, False)
    place(img, card_image(sl.get("kicker", "Today's tiny word"), BRAND, parts), SAFE_TOP + 20, warns, "intro card")
    footer(img, cfg)
    return img, warns


def slide_word(sl, seq, cfg):
    warns, img = [], static_bg(seq.get("scene", "sakura"))
    size = fit(sl["jp"], 240, 100)
    parts = [(sl["jp"], font(size), INK, int(size * 1.2)), (sl["reading"], font(72), BRAND, 100),
             (sl["en"], font(80, False), SOFT, 100)]
    y = place(img, card_image(f"Word of the day · {seq.get('level', '')}".rstrip(" ·"), BRAND, parts), SAFE_TOP + 20, warns, "word card")
    ex = sl["example"]; jf = font(58)
    parts = [(t, jf, INK, 76) for t in balanced(ex["jp"], jf, 840)] + [("", None, None, 10)]
    parts += lines_parts([ex.get("reading", "")], 34, (176, 110, 128), 46, False) + [("", None, None, 14)]
    parts += lines_parts([ex["en"]], 42, SOFT, 56, False)
    place(img, card_image("Example", (96, 150, 112), parts, min_h=300), y + 10, warns, "example card")
    footer(img, cfg)
    return img, warns


def slide_quiz(sl, seq, cfg):
    warns, img = [], static_bg(seq.get("scene", "sakura"))
    size = fit(sl["jp"], 200, 100)
    parts = [(sl["jp"], font(size), BRAND, int(size * 1.2))] if sl.get("jp") else []
    parts += lines_parts([sl["question"]], 54, INK, 72) + [("", None, None, 20)]
    parts += [(f"{LETTERS[i]}    {o}", font(58, False), INK, 82) for i, o in enumerate(sl["options"])]
    y = place(img, card_image("Quick quiz", BRAND, parts, min_h=700), SAFE_TOP + 20, warns, "quiz card")
    ImageDraw.Draw(img).text((W / 2, y + 60), "Reply with A, B, C or D - the answer is in the next Story!",
                             font=font(36, False), fill=SOFT, anchor="mm")
    footer(img, cfg)
    return img, warns


def slide_reveal(sl, seq, cfg):
    warns, img = [], static_bg(seq.get("scene", "sakura"))
    size = fit(sl["jp"], 170, 90)
    parts = [(f"{sl['answer_label']} · {sl['en'].capitalize()}", font(84), BRAND, 112),
             (sl["jp"], font(size), INK, int(size * 1.15)), (sl["reading"], font(56), SOFT, 80), ("", None, None, 14)]
    parts += lines_parts(sl.get("note", []), 40, SOFT, 56, False)
    y = place(img, card_image("Answer", (96, 150, 112), parts, min_h=700), SAFE_TOP + 20, warns, "answer card")
    cta = wrap(sl.get("cta") or cfg["cta_default"], font(40), 900)
    d = ImageDraw.Draw(img)
    for i, t in enumerate(cta):
        d.text((W / 2, y + 60 + i * 56), t, font=font(40), fill=BRAND, anchor="mm")
    footer(img, cfg)
    return img, warns


STATIC = {"intro": slide_intro, "word": slide_word, "quiz": slide_quiz, "reveal": slide_reveal}


def save_jpeg(img, path):
    img.convert("RGB").save(path, "JPEG", quality=92, optimize=True, subsampling=0)


# ---------- conversation clip ----------
def render_convo(sl, seq, cfg, out_mp4, poster, dummy):
    """Reuses tinyvideo's characters/scene/voices; no vocab section so the clip stays Story-length."""
    tmp_story = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    tmp_story.write(f"title: {sl.get('title', 'Tiny chat')}\nscene: {sl.get('scene', 'cafe')}\n\n")
    for ln in sl["lines"]:
        tmp_story.write(f"{ln['speaker']}: {ln['jp']} | {ln['en']}" + (f" | {ln['romaji']}" if ln.get("romaji") else "") + "\n")
    tmp_story.close()
    tv.FALLBACK_USED = False
    status = "placeholder_tone" if dummy else "real_voice"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            meta, lines, audio, n, frame = tv.build(tmp_story.name, cfg["voice_rate"], dummy, tmp)
            if tv.FALLBACK_USED:
                status = "fallback_voice"
            wav = os.path.join(tmp, "final.wav"); write_wav(wav, audio)
            l = lines[min(1, len(lines) - 1)]
            frame(int((l["start"] + 0.5) * FPS)).save(poster, "JPEG", quality=90)
            tmp_mp4 = os.path.join(tmp, "clip.mp4")
            p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "warning", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                  "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-threads", "2", "-crf", "20",
                                  "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", "-shortest", tmp_mp4],
                                 stdin=subprocess.PIPE)
            for i in range(n):
                p.stdin.write(frame(i).tobytes())
            p.stdin.close(); p.wait()
            if p.returncode:
                raise RuntimeError(f"ffmpeg failed (exit {p.returncode})")
            shutil.copyfile(tmp_mp4, out_mp4)
    finally:
        os.unlink(tmp_story.name)
    return {"duration": round(n / FPS, 1), "size_mb": round(os.path.getsize(out_mp4) / 1e6, 2), "audio": status,
            "audio_transcript": [l["jp"] for l in sl["lines"]], "subtitles": [{"jp": l["jp"], "en": l["en"]} for l in sl["lines"]]}


# ---------- QC (consistency checks; NOT a language verification) ----------
def hira(t):
    import pykakasi
    return "".join(x["hira"] for x in pykakasi.kakasi().convert(t))


def norm(s):
    s = re.sub(r"[\s\u3000。、！？!?,.「」\u201c\u201d]", "", s)
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


def qc(seq, convo_info, layout_warns, known_words):
    errors, warns, checks = [], list(layout_warns), []
    slides = seq["slides"]
    for t in [s.get("type") for s in slides]:
        if t not in TYPES:
            errors.append(f"unknown slide type: {t}")
    word = next((s for s in slides if s.get("type") == "word"), None)
    quiz = next((s for s in slides if s.get("type") == "quiz"), None)
    reveal = next((s for s in slides if s.get("type") == "reveal"), None)

    def reading_check(label, jp, reading):
        try:
            # pykakasi reads sentence-initial 今日は as こんにちは (greeting); in a normal sentence it is きょうは + particle.
            ok = norm(hira(jp.replace("今日は", "今日 は"))) == norm(reading)
        except Exception as e:
            warns.append(f"{label}: reading check unavailable ({e})"); return
        checks.append({"check": f"reading matches dictionary: {label}", "ok": ok})
        if not ok:
            alt = hira(jp.replace("今日は", "今日 は"))
            warns.append(f"{label}: given reading '{reading}' differs from dictionary reading '{alt}' - verify")

    if word:
        reading_check("target word", word["jp"], word["reading"])
        reading_check("example sentence", word["example"]["jp"], word["example"]["reading"])
        if word["jp"] not in word["example"]["jp"]:
            warns.append("example sentence does not contain the target word in the same form (check conjugation)")
        if word["jp"] in known_words and known_words[word["jp"]] != seq["id"]:
            warns.append(f"duplicate: {word['jp']} already used in sequence '{known_words[word['jp']]}'")
    if quiz:
        n = len(quiz["options"])
        ok = isinstance(quiz.get("answer"), int) and 0 <= quiz["answer"] < n and 3 <= n <= 4 and len({o.lower() for o in quiz["options"]}) == n
        checks.append({"check": "quiz has 3-4 unique options and exactly one valid correct answer", "ok": ok})
        if not ok:
            errors.append("quiz options/answer invalid")
        elif word and quiz["options"][quiz["answer"]].lower() != word["en"].lower():
            errors.append(f"quiz correct option '{quiz['options'][quiz['answer']]}' != word meaning '{word['en']}'")
        else:
            checks.append({"check": "quiz correct option equals the taught meaning", "ok": True})
        if quiz.get("jp") and word and quiz["jp"] != word["jp"]:
            errors.append("quiz asks about a different word than the word slide")
    if reveal and quiz and isinstance(quiz.get("answer"), int):
        ok = reveal["answer_label"] == LETTERS[quiz["answer"]] and reveal["en"].lower() == quiz["options"][quiz["answer"]].lower()
        checks.append({"check": "reveal slide matches the quiz answer", "ok": ok})
        if not ok:
            errors.append("reveal slide does not match the quiz answer")
    if reveal and word:
        ok = reveal["jp"] == word["jp"] and norm(reveal["reading"]) == norm(word["reading"])
        checks.append({"check": "reveal slide repeats the same word and reading", "ok": ok})
        if not ok:
            errors.append("reveal word/reading differs from word slide")
    if convo_info:
        checks.append({"check": "audio transcript == subtitles (both generated from the same text)",
                       "ok": convo_info["audio_transcript"] == [s["jp"] for s in convo_info["subtitles"]]})
        if convo_info["audio"] != "real_voice":
            errors.append(f"conversation audio is {convo_info['audio']} (placeholder or lower-quality fallback voice), not the natural Japanese voice - re-render")
        if convo_info["duration"] > 60 or convo_info["duration"] < 3:
            errors.append(f"clip duration {convo_info['duration']}s outside Story limits (3-60s)")
        elif convo_info["duration"] > 10:
            warns.append(f"clip is {convo_info['duration']}s (target 5-10s)")
        if convo_info["size_mb"] > 8:
            warns.append(f"clip is {convo_info['size_mb']} MB; some sources report an 8 MB Story video limit")
    for i, s in enumerate(slides, 1):
        for k in ("jp", "reading", "en", "question"):
            if k in s and not str(s[k]).strip():
                errors.append(f"slide {i}: empty '{k}'")
    notes = ["Automated checks only prove internal consistency. They cannot prove the Japanese is natural or correct.",
             "Vocabulary/grammar level was NOT machine-checked; compare against your N4 target by eye."]
    approved = bool(seq.get("approved")) and bool(str(seq.get("reviewed_by", "")).strip())
    return {"errors": errors, "warnings": warns, "checks": checks, "uncertain": seq.get("uncertain", []), "notes": notes,
            "japanese_verified": False,
            "status": "blocked" if errors else ("ready" if approved else "needs_review")}


# ---------- main ----------
def render_sequence(path, cfg, args, known_words):
    seq = json.load(open(path, encoding="utf-8"))
    sid = seq["id"]; out = os.path.join(OUT_DIR, sid); os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, "*")):
        os.unlink(f)
    slides_out, layout_warns, convo_info = [], [], None
    for i, sl in enumerate(seq["slides"], 1):
        t = sl["type"]; base = f"{i:02d}-{t}"
        if t == "convo":
            if args.no_video:
                continue
            mp4, poster = os.path.join(out, base + ".mp4"), os.path.join(out, base + "-poster.jpg")
            convo_info = render_convo(sl, seq, cfg, mp4, poster, args.dummy_audio)
            slides_out.append({"n": i, "type": t, "kind": "video", "file": base + ".mp4", "poster": base + "-poster.jpg", **convo_info})
        elif t in STATIC:
            img, w = STATIC[t](sl, seq, cfg)
            save_jpeg(img, os.path.join(out, base + ".jpg"))
            layout_warns += [f"slide {i}: {x}" for x in w]
            slides_out.append({"n": i, "type": t, "kind": "image", "file": base + ".jpg"})
        else:
            slides_out.append({"n": i, "type": t, "kind": "unknown", "file": ""})
        slides_out[-1]["content"] = {k: v for k, v in sl.items() if k != "type"}
    report = qc(seq, convo_info, layout_warns, known_words)
    manifest = {
        "id": sid, "title": seq.get("title", sid), "level": seq.get("level", ""), "approved": bool(seq.get("approved")),
        "reviewed_by": seq.get("reviewed_by", ""), "publish_at": seq.get("publish_at", ""), "timezone": cfg["timezone"],
        "ready_to_publish": report["status"] == "ready", "qc": report, "slides": slides_out,
        "source": f"ig-stories/sequences/{os.path.basename(path)}",
        "api_limits": ["Stories are single-media: each slide is posted as its own Story.",
                       "The Instagram API cannot add stickers (poll, quiz, link, question) or captions to Stories.",
                       "The API has no native scheduling: this project's scheduled workflow publishes at publish_at."],
        "manual_steps": [
            "Optional: post the quiz slide by hand in the Instagram app and add the native Quiz sticker (options from the quiz slide, correct answer set) instead of the text-reply version.",
            "Optional: add a Link sticker to the last Story by hand if you want a tappable link to the free lesson."
        ] if any(s["type"] == "quiz" for s in seq["slides"]) else [],
    }
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return manifest


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["render"])
    ap.add_argument("--sequence", default="all"); ap.add_argument("--dummy-audio", action="store_true")
    ap.add_argument("--no-video", action="store_true")
    args = ap.parse_args(); cfg = load_cfg()
    paths = sorted(glob.glob(os.path.join(SEQ_DIR, "*.json")))
    if args.sequence != "all":
        paths = [p for p in paths if os.path.basename(p) == args.sequence + ".json"]
        if not paths:
            sys.exit(f"No such sequence: {args.sequence}")
    known = {}
    for p in sorted(glob.glob(os.path.join(SEQ_DIR, "*.json"))):
        s = json.load(open(p, encoding="utf-8"))
        for sl in s["slides"]:
            if sl.get("type") == "word":
                known.setdefault(sl["jp"], s["id"])
    os.makedirs(OUT_DIR, exist_ok=True)
    for p in paths:
        m = render_sequence(p, cfg, args, known)
        print(f"{m['id']}: status={m['qc']['status']} errors={len(m['qc']['errors'])} warnings={len(m['qc']['warnings'])}")
        for e in m["qc"]["errors"]:
            print("  ERROR:", e)
        for w in m["qc"]["warnings"]:
            print("  warn:", w)
    index = []
    for mp in sorted(glob.glob(os.path.join(OUT_DIR, "*", "manifest.json"))):
        m = json.load(open(mp, encoding="utf-8"))
        index.append({k: m[k] for k in ("id", "title", "level", "approved", "ready_to_publish", "publish_at")} | {"status": m["qc"]["status"]})
    json.dump(index, open(os.path.join(OUT_DIR, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
