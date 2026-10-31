"""Tiny Japanese Story mode - vertical (1080x1920) Reel renderer: animated story, vocabulary, optional grammar and quiz."""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from .config import *
from .parser import Say, Direction, SceneChange, to_romaji
from .voice import synth, read_wav, write_wav
from .srt import write_srt

from .fonts import font
from . import acting, scenes as SC, rig

def wrap(d, text, f, maxw):
    """Wrap on spaces (English, romaji); Japanese without spaces wraps between characters."""
    if not text: return []
    sep = " " if " " in text else ""
    toks = text.split(" ") if sep else list(text)
    lines, cur = [], ""
    for w in toks:
        t = (cur + sep + w) if cur else w
        if d.textlength(t, font=f) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def block(d, cx, y, text, size, fill, maxw, bold=True, gap=1.2, maxlines=None):
    """Centered wrapped text; shrinks the font to fit maxlines. Returns bottom y."""
    s = size
    while True:
        f = font(s, bold); lines = wrap(d, text, f, maxw)
        if maxlines is None or len(lines) <= maxlines or s <= 28: break
        s -= 4
    for ln in lines:
        d.text((cx, y), ln, font=f, fill=fill, anchor="ma"); y += int(s * gap)
    return y

def stack(d, cx, y, parts, maxh, maxw=900, gap=10):
    """parts: [(text, size, fill, bold, maxlines)] drawn one under the other; everything shrinks together until it fits maxh."""
    k = 1.0
    while True:
        laid, total = [], 0
        for text, size, fill, bold, ml in parts:
            if not text: continue
            s = max(24, int(size * k)); f = font(s, bold)
            while True:
                lines = wrap(d, text, f, maxw)
                if len(lines) <= ml or s <= 24: break
                s -= 3; f = font(s, bold)
            laid.append((lines, f, s, fill)); total += len(lines) * int(s * 1.2) + gap
        if total - gap <= maxh or k <= 0.5: break
        k -= 0.07
    for lines, f, s, fill in laid:
        for ln in lines: d.text((cx, y), ln, font=f, fill=fill, anchor="ma"); y += int(s * 1.2)
        y += gap
    return y

import functools
@functools.lru_cache(maxsize=32)
def _vgrad(top, bot):
    a = np.linspace(0, 1, H)[:, None, None]
    arr = (np.array(top)[None, None, :] * (1 - a) + np.array(bot)[None, None, :] * a)
    return Image.fromarray(np.repeat(arr, W, axis=1).astype("uint8"), "RGB")

def vgrad(top, bot):
    return _vgrad(tuple(top), tuple(bot)).copy()

def pill(d, cx, y, text, fill, fg=(255, 255, 255), size=34):
    f = font(size); w = int(d.textlength(text, font=f)) + 56
    d.rounded_rectangle((cx - w // 2, y, cx + w // 2, y + size + 28), radius=(size + 28) // 2, fill=fill)
    d.text((cx, y + 14), text, font=f, fill=fg, anchor="ma")

def brand_tag(d):
    """Small 'Tiny Japanese' tag above the artwork (compact pill in the top margin, clear of the shop signs)."""
    f = font(38); w = int(d.textlength("Tiny Japanese", font=f)) + 64
    d.rounded_rectangle((W // 2 - w // 2, 128, W // 2 + w // 2, 196), radius=34, fill=(255, 255, 255, 248))
    d.text((W // 2, 162), "Tiny Japanese", font=f, fill=NAVY, anchor="mm")

def wordmark(d, y=SAFE_TOP + 10):
    d.text((W // 2, y), "Tiny Japanese", font=font(56), fill=NAVY, anchor="ma")
    cx, cy = W // 2 + 262, y + 34                       # small sakura blossom
    for k in range(5):
        a = math.radians(-90 + 72 * k); px, py = cx + 20 * math.cos(a), cy + 20 * math.sin(a)
        d.ellipse((px - 13, py - 13, px + 13, py + 13), fill=BLUSH, outline=BRAND)
    d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=(255, 226, 150))

# ---- frames ----
def f_title(seg, t, meta):
    """A cinematic, story-specific opening card; the dialogue/story timeline is unchanged."""
    # Reuse the illustrated location chosen for the first story scene instead of the old pink gradient.
    img = SC.background(seg.get("place") or "street")
    d = ImageDraw.Draw(img, "RGBA")
    # Soft ivory glass panel keeps the title readable while letting the illustrated setting show through.
    panel = (76, 500, W - 76, 1370)
    d.rounded_rectangle(panel, radius=76, fill=(255, 251, 246, 226), outline=(255, 255, 255, 245), width=8)
    d.rounded_rectangle((panel[0] + 16, panel[1] + 16, panel[2] - 16, panel[3] - 16), radius=62,
                        outline=LAVENDER + (235,), width=4)
    wordmark(d, 650)
    y = block(d, W // 2, 830, meta["title"], 78, NAVY, 880, maxlines=4)
    pill(d, W // 2, y + 48, f"Episode {meta.get('episode') or '1'}", BRAND)
    d.text((W // 2, 1270), "A tiny Japanese story · ちいさなものがたり", font=font(38, False), fill=NAVY, anchor="ma")
    return img

def f_story(seg, t, meta):
    img = SC.background(seg["place"]); stage = seg["stage"]; d = ImageDraw.Draw(img, "RGBA"); brand_tag(d)
    pill(d, W // 2, 330, seg["place"].title(), (255, 255, 255, 190), fg=NAVY, size=30)
    poses = {n: stage.pose(n, t) for n in stage.names}
    for n in sorted(stage.names, key=lambda k: poses[k]["lane"]):
        P = poses[n]
        if not P["vis"]: continue
        sp = n == seg.get("speaker")
        spr = rig.draw(n, dict(P, mouth=seg["mouth"](t) if sp else 0.0, t=t))
        sc = SC.scale_of(seg["place"]) * (1.0 + P["lane"] * 0.0009)
        spr = spr.resize((int(spr.width * sc), int(spr.height * sc)), Image.BILINEAR)
        feet = SC.floor_of(seg["place"]) + P["lane"] * 0.55
        d.ellipse((P["x"] - 150 * sc, feet - 16, P["x"] + 150 * sc, feet + 16), fill=(40, 44, 78, 58))   # contact shadow
        img.paste(spr, (int(P["x"] - rig.CX * sc), int(feet - rig.FY * sc)), spr)
    if seg.get("speaker"):
        d = ImageDraw.Draw(img, "RGBA")
        d.rounded_rectangle((60, 1240, W - 60, SAFE_BOTTOM + 20), radius=48, fill=(255, 255, 255, 235))
        pill(d, W // 2, 1210, seg["speaker"], CHARS[seg["speaker"]]["accent"], size=32)
        stack(d, W // 2, 1292, [(seg["jp"], 58, NAVY, True, 2), (seg.get("romaji", ""), 32, ROMA, False, 2), (seg["en"], 38, MUTED, False, 2)], maxh=SAFE_BOTTOM + 8 - 1292)
    return img

def card_frame(tag, tag_color):
    img = vgrad(CREAM, (240, 232, 252)); d = ImageDraw.Draw(img); wordmark(d)
    d.rounded_rectangle((60, 380, W - 60, SAFE_BOTTOM), radius=56, fill=(255, 255, 255)); pill(d, W // 2, 350, tag, tag_color)
    return img, d

def f_vocab(seg, t, meta):
    img, d = card_frame("Vocabulary · たんご", (120, 150, 220))
    y = block(d, W // 2, 470, seg["term"], 104, NAVY, 880, maxlines=2)
    if seg.get("romaji"): y = block(d, W // 2, y + 6, seg["romaji"], 52, ROMA, 880, bold=False, maxlines=2)
    y = block(d, W // 2, y + 24, "means", 42, MUTED, 880, bold=False)
    y = block(d, W // 2, y + 4, seg["meaning"], 74, (74, 112, 200), 880, maxlines=2)
    if seg["example"]:
        jp, en = seg["example"]
        d.line((200, y + 50, W - 200, y + 50), fill=(225, 220, 240), width=4)
        y = block(d, W // 2, y + 80, jp, 46, NAVY, 860, maxlines=2)
        rm = to_romaji(jp)
        if rm: y = block(d, W // 2, y + 2, rm, 30, ROMA, 860, bold=False, maxlines=2)
        if en: block(d, W // 2, y + 8, en, 36, MUTED, 860, bold=False, maxlines=2)
    return img

def f_grammar(seg, t, meta):
    img, d = card_frame("Grammar · ぶんぽう", (92, 168, 120))
    y = block(d, W // 2, 520, seg["pattern"], 84, NAVY, 880, maxlines=2)
    y = block(d, W // 2, y + 20, seg["meaning"], 50, (92, 168, 120), 880, maxlines=2)
    d.line((200, y + 50, W - 200, y + 50), fill=(225, 240, 228), width=4); y += 90
    for fr, en in seg["examples"][:2]:
        y = block(d, W // 2, y, fr, 46, NAVY, 860, maxlines=2)
        if en: y = block(d, W // 2, y + 4, en, 34, MUTED, 860, bold=False, maxlines=2)
        y += 40
    return img

def f_quiz(seg, t, meta):
    img, d = card_frame("Quiz", (240, 150, 100)); q = seg["quiz"]
    y = block(d, W // 2, 480, q.question, 54, NAVY, 880, maxlines=4) + 30
    for L, txt in sorted(q.options.items()):
        win = seg["reveal"] and L == q.answer
        col = (150, 205, 165) if win else ((244, 240, 250) if not seg["reveal"] else (250, 246, 252))
        d.rounded_rectangle((100, y, W - 100, y + 120), radius=36, fill=col)
        d.text((150, y + 60), L, font=font(54), fill=NAVY, anchor="lm")
        d.text((230, y + 60), txt, font=font(42 if len(txt) < 34 else 34, False), fill=NAVY if not seg["reveal"] or win else (150, 150, 170), anchor="lm")
        y += 150
    if seg["reveal"]:
        block(d, W // 2, y + 20, q.explanation, 38, MUTED, 860, bold=False, maxlines=4)
    else:
        frac = max(0.0, min(1.0, (t - seg["t0"] - seg["think_from"]) / max(0.1, seg["t1"] - seg["t0"] - seg["think_from"])))
        d.rounded_rectangle((140, y + 30, W - 140, y + 54), radius=12, fill=(235, 230, 245))
        d.rounded_rectangle((140, y + 30, 140 + int((W - 280) * (1 - frac)), y + 54), radius=12, fill=(240, 150, 100))
    return img

def f_outro(seg, t, meta):
    img = vgrad(BLUSH, LAVENDER); d = ImageDraw.Draw(img); wordmark(d, 700)
    block(d, W // 2, 860, "また明日！ See you tomorrow!", 60, NAVY, 880, maxlines=2)
    d.text((W // 2, SAFE_BOTTOM - 130), "Japanese, one tiny story at a time.", font=font(38, False), fill=NAVY, anchor="ma")
    return img

DRAW = {"title": f_title, "story": f_story, "vocab": f_vocab, "grammar": f_grammar, "quiz": f_quiz, "outro": f_outro}

# ---- timeline ----
def envelope(x):
    n = int(SR / FPS); m = len(x) // n
    e = np.sqrt(np.mean(x[:m * n].reshape(m, n) ** 2, axis=1)) if m else np.zeros(1)
    return e

def build(script, tmp, dummy=False, sections=("story", "vocab", "grammar", "quiz"), max_quiz=1):
    cast_names = acting.cast_of(script)[0]
    if len(cast_names) == 1: cast_names.append("Alex" if cast_names[0] != "Alex" else "Mika")
    segs, mix, cues, skipped = [], [], [], 0
    cnt = [0]
    def speak(text, voice, rate=None, who=None):
        cnt[0] += 1; p = os.path.join(tmp, f"a{cnt[0]:03}.wav")
        synth(text, voice, p, dummy, rate, CHARS[who].get("pitch") if who else None); return read_wav(p)
    def place(t0, x): mix.append((t0, x))
    t = 0.0
    segs.append(dict(kind="title", t0=0, t1=2.6, place=SC.scene_for(script) or "street")); t = 2.6
    stage = None
    if "story" in sections:
        voices = {}
        for ev in script.story:
            if isinstance(ev, Say): voices[id(ev)] = speak(ev.jp, CHARS[ev.speaker]["voice"], who=ev.speaker)
        stage, items, tend = acting.play(script, lambda ev: len(voices[id(ev)]) / SR, t0=t)
        for it in items:
            if it[0] == "act":
                segs.append(dict(kind="story", t0=it[1], t1=it[2], place=it[3], speaker=None, stage=stage))
            elif it[0] == "say":
                ev = it[3]; x = voices[id(ev)]; dur = len(x) / SR; env = envelope(x)
                def mouth(tt, env=env, t0=it[1] + 0.15):
                    i = int((tt - t0) * FPS); return float(min(1.0, env[i] * 7)) if 0 <= i < len(env) else 0.0
                segs.append(dict(kind="story", t0=it[1], t1=it[2], speaker=ev.speaker, jp=ev.jp, romaji=ev.romaji, en=ev.en, place=it[4], mouth=mouth, stage=stage))
                place(it[1] + 0.15, x); cues.append((it[1] + 0.15, it[1] + 0.15 + dur + 0.25, ev.jp, ev.en))
        t = tend
    if "vocab" in sections:
        A, B = cast_names[0], cast_names[1]
        for v in script.vocab:
            # Japanese word -> English "means ..." -> Japanese word again, slowly (the viewer hears AND sees the meaning)
            x = speak(v.term, CHARS[A]["voice"], who=A); parts = [(0.3, x)]; d = 0.3 + len(x) / SR + 0.45
            m = speak("means " + v.meaning, EN_VOICE, "+0%"); parts.append((d, m)); d += len(m) / SR + 0.45
            x2 = speak(v.term, CHARS[A]["voice"], "-30%", who=A); parts.append((d, x2)); d += len(x2) / SR + 0.6
            ex = v.examples[0] if v.examples else None
            if ex:
                y = speak(ex[0], CHARS[B]["voice"], who=B); parts.append((d, y)); d += len(y) / SR + 0.8
            for off, a_ in parts: place(t + off, a_)
            segs.append(dict(kind="vocab", t0=t, t1=t + max(d, 3.2), term=v.term, romaji=v.romaji, meaning=v.meaning, example=ex))
            cues.append((t + 0.3, t + 0.3 + len(x) / SR + 0.2, v.term, v.meaning)); t += max(d, 3.2)
    if "grammar" in sections:
        for g in script.grammar:
            d = 0.6; parts = []
            for i, (fr, en) in enumerate(g.examples[:2]):
                a = speak(fr, CHARS[cast_names[i % 2]]["voice"], who=cast_names[i % 2]); parts.append((d, a)); d += len(a) / SR + 0.9
            for off, a in parts: place(t + off, a)
            segs.append(dict(kind="grammar", t0=t, t1=t + max(d + 1.2, 6.0), pattern=g.pattern, meaning=g.meaning, examples=g.examples)); t += max(d + 1.2, 6.0)
    if "quiz" in sections:
        for q in script.quiz[:max_quiz]:
            a = speak(q.question, NARRATOR_VOICE); d1 = 0.4 + len(a) / SR + 0.5; place(t + 0.4, a)
            segs.append(dict(kind="quiz", t0=t, t1=t + d1 + 4.0, quiz=q, reveal=False, think_from=d1)); t += d1 + 4.0
            b = speak(f"The answer is {q.answer}. {q.explanation}", NARRATOR_VOICE); d2 = 0.3 + len(b) / SR + 1.0; place(t + 0.3, b)
            segs.append(dict(kind="quiz", t0=t, t1=t + d2, quiz=q, reveal=True, think_from=0)); t += d2
    segs.append(dict(kind="outro", t0=t, t1=t + 2.4)); t += 2.4
    return segs, mix, cues, skipped, t

def render(script, outdir, stem, dummy=False, preview=None, sections=("story", "vocab", "grammar", "quiz"), max_quiz=1, no_video=False):
    os.makedirs(outdir, exist_ok=True)
    tmp = os.path.join(outdir, ".tmp"); os.makedirs(tmp, exist_ok=True)
    segs, mix, cues, skipped, total = build(script, tmp, dummy, sections, max_quiz)
    audio = np.zeros(int(total * SR) + SR, dtype=np.float32)
    for t0, x in mix:
        i = int(t0 * SR); audio[i:i + len(x)] += x[:len(audio) - i]
    wav = os.path.join(tmp, "mix.wav"); write_wav(wav, np.clip(audio, -1, 1))
    write_srt(os.path.join(outdir, stem + ".srt"), cues)
    last = [None, None]
    STATIC = ("title", "vocab", "grammar", "outro")
    def frame(t):
        for s in segs:
            if s["t0"] <= t < s["t1"]:
                if s["kind"] in STATIC or (s["kind"] == "quiz" and s["reveal"]):
                    if last[0] is not s: last[0] = s; last[1] = DRAW[s["kind"]](s, t, script.meta)
                    return last[1]
                return DRAW[s["kind"]](s, t, script.meta)
        return frame(segs[-1]["t0"])
    if preview:
        os.makedirs(preview, exist_ok=True)
        for i, s in enumerate(segs):
            frame((s["t0"] + s["t1"]) / 2 + 0.05).save(os.path.join(preview, f"{i:02}-{s['kind']}.png"))
    if no_video: return dict(title=script.meta["title"], seconds=round(total, 2), segments=len(segs))
    mp4 = os.path.join(outdir, stem + ".mp4"); n = int(total * FPS)
    X264 = (["-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency", "-crf", "20", "-threads", "1"] if os.environ.get("TF_LOWMEM") == "1"
            else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21"])
    logf = open(os.path.join(tmp, "ffmpeg.log"), "w")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "warning", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", wav, *X264, "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
                          "-shortest", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE, stderr=logf)
    try:
        for i in range(n):
            p.stdin.write(frame(i / FPS).tobytes())
        p.stdin.close()
    except BrokenPipeError:
        p.wait(); sys.exit("ERROR: ffmpeg stopped early (rc=%s):\n%s" % (p.returncode, open(os.path.join(tmp, "ffmpeg.log")).read()[-1500:]))
    if p.wait() != 0: sys.exit("ERROR: ffmpeg failed:\n" + open(os.path.join(tmp, "ffmpeg.log")).read()[-1500:])
    info = dict(title=script.meta["title"], width=W, height=H, fps=FPS, seconds=round(total, 2), sections=list(sections), directions_not_animated=skipped)
    json.dump(info, open(os.path.join(outdir, stem + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return info
