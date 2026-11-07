"""Practice-style reel generator (side generator, does not touch the original tinyvideo.py system).

Format (~20 s): big hook -> 3 short lines -> "Your turn! Say it out loud!" with a 3-2-1 countdown ->
Mika says the key phrase -> "Save this / send it to a study buddy". No vocab recap.

Usage:  python practice_reel.py practice/01-introduce-yourself.txt -o output/practice/01.mp4
Story files use the same format as stories/*.txt; the FIRST `vocab:` line is the practice phrase.
"""
import argparse, math, os, re, subprocess, tempfile
import numpy as np
from PIL import Image, ImageDraw
import tinyvideo as tv

W, H, FPS, SR = tv.W, tv.H, tv.FPS, tv.SR
HOOK = 2.0


def silence(sec):
    return np.zeros(int(sec * SR), np.float32)


def ring(n, f):
    s = 260; im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((6, 6, s - 6, s - 6), fill=(255, 253, 250, 240))
    d.arc((14, 14, s - 14, s - 14), -90, -90 + 360 * f, fill=tv.BRAND, width=22)
    d.text((s / 2, s / 2 + 4), str(n), font=tv.font(130), fill=tv.BRAND, anchor="mm")
    return im


def build(story, rate, dummy, tmp):
    meta, lines, vocab = tv.parse_story(story)
    key = vocab[0]
    chunks, t = [silence(0.15)], 0.15
    for i, ln in enumerate(lines):
        wav = os.path.join(tmp, f"l{i}.wav"); tv.synth(ln["jp"], ln["speaker"], wav, rate, dummy)
        x = tv.read_wav(wav); ln["start"], ln["end"] = t, t + len(x) / SR
        chunks += [x, silence(0.25)]; t = ln["end"] + 0.25
    talk = list(lines)
    wav = os.path.join(tmp, "turn.wav"); tv.synth("Your turn! Say it out loud!", "Narrator", wav, "+5%", dummy, voice="en-US-AriaNeural", lang="en")
    x = tv.read_wav(wav); turn0 = t; chunks += [x, silence(0.3)]; t += len(x) / SR + 0.3
    cd0 = t; chunks.append(silence(3.0)); t += 3.0
    wav = os.path.join(tmp, "key.wav"); tv.synth(re.sub(r"[〜~]+", "、", key["jp"]).strip("、 "), "Mika", wav, "-20%", dummy)
    x = tv.read_wav(wav); key0 = t; talk.append(dict(speaker="Mika", start=t, end=t + len(x) / SR)); chunks += [x, silence(0.3)]; t += len(x) / SR + 0.3
    wav = os.path.join(tmp, "end.wav"); tv.synth("Perfect! Save this, and send it to a study buddy.", "Narrator", wav, "+5%", dummy, voice="en-US-AriaNeural", lang="en")
    x = tv.read_wav(wav); end0 = t; chunks += [x, silence(0.6)]; t += len(x) / SR + 0.6
    total = t
    audio = np.concatenate(chunks); audio = audio / max(0.01, np.abs(audio).max()) * 0.9
    n = int(total * FPS); mouth = tv.mouth_levels(audio, n)
    meta["scene"] = tv.pick_scene(meta, lines)
    bg, fg = tv.make_scene(meta["scene"], meta)
    wx = tv.pick_weather(meta, lines, meta["scene"]); wxp = tv.make_weather(wx, meta["scene"]) if wx else None
    cards = [tv.line_card(l) for l in lines]
    pt = [(key["jp"], tv.font(76), (52, 40, 44), 100), (key["romaji"], tv.font(44, False), (176, 110, 128), 62), (key["en"], tv.font(46, False), (90, 78, 80), 64)]
    turn_card = tv.card_image("Your turn!", tv.BRAND, pt, min_h=420)
    done_card = tv.card_image("Perfect!", (79, 154, 110), pt, min_h=420)
    cta_card = tv.card_image("Tiny Japanese", tv.BRAND, [("Save this for later", tv.font(60), (52, 40, 44), 90), ("Send it to a study buddy", tv.font(44, False), (120, 98, 104), 70)], min_h=380)
    banner = tv.hook_banner(meta, "Tiny Japanese")
    pills = {(nm, a): tv.pill(tv.CHARS[nm]["label"], tv.CHARS[nm]["accent"] if a else (226, 214, 206), (255, 255, 255) if a else (130, 112, 108)) for nm in tv.CHARS for a in (0, 1)}

    def frame(i):
        tt = i / FPS; fr = bg.copy()
        if wx: fr.alpha_composite(tv.wx_layer(wx, wxp, tt, False), (0, tv.WX_Y0))
        cur = next((k for k, l in enumerate(talk) if l["start"] - 0.02 <= tt <= l["end"] + 0.1), None)
        for nm, c in tv.CHARS.items():
            sp = cur is not None and talk[cur]["speaker"] == nm
            bob = 6 * abs(math.sin(tt * 7)) if sp and mouth[i] else 2 * math.sin(tt * 2 + (0 if nm == "Mika" else 1.7))
            blink = ((i + (0 if nm == "Mika" else 41)) % 97) < 4
            s = tv.sprite(nm, int(mouth[i]) if sp else 0, blink)
            fr.paste(s, (c["x"], int(tv.CHAR_Y - bob)), s)
            p = pills[(nm, int(sp))]; fr.paste(p, (c["x"] + s.width // 2 - p.width // 2, 330), p)
        fr.paste(fg, (0, tv.TABLE_TOP - 55), fg)
        if wx: fr.alpha_composite(tv.wx_layer(wx, wxp, tt, True), (0, tv.WX_Y0))
        if tt >= end0: card, t0 = cta_card, end0
        elif tt >= key0: card, t0 = done_card, key0
        elif tt >= turn0: card, t0 = turn_card, turn0
        else:
            k = max((k for k, l in enumerate(lines) if tt >= l["start"] - 0.02), default=0); card, t0 = cards[k], lines[k]["start"]
        f = max(0, min(1, (tt - t0) / 0.18)); dy = int(30 * (1 - f))
        if f < 1: card = card.copy(); card.putalpha(card.getchannel("A").point(lambda v: int(v * f)))
        fr.paste(card, (20, tv.CARD_Y - 40 + dy), card)
        if cd0 <= tt < cd0 + 3.0:
            u = tt - cd0; r = ring(3 - int(u), 1 - (u - int(u)))
            fr.paste(r, ((W - r.width) // 2, tv.CARD_Y + 470), r)
        if tt < HOOK:
            a = min(1.0, tt / 0.12, (HOOK - tt) / 0.3)
            if a > 0:
                b = banner if a >= 1 else banner.copy()
                if a < 1: b.putalpha(b.getchannel("A").point(lambda v: int(v * a)))
                fr.paste(b, (40, 130), b)
        return fr.convert("RGB")

    return meta, lines, audio, n, frame


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("story"); ap.add_argument("-o", "--out", default="output/practice/video.mp4")
    ap.add_argument("--rate", default="-8%"); ap.add_argument("--dummy-audio", action="store_true")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        meta, lines, audio, n, frame = build(a.story, a.rate, a.dummy_audio, tmp)
        wav = os.path.join(tmp, "final.wav"); tv.write_wav(wav, audio)
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                              "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
                              "-movflags", "+faststart", "-t", f"{n / FPS:.2f}", a.out], stdin=subprocess.PIPE)
        for i in range(n):
            p.stdin.write(frame(i).tobytes())
        p.stdin.close(); p.wait()
        print(f"Wrote {a.out} ({n / FPS:.1f}s)")


if __name__ == "__main__":
    main()
