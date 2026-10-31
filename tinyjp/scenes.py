"""Scene library (Japanese signs). Each scene: a drawing function, walkable named spots (x in pixels), and aliases.
Only scenes registered in SCENES exist; the director prompt must list exactly these."""
import math, random, re, zlib
from PIL import Image, ImageDraw
from .config import *
from .fonts import font

FLOOR = 1190          # feet baseline of the characters
HORIZON = 1130        # where the wall meets the floor

def lerp(a, b, u): return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3))
def grad(d, y0, y1, top, bot):
    for y in range(y0, y1): d.line((0, y, W, y), fill=lerp(top, bot, (y - y0) / max(1, y1 - y0 - 1)))
def win(d, x, y, w, h, frame=(150, 120, 100), glass=(196, 224, 246), cross=True, t=10):
    d.rectangle((x - t, y - t, x + w + t, y + h + t), fill=frame); d.rectangle((x, y, x + w, y + h), fill=glass)
    if cross: d.line((x + w // 2, y, x + w // 2, y + h), fill=frame, width=6); d.line((x, y + h // 2, x + w, y + h // 2), fill=frame, width=6)
def awning(d, x0, x1, y, h, c1, c2, n=9):
    sw = (x1 - x0) / n
    for i in range(n):
        d.rectangle((x0 + i * sw, y, x0 + (i + 1) * sw, y + h), fill=c1 if i % 2 == 0 else c2)
        d.pieslice((x0 + i * sw, y + h - sw / 2, x0 + (i + 1) * sw, y + h + sw / 2), 0, 180, fill=c1 if i % 2 == 0 else c2)
def tree(d, cx, base, r, trunk=(130, 100, 80), leaf=(150, 200, 150)):
    d.rectangle((cx - 16, base - r, cx + 16, base), fill=trunk)
    for dx, dy, rr in ((0, -r, r), (-r * 0.6, -r * 0.7, r * 0.7), (r * 0.6, -r * 0.7, r * 0.7), (0, -r * 1.5, r * 0.7)):
        d.ellipse((cx + dx - rr, base + dy - rr, cx + dx + rr, base + dy + rr), fill=lerp(leaf, (255, 255, 255), 0.08 if dy < -r else 0))
def clouds(d, spots):
    for x, y, s in spots:
        for dx, dy, r in ((0, 0, 50), (50, 10, 40), (-50, 12, 36), (20, -22, 36)):
            d.ellipse((x + dx * s - r * s, y + dy * s - r * s, x + dx * s + r * s, y + dy * s + r * s), fill=(255, 255, 255))
def lamp(d, x, base, h=420):
    d.rectangle((x - 8, base - h, x + 8, base), fill=(52, 84, 70)); d.rectangle((x - 22, base - 22, x + 22, base), fill=(52, 84, 70))
    d.line((x, base - h, x + 40, base - h - 20), fill=(52, 84, 70), width=8)
    d.ellipse((x + 22, base - h - 56, x + 66, base - h - 8), fill=(255, 236, 170), outline=(52, 84, 70), width=4)
def eiffel(d, cx, base, h, col):
    w = h * 0.34
    d.polygon([(cx - w / 2, base), (cx - w * 0.12, base - h * 0.46), (cx - w * 0.04, base - h * 0.8), (cx, base - h), (cx + w * 0.04, base - h * 0.8), (cx + w * 0.12, base - h * 0.46), (cx + w / 2, base)], fill=col)
    d.rectangle((cx - w * 0.2, base - h * 0.46, cx + w * 0.2, base - h * 0.43), fill=col); d.rectangle((cx - w * 0.12, base - h * 0.72, cx + w * 0.12, base - h * 0.7), fill=col)
def checker(d, y0, y1, c1, c2, s=90):
    for r, y in enumerate(range(y0, y1, s // 2)):
        for i, x in enumerate(range(-s * (r % 2) // 1, W, s)):
            d.rectangle((x, y, x + s, y + s // 2), fill=c1 if (i + r) % 2 == 0 else c2)

def street(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (169, 208, 245), (255, 236, 240)); clouds(d, [(240, 330, 1.2), (860, 440, 0.9)])
    eiffel(d, 860, 1000, 520, (170, 176, 214))
    for x0, x1, col in ((0, 380, (250, 238, 214)), (380, 700, (246, 214, 206)), (700, 1080, (222, 230, 246))):
        d.rectangle((x0, 700, x1, HORIZON), fill=col); d.rectangle((x0, 640, x1, 710), fill=(112, 122, 152))
        for xx in range(x0 + 40, x1 - 40, 110): d.rectangle((xx, 600, xx + 60, 660), fill=(98, 108, 138)); d.rectangle((xx + 8, 612, xx + 52, 660), fill=(190, 214, 240))
        for yy in (760, 900):
            for xx in range(x0 + 50, x1 - 60, 110): win(d, xx, yy, 56, 100, frame=(150, 130, 120))
        for xx in range(x0 + 40, x1 - 60, 110): d.rectangle((xx - 4, 872, xx + 70, 884), fill=(60, 66, 84))
    d.rectangle((640, 1000, 1010, HORIZON + 6), fill=(255, 245, 232)); awning(d, 630, 1020, 960, 54, (246, 182, 205), (255, 255, 255), 8)
    win(d, 670, 1050, 300, 70, frame=(120, 100, 90), glass=(222, 238, 250), cross=False, t=6)
    grad(d, HORIZON, H, (214, 210, 222), (190, 186, 202)); d.rectangle((0, HORIZON, W, HORIZON + 14), fill=(170, 166, 184))
    rng = random.Random(3)
    for _ in range(90): x, y = rng.randint(0, W), rng.randint(HORIZON + 30, 1700); d.ellipse((x, y, x + 22, y + 8), outline=(176, 172, 190))
    lamp(d, 80, 1180); tree(d, 1010, 1150, 90)
    d.rounded_rectangle((330, 1100, 530, 1130), radius=8, fill=(150, 108, 76)); d.rounded_rectangle((330, 1040, 530, 1076), radius=8, fill=(176, 130, 92))
    for x in (350, 505): d.rectangle((x, 1130, x + 14, 1190), fill=(60, 66, 84))

def bakery(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (255, 238, 218), (250, 222, 198))
    d.rectangle((0, 880, W, HORIZON), fill=(246, 190, 205))
    for x in range(0, W, 60): d.line((x, 880, x, HORIZON), fill=(236, 170, 188), width=2)
    for y in range(880, HORIZON, 50): d.line((0, y, W, y), fill=(236, 170, 188), width=2)
    awning(d, 0, W, 330, 90, (246, 182, 205), (255, 245, 232), 12)
    d.rounded_rectangle((250, 250, 830, 330), radius=14, fill=(120, 76, 56)); d.text((540, 290), "パン屋", font=font(54), fill=(255, 220, 140), anchor="mm")
    d.rectangle((480, 520, 1060, 540), fill=(176, 130, 92)); d.rectangle((480, 680, 1060, 700), fill=(176, 130, 92)); d.rectangle((480, 840, 1060, 860), fill=(176, 130, 92))
    rng = random.Random(5)
    for row in (520, 680):
        for x in range(500, 1040, 56):
            d.polygon([(x, row), (x + 26, row), (x + 36, row - 120 + rng.randint(-10, 10)), (x + 10, row - 120)], fill=(224, 168, 92), outline=(168, 112, 50))
    win(d, 250, 520, 200, 340, glass=(196, 228, 250)); d.line((250, 700, 450, 700), fill=(150, 120, 100), width=6)
    d.rectangle((20, 500, 220, HORIZON), fill=(130, 84, 62)); d.rectangle((50, 540, 190, 860), fill=(206, 234, 248)); d.ellipse((184, 840, 204, 860), fill=(255, 220, 140))
    d.polygon([(100, 470), (140, 470), (130, 520), (110, 520)], fill=(255, 220, 140))
    d.rectangle((480, 940, W, HORIZON + 10), fill=(214, 168, 128)); d.rectangle((470, 920, W, 950), fill=(240, 208, 170))
    d.rectangle((560, 780, 1050, 920), fill=(226, 242, 250), outline=(150, 170, 190), width=5)
    d.line((560, 850, 1050, 850), fill=(180, 196, 210), width=4)
    for i, x in enumerate(range(590, 1030, 64)):
        d.ellipse((x - 24, 806, x + 24, 842), fill=(226, 160, 78), outline=(176, 110, 48), width=3)
        for k, col in enumerate(((246, 168, 196), (200, 230, 190), (250, 216, 130), (185, 167, 245))):
            d.ellipse((x - 26 + k * 14, 876, x - 10 + k * 14, 896), fill=col)
    d.rectangle((520, 880, 600, 920), fill=(70, 76, 96)); d.rectangle((530, 890, 590, 906), fill=(169, 208, 245))
    checker(d, HORIZON, H, (250, 244, 232), (226, 204, 186))

def cafe(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (255, 246, 234), (246, 226, 206))
    d.rectangle((20, 500, 200, HORIZON), fill=(120, 84, 70)); d.rectangle((50, 540, 170, 860), fill=(206, 234, 248)); d.ellipse((164, 840, 184, 860), fill=(255, 220, 140))
    win(d, 260, 420, 300, 480, glass=(190, 222, 248)); d.rectangle((270, 700, 550, 900), fill=(246, 214, 206)); d.rectangle((320, 600, 420, 900), fill=(222, 230, 246))
    d.arc((260, 340, 560, 420), 180, 360, fill=(190, 150, 80), width=8); d.text((410, 370), "カフェ", font=font(50), fill=(190, 150, 80), anchor="mm")
    d.rounded_rectangle((620, 400, 900, 720), radius=14, fill=(176, 130, 92)); d.rounded_rectangle((634, 414, 886, 706), radius=8, fill=(50, 70, 64))
    d.text((760, 470), "メニュー", font=font(46), fill=(255, 255, 255), anchor="mm")
    for k, tx in enumerate(("コーヒー", "おちゃ", "パン", "ジュース")):
        d.text((660, 540 + k * 40), tx, font=font(30, False), fill=(240, 240, 230), anchor="lm"); d.text((860, 540 + k * 40), "· · ·", font=font(26, False), fill=(240, 240, 230), anchor="rm")
    for x in (200, 560, 920):
        d.line((x, 0, x, 250), fill=(80, 70, 90), width=4); d.pieslice((x - 50, 230, x + 50, 330), 180, 360, fill=(246, 182, 205)); d.ellipse((x - 14, 292, x + 14, 316), fill=(255, 236, 170))
    d.rectangle((780, 930, W, HORIZON + 10), fill=(150, 108, 76)); d.rectangle((770, 910, W, 940), fill=(190, 140, 100))
    d.rectangle((820, 810, 960, 910), fill=(190, 196, 210), outline=(120, 126, 150), width=4); d.rectangle((840, 790, 940, 812), fill=(150, 156, 176)); d.ellipse((960, 850, 1000, 910), fill=(150, 156, 176))
    checker(d, HORIZON, H, (250, 244, 236), (170, 176, 210))
    d.ellipse((310, 1096, 570, 1142), fill=(230, 196, 160)); d.rectangle((430, 1130, 450, 1190), fill=(110, 90, 80)); d.ellipse((380, 1176, 500, 1196), fill=(110, 90, 80))
    for cx in (330, 560):
        d.ellipse((cx - 36, 1090, cx + 36, 1120), fill=(190, 140, 100)); d.rectangle((cx - 4, 1112, cx + 4, 1180), fill=(110, 90, 80))

def park(img):
    d = ImageDraw.Draw(img); grad(d, 0, 1100, (190, 228, 252), (236, 248, 238)); clouds(d, [(260, 340, 1.1), (820, 460, 1.0)])
    eiffel(d, 560, 1010, 380, (190, 206, 230))
    d.rectangle((0, 960, W, 1110), fill=(120, 176, 124)); grad(d, 1100, H, (170, 210, 150), (150, 196, 132))
    d.polygon([(380, 1100), (700, 1100), (940, H), (140, H)], fill=(236, 222, 196))
    tree(d, 90, 1100, 150, leaf=(120, 184, 128)); tree(d, 1000, 1110, 130, leaf=(150, 200, 150))
    rng = random.Random(8)
    for _ in range(40):
        x, y = rng.randint(0, W), rng.randint(1180, 1700)
        if 380 < x < 940: continue
        d.ellipse((x, y, x + 12, y + 12), fill=rng.choice(((246, 150, 180), (255, 255, 255), (255, 214, 120))))
    d.rounded_rectangle((170, 1090, 390, 1120), radius=8, fill=(150, 108, 76)); d.rounded_rectangle((170, 1030, 390, 1064), radius=8, fill=(176, 130, 92))
    for x in (186, 366): d.rectangle((x, 1120, x + 12, 1180), fill=(70, 76, 96))
    d.ellipse((620, 1120, 940, 1210), fill=(190, 198, 214), outline=(150, 158, 178), width=4); d.ellipse((650, 1130, 910, 1190), fill=(169, 208, 245))
    d.rectangle((770, 1000, 790, 1160), fill=(190, 198, 214)); d.ellipse((730, 990, 830, 1030), fill=(190, 198, 214))
    for a in range(-60, 61, 30): d.arc((780 - abs(a) - 40, 920, 780 + abs(a) + 40, 1080), 200 + a * 0.4, 340 + a * 0.4, fill=(210, 232, 250), width=4)

def classroom(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (240, 248, 236), (228, 238, 226))
    d.rectangle((0, 960, W, HORIZON), fill=(214, 226, 208))
    d.rectangle((20, 500, 200, HORIZON), fill=(150, 108, 76)); d.rectangle((50, 540, 170, 820), fill=(206, 234, 248))
    d.rounded_rectangle((220, 380, 860, 780), radius=14, fill=(176, 130, 92)); d.rounded_rectangle((238, 398, 842, 762), radius=8, fill=(52, 84, 70))
    d.text((540, 520), "こんにちは", font=font(96), fill=(255, 255, 255), anchor="mm"); d.text((540, 650), "あ  い  う  え  お", font=font(54, False), fill=(240, 244, 240), anchor="mm")
    d.rectangle((220, 780, 860, 800), fill=(150, 108, 76)); d.rectangle((300, 770, 340, 780), fill=(255, 255, 255)); d.rectangle((380, 770, 410, 780), fill=(246, 182, 205))
    win(d, 900, 400, 150, 360, glass=(196, 226, 250)); d.ellipse((210, 230, 330, 350), fill=(255, 255, 255), outline=(120, 100, 90), width=8)
    d.line((270, 290, 270, 250), fill=(60, 60, 80), width=5); d.line((270, 290, 300, 300), fill=(60, 60, 80), width=5)
    for x in range(0, W, 120): d.line((x, HORIZON, x - 60, H), fill=(190, 156, 116), width=3)
    grad(d, HORIZON, H, (214, 184, 144), (196, 164, 124))
    d.rounded_rectangle((780, 1050, 1060, 1090), radius=8, fill=(236, 206, 160)); d.rectangle((800, 1090, 814, 1190), fill=(120, 90, 70)); d.rectangle((1020, 1090, 1034, 1190), fill=(120, 90, 70))
    d.rounded_rectangle((850, 1100, 970, 1130), radius=8, fill=(176, 130, 92))

def metro(img):
    d = ImageDraw.Draw(img); d.rectangle((0, 0, W, HORIZON), fill=(240, 244, 246))
    for x in range(0, W, 60): d.line((x, 0, x, HORIZON), fill=(206, 216, 222), width=3)
    for y in range(0, HORIZON, 40): d.line((0, y, W, y), fill=(206, 216, 222), width=3)
    d.rectangle((0, 0, W, 200), fill=(34, 56, 74)); d.rounded_rectangle((340, 330, 740, 470), radius=30, fill=(70, 140, 100)); d.text((540, 400), "地下鉄", font=font(76), fill=(255, 255, 255), anchor="mm")
    for x in (400, 680): d.ellipse((x - 26, 480, x + 26, 532), fill=(255, 255, 255), outline=(70, 140, 100), width=5); d.text((x, 506), "M", font=font(30), fill=(70, 140, 100), anchor="mm")
    d.polygon([(0, 420), (250, 520), (250, HORIZON), (0, HORIZON)], fill=(52, 60, 84))
    for i in range(7): d.line((0, 520 + i * 90, 250, 560 + i * 90), fill=(90, 100, 130), width=6)
    d.line((250, 520, 250, HORIZON), fill=(180, 190, 206), width=8)
    d.rounded_rectangle((420, 620, 700, 1030), radius=24, fill=(38, 48, 74)); d.rounded_rectangle((450, 660, 670, 820), radius=14, fill=(169, 208, 245))
    d.text((560, 740), "きっぷ", font=font(44), fill=(38, 48, 74), anchor="mm"); d.rounded_rectangle((470, 860, 650, 880), radius=8, fill=(20, 24, 40)); d.rectangle((470, 920, 650, 990), fill=(70, 76, 100))
    d.rounded_rectangle((760, 560, 1120, 1110), radius=18, fill=(236, 240, 250), outline=(150, 160, 190), width=6)
    for x in (790, 940): d.rectangle((x, 600, x + 140, 1100), fill=(206, 214, 232), outline=(150, 160, 190), width=4); d.rectangle((x + 20, 650, x + 120, 850), fill=(169, 208, 245))
    d.rectangle((760, 900, 1120, 940), fill=(70, 100, 190))
    grad(d, HORIZON, H, (176, 180, 196), (156, 160, 180)); d.rectangle((0, 1230, W, 1262), fill=(250, 214, 90))

def _make(name, fn, spots, aliases=()):
    return dict(name=name, draw=fn, spots=spots, aliases=list(aliases))

SCENES = {
    "street": _make("street", street, {"lamp": 120, "bench": 430, "shop window": 800}, ["town", "road", "city", "まち", "みち"]),
    "bakery": _make("bakery", bakery, {"entrance": 110, "window": 350, "counter": 640, "display": 900}, ["bakery shop", "pastry shop", "パン屋"]),
    "cafe": _make("cafe", cafe, {"entrance": 110, "table": 440, "counter": 900}, ["café", "coffee shop", "カフェ"]),
    "park": _make("park", park, {"bench": 280, "fountain": 780}, ["garden", "こうえん", "公園"]),
    "classroom": _make("classroom", classroom, {"door": 110, "board": 540, "desk": 900}, ["school", "class", "がっこう", "学校", "きょうしつ"]),
    "metro": _make("metro", metro, {"entrance": 120, "ticket machine": 560, "platform": 920}, ["metro station", "subway", "underground", "地下鉄", "ちかてつ"]),
}
from .scenes_more import EXTRA
SCENES.update(EXTRA)

ALIAS = {}
for k, v in SCENES.items():
    ALIAS[k] = k
    for a in v["aliases"]: ALIAS[a] = k

# A few extra names people use for places that exist under another name.
for _a, _k in {"shop": "supermarket", "hotel": "restaurant", "izakaya": "restaurant", "temple": "park", "shrine": "park"}.items():
    ALIAS.setdefault(_a, _k)

def resolve(name):
    return ALIAS.get(name.strip().lower())

# Per-scene tuning, e.g. {"bakery": dict(scale=0.7, floor=1200)}: scale = character size, floor = y of the feet.
SCENE_TUNING = {}
def scale_of(name): return SCENE_TUNING.get(name, {}).get("scale", CHAR_SCALE)
def floor_of(name): return SCENE_TUNING.get(name, {}).get("floor", FLOOR)

# `scene: auto` picks the place from the story text; with no clue it falls back to a stable, title-based choice,
# so different lessons land in different places instead of always starting in the same one.
KEYWORDS = {
    "bakery": ["パン", "パン屋", "クロワッサン", "ベーカリー", "bakery", "bread", "pastry", "croissant", "baguette"],
    "cafe": ["カフェ", "コーヒー", "こうちゃ", "お茶", "おちゃ", "ケーキ", "cafe", "café", "coffee", "tea", "cake"],
    "restaurant": ["レストラン", "ラーメン", "すし", "寿司", "メニュー", "ちゅうもん", "注文", "おなか", "ごはん", "定食", "restaurant", "menu", "order", "ramen", "sushi", "hungry", "lunch", "dinner", "waiter"],
    "supermarket": ["スーパー", "コンビニ", "かいもの", "買い物", "いくら", "レジ", "supermarket", "convenience", "groceries", "checkout", "how much", "price", "shopping"],
    "bookstore": ["ほんや", "本屋", "しょてん", "書店", "ほん", "bookstore", "book", "books", "read"],
    "classroom": ["がっこう", "学校", "せんせい", "先生", "じゅぎょう", "しゅくだい", "きょうしつ", "教室", "classroom", "school", "teacher", "student", "homework", "class"],
    "metro": ["ちかてつ", "地下鉄", "きっぷ", "切符", "かいさつ", "metro", "subway", "ticket", "underground"],
    "train station": ["えき", "駅", "でんしゃ", "電車", "ホーム", "しんかんせん", "のりば", "station", "train", "platform", "railway", "bus stop"],
    "museum": ["びじゅつかん", "美術館", "はくぶつかん", "博物館", "museum", "painting", "statue", "exhibition", "gallery"],
    "tower": ["タワー", "とうきょうタワー", "てんぼうだい", "展望台", "tower", "observation", "viewpoint"],
    "park": ["こうえん", "公園", "さんぽ", "ベンチ", "ピクニック", "park", "garden", "bench", "picnic", "fountain", "walk"],
    "airport": ["くうこう", "空港", "ひこうき", "飛行機", "パスポート", "にもつ", "airport", "plane", "flight", "passport", "suitcase", "boarding", "luggage"],
    "beach": ["うみ", "海", "なつ", "夏", "およぐ", "ビーチ", "すなはま", "beach", "sea", "sand", "swim", "summer", "holiday", "vacation"],
    "apartment": ["いえ", "家", "うち", "へや", "部屋", "ただいま", "ソファ", "かぞく", "apartment", "sofa", "kitchen", "home", "house", "living room", "room", "family"],
    "market": ["いちば", "市場", "やさい", "さかな", "くだもの", "market", "stall", "vegetables", "fish", "fruit"],
    "library": ["としょかん", "図書館", "かりる", "しずかに", "library", "borrow", "silence", "librarian"],
    "street": ["まち", "みち", "道", "よる", "夜", "こうさてん", "street", "city", "road", "town", "turn left", "turn right", "directions", "night"],
}

def scene_for(script):
    """Scene name for the script's header (`scene:`), or None if unknown. Handles `scene: auto`."""
    raw = (script.meta.get("scene") or "auto").strip()
    if raw.lower() != "auto": return resolve(raw)
    for ev in script.story:                      # the first @scene wins, so the cover matches the opening shot
        if hasattr(ev, "place"): return resolve(ev.place)
    text = " ".join([script.meta.get("title", "")] + [f"{e.jp} {e.en}" for e in script.story if hasattr(e, "jp")]).lower()
    best, top = None, 0
    for name, kws in KEYWORDS.items():
        n = 0
        for k in kws:
            n += len(re.findall(r"(?<!\w)" + re.escape(k) + r"(?!\w)", text)) if k.isascii() else (text.count(k) if len(k) > 1 else 0)
        if n > top: best, top = name, n
    if best: return best
    key = (script.meta.get("title", "") + "|" + str(script.meta.get("episode", ""))).encode("utf-8")
    return list(SCENES)[zlib.crc32(key) % len(SCENES)]

_cache = {}
def background(name):
    if name not in _cache:
        img = Image.new("RGB", (W, H)); SCENES[name]["draw"](img); _cache[name] = img
    return _cache[name].copy()
