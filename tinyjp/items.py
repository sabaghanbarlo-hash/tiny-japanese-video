"""Story objects. ITEMS is the single registry: only things drawn here may appear in the director prompt."""
import math, re
from PIL import ImageDraw

EDIBLE = {"croissant", "baguette", "macaron", "ice cream", "onigiri", "ramen"}
DRINKABLE = {"coffee", "juice", "tea"}
ITEMS = ["croissant", "baguette", "macaron", "coffee", "juice", "menu", "book", "notebook", "bag", "ticket", "phone", "map", "umbrella", "flowers", "ice cream", "onigiri", "ramen", "tea"]
ALIASES = {"coffee cup": "coffee", "cup of coffee": "coffee", "cafe": "coffee", "café": "coffee", "orange juice": "juice", "glass of juice": "juice", "juice glass": "juice",
           "shopping bag": "bag", "ice-cream": "ice cream", "icecream": "ice cream", "bouquet": "flowers", "flower": "flowers", "croissants": "croissant",
           "baguettes": "baguette", "macarons": "macaron", "tickets": "ticket", "metro ticket": "ticket", "cell phone": "phone", "smartphone": "phone", "sketchbook": "notebook", "green tea": "tea", "tea cup": "tea", "rice ball": "onigiri", "omusubi": "onigiri", "noodles": "ramen", "ramen bowl": "ramen", "bowl of ramen": "ramen", "bread": "croissant", "train ticket": "ticket"}
_DET = re.compile(r"^(?:a|an|the|her|his|their|some|one|my|a cup of|a glass of)\s+")

def find(text):
    t = _DET.sub("", text.strip().lower())
    t = _DET.sub("", t)
    if t in ITEMS: return t
    return ALIASES.get(t)

def _rot(cx, cy, w, h, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]

def draw(d, kind, x, y, bites=0):
    """Draw item centred at (x, y) in sprite coordinates (about 80-110 px)."""
    if kind == "onigiri":
        if bites < 2:
            d.polygon([(x, y - 42), (x - 42, y + 30), (x + 42, y + 30)], fill=(252, 252, 250), outline=(200, 200, 208))
            d.rectangle((x - 20, y + 6, x + 20, y + 30), fill=(40, 52, 46))
    elif kind == "ramen":
        d.ellipse((x - 56, y - 6, x + 56, y + 52), fill=(214, 70, 60), outline=(150, 40, 40), width=3)
        d.ellipse((x - 48, y - 24, x + 48, y + 14), fill=(240, 190, 100)); d.ellipse((x - 20, y - 20, x + 6, y), fill=(255, 250, 240)); d.ellipse((x - 11, y - 15, x - 1, y - 5), fill=(250, 190, 60))
        d.arc((x + 6, y - 20, x + 40, y + 6), 20, 200, fill=(226, 170, 80), width=4); d.line((x + 14, y - 50, x + 52, y - 12), fill=(150, 108, 76), width=4); d.line((x + 24, y - 54, x + 62, y - 16), fill=(150, 108, 76), width=4)
    elif kind == "tea":
        d.rounded_rectangle((x - 26, y - 24, x + 26, y + 30), radius=10, fill=(244, 248, 240), outline=(170, 190, 160), width=3)
        d.ellipse((x - 22, y - 22, x + 22, y - 6), fill=(150, 190, 110))
        for k in (-8, 8): d.arc((x + k - 6, y - 56, x + k + 6, y - 30), 90, 270, fill=(210, 220, 210), width=3)
    elif kind == "croissant":
        n = max(1, 5 - bites)
        for i in range(n):
            a = math.radians(205 + i * 32); px, py = x + 44 * math.cos(a), y + 30 + 40 * math.sin(a)
            r = 14 + 12 * math.sin(math.pi * (i + 0.6) / 5.4)
            d.ellipse((px - r, py - r * 0.8, px + r, py + r * 0.8), fill=(226, 160, 78), outline=(176, 110, 48), width=3)
    elif kind == "baguette":
        L = 150 - bites * 30
        d.polygon(_rot(x, y, L, 30, -0.55), fill=(224, 168, 92), outline=(168, 112, 50))
        for k in (-0.3, 0, 0.3):
            px, py = x + k * L * math.cos(-0.55), y + k * L * math.sin(-0.55)
            d.line((px - 7, py - 12, px + 7, py + 12), fill=(176, 118, 56), width=4)
    elif kind == "macaron":
        if bites < 2:
            d.ellipse((x - 34, y - 26, x + 34, y - 4), fill=(246, 168, 196)); d.rectangle((x - 30, y - 6, x + 30, y + 4), fill=(255, 245, 232))
            d.ellipse((x - 34, y, x + 34, y + 24), fill=(246, 168, 196))
    elif kind == "coffee":
        d.ellipse((x - 46, y + 18, x + 46, y + 40), fill=(240, 236, 236), outline=(190, 186, 190), width=2)
        d.rounded_rectangle((x - 30, y - 24, x + 30, y + 26), radius=12, fill=(255, 255, 255), outline=(190, 186, 190), width=3)
        d.arc((x + 18, y - 12, x + 52, y + 16), -80, 80, fill=(190, 186, 190), width=6)
        d.ellipse((x - 26, y - 22, x + 26, y - 8), fill=(120, 76, 52))
        for k in (-10, 8): d.arc((x + k - 6, y - 56, x + k + 6, y - 28), 90, 270, fill=(210, 210, 220), width=3)
    elif kind == "juice":
        d.polygon([(x - 28, y - 40), (x + 28, y - 40), (x + 22, y + 34), (x - 22, y + 34)], fill=(255, 236, 200, 255), outline=(190, 200, 210))
        d.polygon([(x - 26, y - 14), (x + 26, y - 14), (x + 21, y + 32), (x - 21, y + 32)], fill=(250, 170, 60))
        d.line((x + 6, y - 66, x + 18, y - 10), fill=(240, 100, 130), width=6)
    elif kind == "menu":
        d.rounded_rectangle((x - 34, y - 52, x + 34, y + 52), radius=8, fill=(255, 246, 228), outline=(176, 130, 92), width=4)
        for k in range(5): d.line((x - 20, y - 30 + k * 16, x + 20, y - 30 + k * 16), fill=(176, 130, 92), width=3)
    elif kind == "book":
        d.rounded_rectangle((x - 40, y - 30, x + 40, y + 30), radius=6, fill=(104, 126, 190), outline=(62, 80, 140), width=3)
        d.rectangle((x - 40, y - 30, x - 30, y + 30), fill=(62, 80, 140)); d.rectangle((x - 18, y - 12, x + 24, y - 4), fill=(255, 245, 232))
    elif kind == "notebook":
        d.rounded_rectangle((x - 34, y - 44, x + 34, y + 44), radius=6, fill=(250, 210, 224), outline=(210, 140, 170), width=3)
        for k in range(5): d.ellipse((x - 40, y - 34 + k * 17, x - 30, y - 26 + k * 17), fill=(120, 120, 140))
    elif kind == "bag":
        d.polygon([(x - 36, y - 24), (x + 36, y - 24), (x + 44, y + 44), (x - 44, y + 44)], fill=(185, 167, 245), outline=(130, 110, 200))
        d.arc((x - 22, y - 56, x + 22, y - 4), 180, 360, fill=(130, 110, 200), width=6)
    elif kind == "ticket":
        d.rounded_rectangle((x - 40, y - 22, x + 40, y + 22), radius=6, fill=(255, 238, 170), outline=(214, 180, 90), width=3)
        d.ellipse((x - 6, y - 30, x + 6, y - 18), fill=(255, 255, 255)); d.line((x - 26, y, x + 26, y), fill=(214, 180, 90), width=3)
    elif kind == "phone":
        d.rounded_rectangle((x - 22, y - 44, x + 22, y + 44), radius=8, fill=(40, 44, 60)); d.rounded_rectangle((x - 17, y - 36, x + 17, y + 34), radius=4, fill=(169, 208, 245))
    elif kind == "map":
        d.polygon([(x - 46, y - 34), (x - 16, y - 40), (x + 16, y - 34), (x + 46, y - 40), (x + 46, y + 34), (x + 16, y + 40), (x - 16, y + 34), (x - 46, y + 40)], fill=(246, 238, 210), outline=(176, 160, 120))
        d.line((x - 30, y + 10, x - 6, y - 10, x + 14, y + 6, x + 34, y - 14), fill=(110, 150, 200), width=4); d.ellipse((x + 24, y - 24, x + 36, y - 12), fill=(224, 80, 90))
    elif kind == "umbrella":
        d.pieslice((x - 70, y - 60, x + 70, y + 40), 180, 360, fill=(185, 167, 245), outline=(130, 110, 200))
        d.line((x, y - 10, x, y + 70), fill=(80, 70, 110), width=6); d.arc((x - 14, y + 50, x + 14, y + 84), 0, 180, fill=(80, 70, 110), width=6)
    elif kind == "flowers":
        for k in (-18, 0, 18): d.line((x + k * 0.3, y + 50, x + k, y - 6), fill=(90, 160, 100), width=5)
        for k, col in ((-18, (246, 150, 180)), (0, (255, 200, 120)), (18, (246, 182, 205))):
            for a in range(0, 360, 72):
                d.ellipse((x + k + 12 * math.cos(math.radians(a)) - 9, y - 10 + 12 * math.sin(math.radians(a)) - 9, x + k + 12 * math.cos(math.radians(a)) + 9, y - 10 + 12 * math.sin(math.radians(a)) + 9), fill=col)
            d.ellipse((x + k - 6, y - 16, x + k + 6, y - 4), fill=(255, 240, 160))
    elif kind == "ice cream":
        d.polygon([(x - 24, y), (x + 24, y), (x, y + 74)], fill=(226, 176, 100), outline=(176, 126, 60))
        if bites < 3:
            d.ellipse((x - 30, y - 34, x + 30, y + 18), fill=(246, 182, 205))
        if bites < 2:
            d.ellipse((x - 24, y - 64, x + 24, y - 14), fill=(255, 245, 232))
