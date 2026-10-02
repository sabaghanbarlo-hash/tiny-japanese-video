#!/usr/bin/env python3
"""Tiny Japanese video generator: story script (.txt) -> 1080x1920 MP4.

Free stack: edge-tts (Japanese neural voices), Pillow (drawn characters + subtitles),
ffmpeg (encode). Runs on GitHub Actions, nothing to install locally.
"""
import argparse, asyncio, functools, glob, math, os, random, re, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, SR = 1080, 1920, 30, 24000
CHAR_SCALE, CHAR_Y = 0.9, 300
TABLE_TOP, CARD_Y = 885, 1040

CHARS = {
    "Mika": dict(voice="ja-JP-NanamiNeural", hair=(74, 45, 38), skin=(255, 224, 205), top=(244, 168, 184),
                 accent=(222, 110, 134), long_hair=True, x=16),
    "Alex": dict(voice="ja-JP-KeitaNeural", hair=(139, 98, 64), skin=(250, 214, 190), top=(142, 178, 150),
                 accent=(96, 150, 112), long_hair=False, x=W - 16 - int(560 * CHAR_SCALE)),
}
SCENES = {
    "cafe": dict(top=(255, 246, 232), bot=(250, 228, 210), floor=(204, 160, 120), table=(228, 184, 140), edge=(176, 130, 92)),
    "station": dict(top=(196, 224, 246), bot=(236, 246, 252), floor=(150, 150, 164), table=(238, 204, 96), edge=(120, 120, 134)),
    "sakura": dict(top=(255, 228, 236), bot=(255, 246, 242), floor=(160, 204, 148), table=(176, 218, 156), edge=(120, 170, 108)),
}
BRAND = (222, 110, 134)


# ---------- fonts / text ----------
@functools.lru_cache(None)
def font(size, bold=True):
    w = "Bold" if bold else "Regular"
    for pat in (f"/usr/share/fonts/**/NotoSansCJK-{w}.ttc", f"/usr/share/fonts/**/NotoSansCJKjp-{w}.otf",
                "/usr/share/fonts/**/NotoSansCJK*.ttc", "/usr/share/fonts/**/*CJK*.tt*", "/usr/share/fonts/**/DejaVuSans.ttf"):
        g = sorted(glob.glob(pat, recursive=True))
        if g:
            try:
                return ImageFont.truetype(g[0], size)
            except Exception:
                pass
    return ImageFont.load_default()


def wrap(text, f, maxw):
    if not text:
        return []
    sep = " " if " " in text else ""
    toks = text.split(" ") if sep else list(text)
    out, cur = [], ""
    for t in toks:
        trial = cur + sep + t if cur else t
        if f.getlength(trial) > maxw and cur:
            out.append(cur)
            cur = t
        else:
            cur = trial
    out.append(cur)
    return out


def to_romaji(t):
    try:
        import pykakasi
        r = pykakasi.kakasi().convert(t)
        s = " ".join(x["hepburn"] for x in r if x["hepburn"].strip())
        s = re.sub(r"\s+([!?,.。！？、])", r"\1", s)
        return s[:1].upper() + s[1:]
    except Exception:
        return ""


# ---------- script parsing ----------
def parse_story(path):
    meta, lines, vocab = {"title": "Tiny Story", "scene": "cafe", "episode": ""}, [], []
    for raw in open(path, encoding="utf-8"):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^(title|scene|episode)\s*:\s*(.+)$", s, re.I)
        if m:
            meta[m[1].lower()] = m[2].strip()
            continue
        m = re.match(r"^vocab\s*:\s*(.+)$", s, re.I)
        if m:
            p = [x.strip() for x in m[1].split("|")]
            if len(p) == 2:
                p = [p[0], to_romaji(p[0]), p[1]]
            if len(p) == 3:
                vocab.append(dict(jp=p[0], romaji=p[1], en=p[2]))
            continue
        m = re.match(r"^([A-Za-z]+)\s*[:：]\s*(.+)$", s)
        if m and m[1].capitalize() in CHARS:
            p = [x.strip() for x in m[2].split("|")]
            lines.append(dict(speaker=m[1].capitalize(), jp=p[0], en=p[1] if len(p) > 1 else "",
                              romaji=p[2] if len(p) > 2 else to_romaji(p[0])))
            continue
        sys.exit(f"Cannot parse line (speakers must be {', '.join(CHARS)}): {s}")
    if not lines:
        sys.exit("No dialogue lines found.")
    return meta, lines, vocab


# ---------- audio ----------
def write_wav(path, x):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())


def read_wav(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def sh(cmd):
    subprocess.run(cmd, check=True)


def synth(text, speaker, out_wav, rate, dummy=False):
    if dummy:
        n = int(max(1.0, len(text) * 0.11) * SR); t = np.arange(n) / SR
        write_wav(out_wav, 0.4 * np.sin(2 * np.pi * 220 * t) * np.abs(np.sin(2 * np.pi * 3.5 * t)) ** 0.7)
        return
    mp3, af = out_wav + ".mp3", []
    try:
        import edge_tts
        asyncio.run(edge_tts.Communicate(text, CHARS[speaker]["voice"], rate=rate).save(mp3))
    except Exception as e:
        print(f"edge-tts failed ({e}); falling back to gTTS", file=sys.stderr)
        from gtts import gTTS
        gTTS(text, lang="ja").save(mp3)
        if speaker == "Alex":
            af = ["-af", f"asetrate={int(SR * 0.86)},aresample={SR}"]
    sh(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, *af, "-ar", str(SR), "-ac", "1", out_wav])


def mouth_levels(audio, n):
    spf = SR / FPS
    rms = np.array([np.sqrt(np.mean(audio[int(i * spf):int((i + 1) * spf)] ** 2) + 1e-12)
                    if int(i * spf) < len(audio) else 0 for i in range(n)])
    ref = np.percentile(rms[rms > 1e-3], 90) if (rms > 1e-3).any() else 1
    lv = np.clip(rms / ref, 0, 1.2)
    sm = lv.copy(); sm[1:-1] = 0.5 * lv[1:-1] + 0.25 * (lv[:-2] + lv[2:])
    return np.where(sm < 0.15, 0, np.where(sm < 0.55, 1, 2))


# ---------- characters ----------
@functools.lru_cache(None)
def sprite(name, mouth, blink):
    c, S = CHARS[name], 2 * CHAR_SCALE
    w, h = int(560 * S), int(760 * S)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda *v: [int(x * S) for x in v]
    ell = lambda box, fill: d.ellipse(P(*box), fill=fill)
    ink, hair, skin, top, acc = (70, 45, 48), c["hair"], c["skin"], c["top"], c["accent"]
    if c["long_hair"]:
        d.rounded_rectangle(P(110, 170, 450, 590), radius=int(110 * S), fill=hair)
    d.rounded_rectangle(P(185, 450, 375, 690), radius=int(60 * S), fill=top)           # body
    d.polygon(P(245, 452, 280, 505, 315, 452), fill=skin)                              # neckline
    ell((140, 500, 210, 650), top); ell((350, 500, 420, 650), top)                     # arms
    ell((148, 625, 205, 675), skin); ell((355, 625, 412, 675), skin)                   # hands
    ell((125, 145, 435, 455), skin)                                                    # head
    d.pieslice(P(118, 136, 442, 460), 180, 360, fill=hair)                             # hair cap
    if c["long_hair"]:
        for x in range(150, 420, 48):
            ell((x - 34, 225, x + 34, 300 + (12 if (x // 48) % 2 else 0)), hair)
        ell((112, 280, 168, 520), hair); ell((392, 280, 448, 520), hair)
        ell((340, 165, 392, 215), acc); ell((355, 180, 377, 200), (255, 240, 200))     # hair flower
    else:
        for x in range(135, 420, 58):
            d.polygon(P(x, 225, x + 58, 225, x + 29, 305), fill=hair)
        d.polygon(P(262, 120, 300, 120, 282, 165), fill=hair)
    for ex in (222, 338):                                                              # eyes
        if blink:
            d.arc(P(ex - 26, 335, ex + 26, 375), 200, 340, fill=ink, width=int(6 * S))
        else:
            ell((ex - 24, 318, ex + 24, 382), (55, 35, 42))
            ell((ex - 15, 330, ex + 3, 350), (255, 255, 255)); ell((ex + 6, 358, ex + 16, 368), (255, 255, 255))
    ell((168, 388, 215, 412), (250, 172, 170)); ell((345, 388, 392, 412), (250, 172, 170))  # blush
    if mouth == 0:
        d.arc(P(262, 400, 298, 430), 20, 160, fill=ink, width=int(5 * S))
    elif mouth == 1:
        ell((268, 408, 292, 430), (120, 40, 52))
    else:
        ell((258, 405, 302, 442), (120, 40, 52)); ell((266, 424, 294, 440), (236, 120, 132))
    return im.resize((int(560 * CHAR_SCALE), int(760 * CHAR_SCALE)), Image.LANCZOS)


def pill(text, fill, fg=(255, 255, 255)):
    f = font(32); tw = int(f.getlength(text)) + 56
    im = Image.new("RGBA", (tw, 58), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, tw - 1, 57), radius=29, fill=fill)
    d.text((tw / 2, 29), text, font=f, fill=fg, anchor="mm")
    return im


# ---------- scenes ----------
def vgrad(w, h, a, b):
    arr = np.zeros((h, w, 3), np.uint8)
    for i in range(3):
        arr[:, :, i] = np.linspace(a[i], b[i], h)[:, None]
    return Image.fromarray(arr).convert("RGBA")


def blossoms(d, rng, box, n):
    cols = ((255, 200, 214), (255, 214, 224), (250, 184, 202))
    for _ in range(n):
        x, y, r = rng.randint(box[0], box[2]), rng.randint(box[1], box[3]), rng.randint(8, 18)
        d.ellipse((x - r, y - r, x + r, y + r), fill=rng.choice(cols))


def make_scene(scene, meta):
    sc = SCENES.get(scene, SCENES["cafe"]); rng = random.Random(7)
    bg = vgrad(W, H, sc["top"], sc["bot"]); d = ImageDraw.Draw(bg)
    if scene == "station":
        for x in range(-40, W, 150):
            hh = rng.randint(180, 380); d.rectangle((x, TABLE_TOP - hh, x + 130, TABLE_TOP), fill=(206, 218, 234))
        d.rounded_rectangle((330, 290, 750, 400), radius=24, fill=(60, 80, 120))
        d.text((540, 345), "えき  Station", font=font(52), fill="white", anchor="mm")
    elif scene == "sakura":
        d.line([(0, 330), (300, 280), (600, 340), (1080, 240)], fill=(122, 84, 72), width=20)
        blossoms(d, rng, (0, 170, W, 520), 150)
        blossoms(d, rng, (0, 520, W, 880), 40)
    else:
        d.rounded_rectangle((290, 280, 790, 730), radius=36, fill=(255, 255, 255))
        d.rounded_rectangle((310, 300, 770, 710), radius=26, fill=(205, 232, 244))
        d.line([(540, 300), (540, 710)], fill=(255, 255, 255), width=10); d.line([(310, 505), (770, 505)], fill=(255, 255, 255), width=10)
        blossoms(d, rng, (330, 320, 750, 480), 22)
        for x in (110, 970):
            d.line([(x, 0), (x, 190)], fill=(120, 90, 80), width=6)
            d.pieslice((x - 62, 170, x + 62, 300), 180, 360, fill=(240, 170, 120))
    d.rectangle((0, TABLE_TOP, W, H), fill=sc["floor"])
    for y in range(TABLE_TOP + 140, H, 96):
        d.line([(0, y), (W, y)], fill=tuple(int(v * 0.93) for v in sc["floor"]), width=3)
    ep = f"Ep.{meta['episode']}  ·  " if meta.get("episode") else ""
    d.rounded_rectangle((60, 118, 1020, 252), radius=54, fill=(255, 255, 255, 238))
    d.text((100, 142), "TINY JAPANESE", font=font(30), fill=BRAND)
    size = 48
    while size > 28 and font(size).getlength(ep + meta["title"]) > 880:
        size -= 2
    d.text((100, 184), ep + meta["title"], font=font(size), fill=(60, 45, 48))
    fg = Image.new("RGBA", (W, 175), (0, 0, 0, 0)); g = ImageDraw.Draw(fg)
    g.rectangle((0, 55, W, 125), fill=sc["table"]); g.rectangle((0, 125, W, 175), fill=sc["edge"])
    if scene not in SCENES or scene == "cafe":
        for x in (180, 820):
            g.rounded_rectangle((x, 8, x + 84, 62), radius=14, fill=(255, 255, 255)); g.ellipse((x + 70, 20, x + 110, 50), outline=(255, 255, 255), width=8)
    return bg, fg


# ---------- cards ----------
def card_image(tag, tag_color, parts, min_h=380):
    body = sum(p[3] for p in parts); h = max(min_h, body + 150); cw = 960
    size = (cw + 80, h + 80)
    m = Image.new("L", size, 0); ImageDraw.Draw(m).rounded_rectangle((40, 52, 40 + cw, 52 + h), radius=56, fill=90)
    sh_ = Image.new("RGBA", size, (120, 80, 70, 0)); sh_.putalpha(m.filter(ImageFilter.GaussianBlur(16)))
    d_img = Image.new("RGBA", size, (0, 0, 0, 0)); d_img = Image.alpha_composite(d_img, sh_)
    d = ImageDraw.Draw(d_img); d.rounded_rectangle((40, 40, 40 + cw, 40 + h), radius=56, fill=(255, 253, 250, 245))
    y = 40 + 56 + (h - 56 - 36 - body) / 2
    for text, f, color, adv in parts:
        if f:
            d.text((40 + cw / 2, y), text, font=f, fill=color, anchor="ma")
        y += adv
    p = pill(tag, tag_color); d_img.paste(p, (84, 14), p)
    return d_img


def balanced(text, f, maxw):
    lines = wrap(text, f, maxw)
    if len(lines) == 2 and " " not in text:
        n, best = len(text), None
        for i in range(n // 3, 2 * n // 3 + 1):
            if text[i] in "。、！？，.!?" or text[i - 1] in "（「":
                continue
            sc = abs(f.getlength(text[:i]) - f.getlength(text[i:]))
            if f.getlength(text[:i]) <= maxw and f.getlength(text[i:]) <= maxw and (best is None or sc < best[0]):
                best = (sc, i)
        if best:
            return [text[:best[1]], text[best[1]:]]
    return lines


def line_card(ln):
    maxw = 840
    jp = next((font(s) for s in (62, 56, 50) if font(s).getlength(ln["jp"]) <= maxw), font(56))
    ro, en = font(36, False), font(40, False)
    parts = [(t, jp, (52, 40, 44), 82) for t in balanced(ln["jp"], jp, maxw)] + [("", None, None, 14)]
    parts += [(t, ro, (176, 110, 128), 49) for t in wrap(ln["romaji"], ro, maxw)] + [("", None, None, 18)]
    parts += [(t, en, (90, 78, 80), 54) for t in wrap(ln["en"], en, maxw)]
    return card_image(ln["speaker"], CHARS[ln["speaker"]]["accent"], parts)


def vocab_card(vocab):
    parts = []
    for v in vocab[:5]:
        parts.append((v["jp"], font(50), (52, 40, 44), 64))
        parts.append((f'{v["romaji"]}  –  {v["en"]}', font(31, False), (120, 98, 104), 58))
    return card_image("Today's tiny words", BRAND, parts, min_h=420)


# ---------- main ----------
def build(story, rate, dummy, tmp):
    meta, lines, vocab = parse_story(story)
    chunks, t = [np.zeros(int(0.6 * SR), np.float32)], 0.6
    for i, ln in enumerate(lines):
        wav = os.path.join(tmp, f"l{i}.wav"); synth(ln["jp"], ln["speaker"], wav, rate, dummy)
        x = read_wav(wav); ln["start"], ln["end"] = t, t + len(x) / SR
        chunks += [x, np.zeros(int(0.5 * SR), np.float32)]; t = ln["end"] + 0.5
    vstart, total = t, t + (5.0 if vocab else 1.2)
    chunks.append(np.zeros(int((total - t) * SR) + SR, np.float32))
    audio = np.concatenate(chunks); audio = audio / max(0.01, np.abs(audio).max()) * 0.9
    n = int(total * FPS); mouth = mouth_levels(audio, n)
    bg, fg = make_scene(meta["scene"].lower(), meta)
    cards = [line_card(l) for l in lines]; vcard = vocab_card(vocab) if vocab else None
    pills = {(nm, a): pill(nm, CHARS[nm]["accent"] if a else (226, 214, 206), (255, 255, 255) if a else (130, 112, 108))
             for nm in CHARS for a in (0, 1)}

    def frame(i):
        tt = i / FPS; fr = bg.copy()
        cur = next((k for k, l in enumerate(lines) if l["start"] - 0.02 <= tt <= l["end"] + 0.1), None)
        for nm, c in CHARS.items():
            sp = cur is not None and lines[cur]["speaker"] == nm
            bob = 6 * abs(math.sin(tt * 7)) if sp and mouth[i] else 2 * math.sin(tt * 2 + (0 if nm == "Mika" else 1.7))
            blink = ((i + (0 if nm == "Mika" else 41)) % 97) < 4
            s = sprite(nm, int(mouth[i]) if sp else 0, blink)
            fr.paste(s, (c["x"], int(CHAR_Y - bob)), s)
            p = pills[(nm, int(sp))]; fr.paste(p, (c["x"] + s.width // 2 - p.width // 2, 330), p)
        fr.paste(fg, (0, TABLE_TOP - 55), fg)
        card, t0 = None, 0
        if tt >= vstart and vcard:
            card, t0 = vcard, vstart
        else:
            k = max((k for k, l in enumerate(lines) if tt >= l["start"] - 0.02), default=None)
            if k is not None:
                card, t0 = cards[k], lines[k]["start"]
        if card:
            f = min(1, (tt - t0) / 0.2); dy = int(24 * (1 - f))
            if f < 1:
                card = card.copy(); card.putalpha(card.getchannel("A").point(lambda v: int(v * f)))
            fr.paste(card, (20, CARD_Y - 40 + dy), card)
        return fr.convert("RGB")

    return meta, lines, audio, n, frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story"); ap.add_argument("-o", "--out", default="output/video.mp4")
    ap.add_argument("--rate", default="-12%", help="speech speed, e.g. -12%% (slower) or +0%%")
    ap.add_argument("--dummy-audio", action="store_true", help="skip TTS (for testing)")
    ap.add_argument("--preview", help="save one PNG frame and exit")
    a = ap.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        meta, lines, audio, n, frame = build(a.story, a.rate, a.dummy_audio, tmp)
        if a.preview:
            l = lines[min(1, len(lines) - 1)]; frame(int((l["start"] + 0.5) * FPS)).save(a.preview); return
        wav = os.path.join(tmp, "final.wav"); write_wav(wav, audio)
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                              "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", a.out],
                             stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(frame(i).tobytes())
        p.stdin.close(); p.wait()
        print(f"Wrote {a.out} ({n / FPS:.1f}s)")


if __name__ == "__main__":
    main()
