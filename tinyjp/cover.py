"""Reel covers (1080x1920), shared by Story and Small modes.

The scene is drawn by the caller; this adds the title card. The card is kept inside the band that survives both
Instagram crops (profile grid 3:4 and feed 4:5), so the title is never cut off.
"""
from PIL import Image, ImageDraw, ImageFilter
from .config import W, NAVY, BLUSH, LAVENDER, BRAND
from .fonts import font

GRID_TOP, GRID_BOTTOM = 240, 1680
CARD_W = 920


def _wrap(text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if f.getlength(t) <= maxw or not cur:
            cur = t
        else:
            out.append(cur); cur = w
    return out + [cur] if cur else out


def fit_title(text, maxw=820, maxlines=3, sizes=(112, 100, 90, 80, 72, 64, 56)):
    for s in sizes:
        f = font(s); lines = _wrap(text, f, maxw)
        if len(lines) <= maxlines and all(f.getlength(l) <= maxw for l in lines):
            return lines, s
    s = sizes[-1]
    return _wrap(text, font(s), maxw)[:maxlines], s


def _pill(d, cx, cy, text, fill, fg, size):
    f = font(size); w = int(f.getlength(text)) + 72; h = size + 38
    d.rounded_rectangle((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), radius=h // 2, fill=fill)
    d.text((cx, cy), text, font=f, fill=fg, anchor="mm")


def compose(scene, title, episode=None, cy=620, kicker="LEARN JAPANESE"):
    """Title card on top of `scene` (PIL image). cy = vertical centre of the card. Returns an RGB image."""
    img = scene.convert("RGBA")
    text = title.strip(); text = text.upper() if len(text) < 22 else text
    lines, size = fit_title(text); lh = int(size * 1.16)
    pad_t, pad_b = 92, 92 + (20 if episode else 0)
    h = pad_t + lh * len(lines) + pad_b
    x0 = (W - CARD_W) // 2
    y0 = max(GRID_TOP + 50, min(int(cy - h / 2), GRID_BOTTOM - 50 - h))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((x0, y0 + 20, x0 + CARD_W, y0 + h + 20), radius=72, fill=(38, 48, 74, 115))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(24)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, y0, x0 + CARD_W, y0 + h), radius=72, fill=(255, 255, 255, 246))
    d.rounded_rectangle((x0 + 14, y0 + 14, x0 + CARD_W - 14, y0 + h - 14), radius=60, outline=LAVENDER + (255,), width=4)
    _pill(d, W // 2, y0, kicker, NAVY, (255, 255, 255), 38)
    f = font(size); y = y0 + pad_t
    for ln in lines:
        d.text((W // 2, y), ln, font=f, fill=NAVY, anchor="ma"); y += lh
    d.rounded_rectangle((W // 2 - 70, y + 4, W // 2 + 70, y + 14), radius=5, fill=BLUSH)
    if episode:
        _pill(d, W // 2, y0 + h, f"TINY JAPANESE  \u00b7  EPISODE {episode}", BLUSH, NAVY, 34)
    return img.convert("RGB")
