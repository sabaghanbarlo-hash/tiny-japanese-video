#!/usr/bin/env python3
"""Cover / thumbnail for a story: python cover.py stories/<name>.txt output/<name>.jpg

Same look as the video (scene, Mika & Alex) plus a big title card and the key words.
Keeps everything important inside the centre 3:4 area, so it also looks right in Instagram's profile grid.
No audio / TTS needed, so it is fast.
"""
import sys
from PIL import Image, ImageDraw, ImageFilter
import tinyvideo as T
from tinyvideo import W, H, font, wrap, CHARS, BRAND


def make_cover(story, out):
    meta, lines, vocab = T.parse_story(story)
    meta["scene"] = T.pick_scene(meta, lines)
    bg, fg = T.make_scene(meta["scene"], meta, header=False)
    fr = bg.copy(); d = ImageDraw.Draw(fr)

    # top badge: brand + episode
    ep = f"EP {meta['episode']}" if meta.get("episode") else ""
    brand = T.pill("TINY JAPANESE", BRAND)
    badges = [brand] + ([T.pill(ep, (60, 45, 48))] if ep else [])
    total = sum(b.width for b in badges) + 16 * (len(badges) - 1); x = (W - total) // 2
    for b in badges:
        fr.paste(b, (x, 150), b); x += b.width + 16

    # characters (smiling), same positions as in the video
    for nm, c in CHARS.items():
        s = T.sprite(nm, 1, False)
        fr.paste(s, (c["x"], T.CHAR_Y + 40), s)
        p = T.pill(nm, c["accent"]); fr.paste(p, (c["x"] + s.width // 2 - p.width // 2, 370), p)
    fr.paste(fg, (0, T.TABLE_TOP - 15), fg)

    # title card
    title = meta["title"]
    for size in (112, 100, 88, 76, 64):
        f = font(size); ls = wrap(title, f, 820)
        if len(ls) <= 3:
            break
    parts = [(t, f, (52, 40, 44), int(size * 1.18)) for t in ls]
    sub = "Learn Japanese · Beginner" if not vocab else "  ·  ".join(v["jp"] for v in vocab[:3])
    sf = font(44, False)
    while sf.size > 30 and sf.getlength(sub) > 820:
        sf = font(sf.size - 2, False)
    parts += [("", None, None, 44), (sub, sf, BRAND, 60)]
    card = T.card_image("Japanese conversation", BRAND, parts, min_h=470)
    fr.paste(card, (20, 1020), card)

    # key-word chips under the card
    chips = []
    for v in vocab[:3]:
        cf = font(34); label = f'{v["romaji"]} = {v["en"]}'
        while cf.size > 22 and cf.getlength(label) > 560:
            cf = font(cf.size - 2)
        w = int(cf.getlength(label)) + 56
        im = Image.new("RGBA", (w, 64), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, 63), radius=32, fill=(255, 255, 255, 235))
        ImageDraw.Draw(im).text((w / 2, 32), label, font=cf, fill=(90, 70, 78), anchor="mm"); chips.append(im)
    y = 1020 + card.height - 10
    for im in chips[:2]:  # two rows max keeps it inside the safe area
        fr.paste(im, ((W - im.width) // 2, y), im); y += 78

    fr.convert("RGB").save(out, quality=90, optimize=True)
    print("Wrote", out, "scene:", meta["scene"])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: cover.py stories/<name>.txt output/<name>.jpg")
    make_cover(sys.argv[1], sys.argv[2])
