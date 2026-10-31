"""More scenes, built from small reusable components (shelves, counters, tables, signs, balustrade...).
Registered into scenes.SCENES. Rules: every prop sits at or behind the floor line (FLOOR), so characters walk in front of
furniture and never through it; spots are walkable x positions at least MIN_GAP apart; nothing important sits in the top
safe-area band (y < 220) or in the card band at the bottom."""
import math, random
from PIL import ImageDraw
from .config import *
from .fonts import font
from .scenes import FLOOR, HORIZON, lerp, grad, win, awning, clouds, tree, lamp, checker

def _make(name, fn, spots, aliases=()):
    return dict(name=name, draw=fn, spots=spots, aliases=list(aliases))

# ---------- reusable components ----------
def floor_band(d, top, bot, edge=None):
    grad(d, HORIZON, H, top, bot)
    if edge: d.rectangle((0, HORIZON, W, HORIZON + 14), fill=edge)

def sign(d, cx, cy, w, h, text, fill, fg=(255, 255, 255), size=46):
    d.rounded_rectangle((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), radius=h // 3, fill=fill)
    d.text((cx, cy), text, font=font(size), fill=fg, anchor="mm")

def shelf(d, x0, y0, x1, y1, rows, pal, seed=1, frame=(150, 108, 76), mode="books"):
    """Shelving unit filled with books (mode='books') or boxed goods (mode='goods')."""
    d.rectangle((x0, y0, x1, y1), fill=frame); rng = random.Random(seed); rh = (y1 - y0) / rows
    for r in range(rows):
        top = int(y0 + r * rh + 8); base = int(y0 + (r + 1) * rh - 8)
        d.rectangle((x0 + 8, top, x1 - 8, base), fill=lerp(frame, (0, 0, 0), 0.35)); x = x0 + 12
        while x < x1 - 30:
            w = rng.randint(16, 30) if mode == "books" else rng.randint(36, 54); w = min(w, x1 - 12 - x)
            h = rng.randint(int(rh * 0.5), int(rh - 24)) if mode == "books" else int(rh * 0.52); col = rng.choice(pal)
            if mode == "books": d.rectangle((x, base - h, x + w, base), fill=col, outline=lerp(col, (0, 0, 0), 0.25))
            else:
                d.rounded_rectangle((x, base - h, x + w, base), radius=6, fill=col); d.rectangle((x + 4, base - h + 10, x + w - 4, base - h + 22), fill=(255, 255, 255))
            x += w + 3
        d.rectangle((x0 + 4, base, x1 - 4, base + 8), fill=frame)

def counter(d, x0, x1, ytop, body, top, h=HORIZON + 10):
    d.rectangle((x0, ytop, x1, h), fill=body); d.rectangle((x0 - 10, ytop - 20, x1 + 10, ytop + 6), fill=top)

def round_table(d, cx, ytop, w, cloth, leg=(110, 90, 80)):
    d.ellipse((cx - w // 2, ytop, cx + w // 2, ytop + 46), fill=cloth); d.rectangle((cx - 8, ytop + 30, cx + 8, FLOOR), fill=leg); d.ellipse((cx - 56, FLOOR - 14, cx + 56, FLOOR + 6), fill=leg)

def plate(d, cx, cy, r=22, rim=(255, 255, 255)):
    d.ellipse((cx - r, cy - r // 3, cx + r, cy + r // 3), fill=rim, outline=(200, 204, 214))
    d.ellipse((cx - r // 2, cy - r // 6, cx + r // 2, cy + r // 6), fill=(244, 232, 214))

def frame_art(d, x, y, w, h, seed, frame=(190, 150, 80), pal=((246, 182, 205), (169, 208, 245), (255, 220, 140), (184, 214, 193), (185, 167, 245))):
    """Original abstract painting in a gilt frame."""
    d.rectangle((x - 12, y - 12, x + w + 12, y + h + 12), fill=frame); rng = random.Random(seed); d.rectangle((x, y, x + w, y + h), fill=rng.choice(pal))
    for _ in range(5):
        a, b = rng.randint(x, x + w - 30), rng.randint(y, y + h - 30)
        d.ellipse((a, b, a + rng.randint(30, w // 2), b + rng.randint(30, h // 2)), fill=rng.choice(pal))

def balustrade(d, ytop, ybase, stone=(226, 218, 206), shade=(196, 188, 178)):
    d.rectangle((0, ytop, W, ytop + 26), fill=stone); d.rectangle((0, ybase - 24, W, ybase), fill=stone)
    for x in range(10, W, 54):
        d.rounded_rectangle((x, ytop + 26, x + 30, ybase - 24), radius=12, fill=stone, outline=shade)
    d.rectangle((0, ytop + 26, W, ytop + 30), fill=shade)

def eiffel_tower(d, cx, base, h, col, sky):
    """Large lattice-style Eiffel Tower silhouette with arch, platforms and braces."""
    w = h * 0.44
    d.polygon([(cx - w / 2, base), (cx - w * 0.16, base - h * 0.5), (cx - w * 0.05, base - h * 0.84), (cx, base - h), (cx + w * 0.05, base - h * 0.84), (cx + w * 0.16, base - h * 0.5), (cx + w / 2, base)], fill=col)
    d.polygon([(cx - w * 0.30, base), (cx - w * 0.22, base - h * 0.16), (cx + w * 0.22, base - h * 0.16), (cx + w * 0.30, base)], fill=sky)
    d.arc((cx - w * 0.30, base - h * 0.24, cx + w * 0.30, base - h * 0.08), 180, 360, fill=col, width=int(h * 0.02))
    for f, ww in ((0.5, 0.40), (0.74, 0.22)): d.rectangle((cx - w * ww / 2, base - h * f - h * 0.012, cx + w * ww / 2, base - h * f + h * 0.012), fill=lerp(col, (255, 255, 255), 0.25))
    lc = lerp(col, (255, 255, 255), 0.45)
    for f0, f1 in ((0.17, 0.5), (0.5, 0.74), (0.74, 0.9)):
        ww0 = w * (1 - 1.35 * f0) * 0.36; ww1 = w * (1 - 1.35 * f1) * 0.36
        d.line((cx - ww0, base - h * f0, cx + ww1, base - h * f1), fill=lc, width=3); d.line((cx + ww0, base - h * f0, cx - ww1, base - h * f1), fill=lc, width=3)

def conveyor(d, x0, x1, y, belt=(70, 76, 96)):
    d.rounded_rectangle((x0, y, x1, y + 26), radius=10, fill=belt)
    for x in range(int(x0) + 14, int(x1) - 10, 34): d.line((x, y + 6, x, y + 20), fill=lerp(belt, (255, 255, 255), 0.3), width=3)

def basket(d, cx, y, col=(246, 182, 205)):
    d.polygon([(cx - 48, y), (cx + 48, y), (cx + 38, y + 40), (cx - 38, y + 40)], fill=col); d.arc((cx - 40, y - 30, cx + 40, y + 20), 180, 360, fill=lerp(col, (0, 0, 0), 0.25), width=5)

def crate_produce(d, x0, x1, y, col, seed=1, r=15):
    d.rectangle((x0, y, x1, y + 60), fill=(176, 130, 92)); d.rectangle((x0, y, x1, y + 8), fill=(150, 108, 76)); rng = random.Random(seed)
    for xx in range(int(x0) + 14, int(x1) - 10, r + 5):
        for k in range(2): d.ellipse((xx, y - 12 - k * 10 + rng.randint(-3, 3), xx + r * 2 - 4, y + 14 - k * 10), fill=lerp(col, (255, 255, 255), 0.1 * k))

# ---------- scenes ----------
def supermarket(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (240, 250, 244), (222, 240, 232))
    for x in range(120, W, 300): d.rectangle((x, 230, x + 160, 244), fill=(255, 255, 255)); d.rectangle((x + 10, 244, x + 150, 252), fill=(255, 250, 220))
    sign(d, 540, 330, 620, 110, "スーパー", (90, 160, 120), size=62)
    for x, pal in ((0, ((246, 182, 205), (255, 220, 140), (169, 208, 245), (200, 230, 190))), (360, ((255, 236, 170), (250, 150, 130), (185, 167, 245), (255, 255, 255)))):
        shelf(d, x + 20, 470, x + 340, 1000, 4, pal, seed=x + 3, frame=(206, 214, 220), mode="goods")
    d.rectangle((14, 440, 40, HORIZON), fill=(206, 214, 220))
    crate_produce(d, 60, 250, 1040, (230, 70, 60), 1); crate_produce(d, 270, 440, 1040, (250, 190, 60), 2); crate_produce(d, 460, 620, 1040, (110, 180, 90), 3)
    d.rectangle((30, 1100, 640, 1112), fill=(150, 108, 76))
    counter(d, 740, W, 1010, (226, 230, 240), (176, 184, 200)); conveyor(d, 760, 1060, 984); basket(d, 880, 940)
    d.rectangle((960, 840, 1050, 984), fill=(70, 76, 96)); d.rectangle((972, 856, 1038, 900), fill=(169, 208, 245)); d.text((1005, 924), "¥", font=font(34), fill=(255, 255, 255), anchor="mm")
    floor_band(d, (236, 238, 244), (212, 214, 224), edge=(190, 196, 206)); checker(d, HORIZON + 14, H, (244, 246, 250), (222, 226, 236), 110)

def bookstore(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (252, 238, 220), (240, 218, 196))
    pal = ((176, 70, 80), (70, 110, 150), (90, 140, 110), (220, 170, 80), (130, 90, 150), (240, 230, 214))
    shelf(d, 20, 330, 420, 1090, 5, pal, seed=11, mode="books"); shelf(d, 440, 330, 700, 1090, 5, pal, seed=12, mode="books")
    sign(d, 400, 270, 420, 84, "本屋", (120, 76, 56), (255, 220, 140), size=52)
    d.ellipse((730, 470, 790, 530), fill=(255, 255, 255), outline=(120, 100, 90), width=6); d.line((760, 500, 760, 480), fill=(60, 60, 80), width=4); d.line((760, 500, 774, 506), fill=(60, 60, 80), width=4)
    win(d, 720, 560, 160, 300, glass=(206, 230, 250)); d.rectangle((728, 760, 872, 860), fill=(246, 214, 206))
    d.rounded_rectangle((740, 980, 920, 1130), radius=40, fill=(190, 90, 100)); d.rounded_rectangle((720, 1040, 760, 1170), radius=18, fill=(170, 74, 86)); d.rounded_rectangle((900, 1040, 940, 1170), radius=18, fill=(170, 74, 86))
    d.rectangle((760, 1130, 780, 1190), fill=(110, 80, 70)); d.rectangle((880, 1130, 900, 1190), fill=(110, 80, 70))
    lamp(d, 1010, 1180, 520)
    d.rounded_rectangle((950, 1080, 1060, 1100), radius=6, fill=(150, 108, 76)); d.rectangle((1000, 1100, 1012, 1190), fill=(110, 80, 70))
    for k, col in enumerate(((176, 70, 80), (70, 110, 150))): d.rectangle((964, 1060 - k * 14, 1044, 1078 - k * 14), fill=col)
    floor_band(d, (206, 160, 118), (180, 134, 98), edge=(150, 108, 76))
    for x in range(-60, W + 60, 140): d.line((x, HORIZON, x - 70, H), fill=(170, 124, 90), width=3)

def restaurant(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (252, 240, 226), (246, 226, 208))
    d.rectangle((0, 820, W, HORIZON), fill=(170, 70, 84)); d.rectangle((0, 800, W, 826), fill=(236, 214, 190))
    for x in range(0, W, 120): d.rounded_rectangle((x + 10, 850, x + 100, 1100), radius=10, outline=(196, 100, 112), width=4)
    d.rounded_rectangle((640, 300, 1020, 700), radius=40, fill=(150, 108, 76)); d.rounded_rectangle((660, 320, 1000, 680), radius=30, fill=(196, 226, 248)); d.line((830, 320, 830, 680), fill=(150, 108, 76), width=8)
    d.polygon([(640, 300), (720, 300), (700, 700), (640, 700)], fill=(250, 214, 220)); d.polygon([(1020, 300), (940, 300), (960, 700), (1020, 700)], fill=(250, 214, 220))
    eiffel_tower(d, 830, 680, 260, (170, 180, 214), (196, 226, 248))
    d.rounded_rectangle((60, 380, 520, 700), radius=14, fill=(176, 130, 92)); d.rounded_rectangle((76, 396, 504, 684), radius=8, fill=(50, 70, 64))
    d.text((290, 450), "本日のメニュー", font=font(42), fill=(255, 255, 255), anchor="mm")
    for k, tx in enumerate(("スープ", "とりにく", "サラダ", "ケーキ")): d.text((120, 520 + k * 38), tx, font=font(30, False), fill=(240, 240, 230), anchor="lm"); d.text((470, 520 + k * 38), "· · ·", font=font(26, False), fill=(240, 240, 230), anchor="rm")
    for x in (250, 640, 960): d.line((x, 0, x, 190), fill=(80, 70, 90), width=4); d.pieslice((x - 54, 170, x + 54, 280), 180, 360, fill=(246, 182, 205)); d.ellipse((x - 14, 236, x + 14, 262), fill=(255, 236, 170))
    sign(d, 540, 245, 460, 70, "レストラン", (120, 76, 56), (255, 220, 140), size=46)
    counter(d, 830, W, 1000, (150, 108, 76), (196, 150, 110))
    for x in (870, 960): d.rounded_rectangle((x - 16, 940, x + 16, 980), radius=8, fill=(255, 255, 255), outline=(200, 204, 214))
    floor_band(d, (236, 212, 184), (210, 184, 156), edge=(176, 130, 92)); checker(d, HORIZON + 14, H, (250, 244, 236), (232, 206, 196), 110)
    for cx in (330, 640):
        round_table(d, cx, 1090, 250, (255, 255, 255)); plate(d, cx - 56, 1108); plate(d, cx + 56, 1108); d.rectangle((cx - 5, 1070, cx + 5, 1100), fill=(255, 250, 220)); d.ellipse((cx - 6, 1058, cx + 6, 1074), fill=(255, 190, 90))

def train_station(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (226, 238, 246), (244, 244, 244))
    for x in range(0, W + 120, 120): d.arc((x - 300, 120, x + 300, 700), 180, 360, fill=(150, 160, 176), width=6)
    d.rectangle((0, 120, W, 134), fill=(150, 160, 176)); d.polygon([(0, 134), (W, 134), (W, 250), (0, 250)], fill=(204, 226, 244))
    for x in range(0, W, 90): d.line((x, 134, x + 30, 250), fill=(150, 160, 176), width=4)
    d.ellipse((470, 300, 610, 440), fill=(255, 255, 255), outline=(60, 66, 84), width=8); d.line((540, 370, 540, 322), fill=(60, 66, 84), width=6); d.line((540, 370, 580, 388), fill=(60, 66, 84), width=6)
    d.rounded_rectangle((120, 470, 640, 800), radius=20, fill=(34, 40, 60)); d.text((380, 510), "出発", font=font(46), fill=(255, 214, 90), anchor="mm")
    for k, (a, b, c) in enumerate((("08:15", "大阪", "A"), ("08:42", "京都", "C"), ("09:05", "札幌", "B"), ("09:30", "福岡", "D"))):
        y = 576 + k * 52; d.text((160, y), a, font=font(32), fill=(255, 255, 255), anchor="lm"); d.text((300, y), b, font=font(32), fill=(210, 224, 240), anchor="lm"); d.text((590, y), c, font=font(32), fill=(255, 214, 90), anchor="rm")
    d.rectangle((700, 430, 1080, 1130), fill=(210, 218, 230)); d.rounded_rectangle((716, 560, 1080, 1010), radius=30, fill=(56, 96, 170)); d.rectangle((716, 790, 1080, 810), fill=(255, 255, 255)); d.rectangle((716, 830, 1080, 842), fill=(210, 60, 70))
    for x in (760, 900): d.rounded_rectangle((x, 600, x + 110, 740), radius=16, fill=(196, 226, 248))
    d.rounded_rectangle((716, 1010, 1080, 1060), radius=10, fill=(40, 46, 64))
    d.rounded_rectangle((60, 880, 360, 1030), radius=16, fill=(236, 240, 246), outline=(150, 160, 190), width=5); d.rectangle((90, 920, 330, 960), fill=(169, 208, 245)); d.text((210, 940), "きっぷ", font=font(30), fill=(38, 48, 74), anchor="mm")
    d.rounded_rectangle((200, 1090, 460, 1116), radius=8, fill=(150, 108, 76)); d.rounded_rectangle((200, 1040, 460, 1070), radius=8, fill=(176, 130, 92)); d.rectangle((220, 1116, 232, 1190), fill=(60, 66, 84)); d.rectangle((430, 1116, 442, 1190), fill=(60, 66, 84))
    floor_band(d, (196, 198, 212), (170, 172, 190), edge=(150, 154, 172)); d.rectangle((0, 1260, W, 1290), fill=(250, 214, 90))

def museum(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (250, 244, 236), (238, 230, 218))
    d.rectangle((0, 260, W, 280), fill=(214, 202, 186)); d.rectangle((0, 1070, W, HORIZON), fill=(206, 192, 176))
    sign(d, 540, 340, 400, 84, "美術館", (60, 70, 100), (255, 236, 190), size=54)
    frame_art(d, 90, 470, 260, 340, 1); frame_art(d, 410, 440, 260, 400, 2, frame=(150, 108, 76)); frame_art(d, 760, 470, 260, 340, 3)
    for x in (220, 540, 890): d.polygon([(x - 50, 860), (x + 50, 860), (x + 30, 900), (x - 30, 900)], fill=(206, 190, 168)); d.rectangle((x - 40, 900, x + 40, 912), fill=(176, 160, 140))
    d.rectangle((630, 760, 800, 1130), fill=(226, 218, 206)); d.rectangle((616, 740, 814, 774), fill=(206, 196, 184))
    d.ellipse((676, 520, 756, 610), fill=(240, 236, 228)); d.rounded_rectangle((668, 600, 764, 740), radius=30, fill=(240, 236, 228)); d.polygon([(668, 640), (620, 700), (650, 706), (680, 670)], fill=(240, 236, 228)); d.polygon([(764, 640), (812, 700), (782, 706), (752, 670)], fill=(240, 236, 228))
    d.rounded_rectangle((120, 1070, 420, 1100), radius=10, fill=(120, 76, 56)); d.rounded_rectangle((120, 1100, 420, 1126), radius=8, fill=(150, 108, 76)); d.rectangle((150, 1126, 164, 1190), fill=(90, 66, 56)); d.rectangle((380, 1126, 394, 1190), fill=(90, 66, 56))
    for x in (860, 1010): d.rectangle((x - 5, 1040, x + 5, 1190), fill=(190, 150, 80)); d.ellipse((x - 14, 1028, x + 14, 1052), fill=(190, 150, 80))
    d.line((860, 1060, 1010, 1060), fill=(176, 50, 70), width=10)
    floor_band(d, (206, 170, 130), (184, 148, 112), edge=(150, 118, 90))
    for x in range(-100, W + 100, 150): d.line((x, HORIZON, x - 90, H), fill=(176, 140, 104), width=3)

def eiffel_view(img):
    d = ImageDraw.Draw(img); grad(d, 0, 1000, (150, 200, 244), (255, 236, 240)); clouds(d, [(220, 340, 1.3), (860, 300, 1.0), (700, 560, 0.8)])
    eiffel_tower(d, 540, 1040, 1000, (224, 96, 80), (236, 238, 248))
    d.rectangle((0, 960, W, 1050), fill=(150, 196, 150)); tree(d, 70, 1050, 130, leaf=(120, 184, 128)); tree(d, 1020, 1050, 140, leaf=(140, 196, 140))
    rng = random.Random(4)
    for _ in range(60): x, y = rng.randint(0, W), rng.randint(1010, 1040); d.ellipse((x, y, x + 36, y + 22), fill=(120, 176, 124))
    balustrade(d, 990, 1120); d.rectangle((0, 1120, W, HORIZON + 10), fill=(214, 206, 194))
    lamp(d, 430, 1180, 380)
    d.rounded_rectangle((830, 1090, 1040, 1118), radius=8, fill=(150, 108, 76)); d.rounded_rectangle((830, 1040, 1040, 1070), radius=8, fill=(176, 130, 92)); d.rectangle((850, 1118, 862, 1190), fill=(60, 66, 84)); d.rectangle((1010, 1118, 1022, 1190), fill=(60, 66, 84))
    grad(d, HORIZON + 10, H, (226, 218, 206), (206, 198, 186))
    for k in range(0, 6): d.line((0, HORIZON + 40 + k * 90, W, HORIZON + 40 + k * 90), fill=(196, 188, 176), width=2)

# ---------- more places (airport, beach, apartment, market, library) ----------
def vgrad(d, x0, y0, x1, y1, top, bot):
    for y in range(y0, y1): d.line((x0, y, x1, y), fill=lerp(top, bot, (y - y0) / max(1, y1 - y0 - 1)))

def airport(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (232, 240, 248), (246, 248, 250))
    d.rectangle((0, 230, W, 262), fill=(204, 212, 226))
    d.rounded_rectangle((50, 330, 520, 700), radius=20, fill=(34, 40, 60)); d.text((285, 378), "出発", font=font(44), fill=(255, 214, 90), anchor="mm")
    for k, (a, b, c) in enumerate((("09:10", "ローマ", "12"), ("09:40", "ロンドン", "08"), ("10:05", "パリ", "21"), ("10:30", "ソウル", "04"))):
        y = 450 + k * 56; d.text((84, y), a, font=font(32), fill=(255, 255, 255), anchor="lm"); d.text((210, y), b, font=font(32), fill=(210, 224, 240), anchor="lm"); d.text((490, y), c, font=font(32), fill=(255, 214, 90), anchor="rm")
    d.rounded_rectangle((556, 316, 1054, 754), radius=14, fill=(150, 160, 176)); vgrad(d, 570, 330, 1040, 640, (150, 200, 244), (222, 238, 250))
    d.rectangle((570, 640, 1040, 740), fill=(120, 126, 140))
    for x in range(580, 1040, 90): d.rectangle((x, 686, x + 46, 694), fill=(250, 250, 250))
    d.polygon([(930, 520), (985, 430), (1010, 430), (985, 540)], fill=(60, 96, 170)); d.polygon([(780, 545), (730, 610), (800, 610), (860, 552)], fill=(222, 228, 238), outline=(150, 160, 176))
    d.ellipse((640, 500, 980, 570), fill=(255, 255, 255), outline=(150, 160, 176), width=4); d.rectangle((660, 538, 960, 546), fill=(60, 96, 170))
    for x in range(700, 930, 34): d.ellipse((x, 514, x + 14, 528), fill=(169, 208, 245))
    d.rectangle((800, 330, 812, 740), fill=(150, 160, 176))
    d.rectangle((0, 760, W, HORIZON), fill=(238, 242, 248)); d.rectangle((0, HORIZON - 20, W, HORIZON), fill=(206, 212, 226))
    counter(d, 60, 560, 960, (60, 96, 170), (236, 240, 246)); sign(d, 310, 840, 300, 62, "CHECK-IN", (60, 96, 170), size=34)
    d.rounded_rectangle((250, 886, 370, 938), radius=8, fill=(34, 40, 60)); d.rectangle((300, 938, 320, 946), fill=(34, 40, 60))
    for x in (640, 780, 920):
        d.rounded_rectangle((x, 990, x + 110, 1044), radius=14, fill=(60, 96, 170)); d.rounded_rectangle((x, 1044, x + 110, 1086), radius=12, fill=(80, 116, 190)); d.rectangle((x + 48, 1086, x + 62, 1130), fill=(60, 66, 84))
    d.rounded_rectangle((570, 1030, 650, 1130), radius=12, fill=(246, 182, 205)); d.rectangle((598, 1006, 622, 1030), outline=(120, 90, 100), width=5)
    floor_band(d, (214, 218, 228), (184, 188, 204), edge=(170, 176, 194)); d.rectangle((0, 1260, W, 1290), fill=(250, 214, 90))
    for x in range(-100, W + 100, 150): d.line((x, HORIZON, x - 90, H), fill=(176, 180, 198), width=3)

def beach(img):
    d = ImageDraw.Draw(img); grad(d, 0, 880, (150, 200, 244), (255, 236, 240)); clouds(d, [(220, 330, 1.3), (760, 500, 0.9)])
    d.ellipse((780, 260, 940, 420), fill=(255, 226, 150))
    vgrad(d, 0, 880, W, 1040, (96, 168, 222), (150, 206, 236))
    for k, y in enumerate(range(900, 1030, 32)):
        for x in range(-40 + (k % 2) * 50, W, 100): d.arc((x, y, x + 60, y + 16), 200, 340, fill=(220, 240, 252), width=3)
    d.polygon([(300, 860), (300, 780), (360, 860)], fill=(255, 255, 255)); d.polygon([(290, 862), (380, 862), (360, 884), (310, 884)], fill=(210, 60, 70)); d.line((300, 862, 300, 772), fill=(120, 100, 90), width=4)
    vgrad(d, 0, 1010, W, H, (246, 230, 190), (224, 196, 146))
    for x in range(-20, W, 70): d.ellipse((x, 998, x + 90, 1030), fill=(236, 246, 252))
    rng = random.Random(9)
    for _ in range(70): x, y = rng.randint(0, W), rng.randint(1200, 1720); d.ellipse((x, y, x + rng.randint(8, 20), y + 6), fill=(206, 176, 128))
    tree(d, 90, 1110, 100, trunk=(150, 112, 80), leaf=(110, 176, 120))
    d.rectangle((372, 840, 388, 1140), fill=(150, 108, 76))
    for i in range(6): d.pieslice((230, 700, 530, 980), 180 + i * 30, 210 + i * 30, fill=(246, 182, 205) if i % 2 == 0 else (255, 255, 255))
    d.polygon([(300, 1100), (470, 1100), (510, 1160), (260, 1160)], fill=(246, 182, 205)); d.polygon([(285, 1126), (485, 1126), (498, 1140), (272, 1140)], fill=(255, 255, 255))
    d.ellipse((620, 1090, 690, 1160), fill=(255, 255, 255), outline=(120, 120, 140)); d.pieslice((620, 1090, 690, 1160), 0, 60, fill=(210, 60, 70)); d.pieslice((620, 1090, 690, 1160), 120, 180, fill=(60, 96, 170)); d.pieslice((620, 1090, 690, 1160), 240, 300, fill=(250, 214, 90))
    d.rectangle((822, 960, 836, 1130), fill=(150, 108, 76)); d.rectangle((954, 960, 968, 1130), fill=(150, 108, 76)); d.line((836, 1040, 954, 1040), fill=(150, 108, 76), width=6)
    d.rectangle((800, 800, 990, 960), fill=(255, 255, 255)); d.rectangle((800, 860, 990, 890), fill=(210, 60, 70)); d.rectangle((850, 812, 940, 850), fill=(196, 226, 248)); d.polygon([(780, 800), (895, 730), (1010, 800)], fill=(210, 60, 70))

def apartment(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (252, 242, 232), (246, 228, 216)); d.rectangle((0, 1070, W, HORIZON), fill=(226, 206, 190))
    d.rounded_rectangle((20, 560, 170, 1130), radius=14, fill=(150, 108, 76)); d.rounded_rectangle((38, 580, 152, 1110), radius=10, outline=(120, 84, 60), width=5); d.ellipse((136, 850, 154, 868), fill=(255, 220, 140))
    d.rounded_rectangle((690, 330, 1030, 760), radius=30, fill=(150, 108, 76)); d.rounded_rectangle((710, 350, 1010, 740), radius=20, fill=(196, 226, 248)); eiffel_tower(d, 860, 740, 300, (170, 180, 214), (196, 226, 248)); d.line((860, 350, 860, 740), fill=(150, 108, 76), width=8)
    d.polygon([(690, 330), (760, 330), (740, 760), (690, 760)], fill=(250, 214, 220)); d.polygon([(1030, 330), (960, 330), (980, 760), (1030, 760)], fill=(250, 214, 220))
    frame_art(d, 250, 420, 200, 260, 7); frame_art(d, 500, 440, 150, 150, 8, frame=(150, 108, 76))
    d.rounded_rectangle((210, 840, 640, 1010), radius=40, fill=(169, 208, 245)); d.rounded_rectangle((190, 940, 660, 1110), radius=36, fill=(150, 192, 236))
    d.rounded_rectangle((250, 960, 400, 1070), radius=24, fill=(246, 182, 205)); d.rounded_rectangle((460, 960, 600, 1070), radius=24, fill=(255, 236, 170))
    d.rounded_rectangle((170, 900, 250, 1110), radius=30, fill=(140, 184, 230)); d.rounded_rectangle((600, 900, 680, 1110), radius=30, fill=(140, 184, 230))
    for x in (220, 620): d.rectangle((x, 1110, x + 16, 1130), fill=(110, 90, 80))
    d.rounded_rectangle((700, 1020, 770, 1130), radius=10, fill=(196, 120, 90))
    for dx, dy, r in ((0, 0, 40), (-34, 18, 30), (34, 18, 30), (0, -40, 30)): d.ellipse((735 + dx - r, 980 + dy - r, 735 + dx + r, 980 + dy + r), fill=(120, 184, 128))
    counter(d, 800, W, 980, (236, 228, 218), (196, 150, 110))
    d.ellipse((930, 950, 1030, 990), fill=(255, 255, 255), outline=(200, 204, 214))
    for x, c in ((950, (210, 60, 70)), (975, (250, 190, 60)), (1000, (120, 184, 128))): d.ellipse((x, 934, x + 28, 962), fill=c)
    for x in (830, 880): d.rounded_rectangle((x, 930, x + 34, 968), radius=8, fill=(255, 255, 255), outline=(200, 204, 214))
    floor_band(d, (214, 170, 128), (190, 146, 108), edge=(150, 108, 76))
    for y in range(HORIZON + 40, H, 90): d.line((0, y, W, y), fill=(176, 134, 98), width=3)
    d.ellipse((140, 1215, 860, 1330), fill=(246, 200, 214)); d.ellipse((190, 1232, 810, 1313), outline=(255, 255, 255), width=6)

def market(img):
    d = ImageDraw.Draw(img); grad(d, 0, 700, (169, 208, 245), (255, 236, 240)); clouds(d, [(220, 330, 1.1), (850, 310, 0.9)])
    for x0, x1, col in ((0, 400, (250, 238, 214)), (400, 720, (246, 214, 206)), (720, 1080, (222, 230, 246))):
        d.rectangle((x0, 420, x1, HORIZON), fill=col); d.rectangle((x0, 380, x1, 430), fill=(112, 122, 152))
        for yy in (470, 600): 
            for xx in range(x0 + 40, x1 - 60, 110): win(d, xx, yy, 56, 90, frame=(150, 130, 120))
    d.line((0, 540, W, 540), fill=(80, 70, 90), width=3)
    cols = ((246, 182, 205), (250, 214, 90), (169, 208, 245), (184, 214, 193))
    for x in range(0, W, 70): d.polygon([(x, 540), (x + 60, 540), (x + 30, 590)], fill=cols[(x // 70) % 4])
    stalls = ((30, 360, (210, 60, 70), "くだもの"), (375, 705, (60, 150, 110), "はな"), (720, 1050, (226, 170, 40), "さかな"))
    for x0, x1, c1, label in stalls:
        d.rectangle((x0 + 8, 760, x0 + 20, HORIZON), fill=(120, 90, 70)); d.rectangle((x1 - 20, 760, x1 - 8, HORIZON), fill=(120, 90, 70))
        awning(d, x0, x1, 700, 70, c1, (255, 255, 255), 6); sign(d, (x0 + x1) // 2, 650, 230, 54, label, c1, size=32)
        counter(d, x0 + 10, x1 - 10, 1010, (176, 130, 92), (196, 150, 110))
    crate_produce(d, 60, 200, 985, (210, 60, 70), 1); crate_produce(d, 215, 335, 985, (250, 200, 60), 2)
    rng = random.Random(5)
    for bx in (405, 475, 545, 615):
        d.rectangle((bx, 962, bx + 50, 1010), fill=(196, 226, 248))
        for _ in range(5):
            fx, fy = bx + rng.randint(4, 34), 925 + rng.randint(0, 24); d.line((fx + 12, fy + 24, bx + 25, 962), fill=(80, 140, 90), width=3)
            d.ellipse((fx, fy, fx + 26, fy + 26), fill=rng.choice(((246, 182, 205), (250, 214, 90), (255, 255, 255), (185, 167, 245), (210, 60, 70))))
    for x, y in ((750, 975), (860, 975), (800, 940)): d.ellipse((x, y, x + 110, y + 38), fill=(250, 214, 110), outline=(226, 170, 40), width=3); d.ellipse((x + 10, y - 10, x + 100, y + 14), fill=(255, 232, 150))
    d.polygon([(930, 1005), (1010, 1005), (1010, 968)], fill=(250, 200, 80), outline=(226, 170, 40))
    grad(d, HORIZON, H, (214, 210, 222), (190, 186, 202)); d.rectangle((0, HORIZON, W, HORIZON + 14), fill=(170, 166, 184))
    for _ in range(90): x, y = rng.randint(0, W), rng.randint(HORIZON + 30, 1700); d.ellipse((x, y, x + 22, y + 8), outline=(176, 172, 190))

def library(img):
    d = ImageDraw.Draw(img); grad(d, 0, HORIZON, (246, 236, 222), (238, 222, 204))
    pal = ((176, 50, 70), (60, 96, 170), (240, 190, 60), (60, 150, 110), (150, 108, 76), (246, 182, 205))
    shelf(d, 20, 330, 400, 1120, 6, pal, seed=3); shelf(d, 700, 330, 1060, 1120, 6, pal, seed=5)
    d.rounded_rectangle((430, 370, 670, 830), radius=100, fill=(150, 108, 76)); d.rounded_rectangle((448, 388, 652, 812), radius=86, fill=(196, 226, 248)); d.line((550, 388, 550, 812), fill=(150, 108, 76), width=8)
    sign(d, 550, 290, 400, 70, "図書館", (120, 76, 56), (255, 220, 140), size=38)
    d.rounded_rectangle((410, 1000, 690, 1032), radius=10, fill=(176, 130, 92)); d.rectangle((430, 1032, 446, 1126), fill=(120, 90, 70)); d.rectangle((654, 1032, 670, 1126), fill=(120, 90, 70))
    for x, c in ((450, (176, 50, 70)), (500, (60, 96, 170))): d.rectangle((x, 984, x + 46, 1000), fill=c); d.rectangle((x + 4, 968, x + 44, 984), fill=lerp(c, (255, 255, 255), 0.3))
    d.rectangle((600, 960, 608, 1000), fill=(120, 90, 70)); d.polygon([(572, 960), (636, 960), (618, 928), (590, 928)], fill=(60, 150, 110))
    counter(d, 740, 1050, 1000, (150, 108, 76), (196, 150, 110)); sign(d, 895, 930, 200, 54, "かし出し", (60, 96, 170), size=30)
    floor_band(d, (206, 170, 130), (184, 148, 112), edge=(150, 118, 90))
    for x in range(-100, W + 100, 150): d.line((x, HORIZON, x - 90, H), fill=(176, 140, 104), width=3)

EXTRA = {
    "supermarket": _make("supermarket", supermarket, {"entrance": 110, "fruit stand": 400, "shelves": 660, "checkout": 920}, ["grocery", "grocery store", "store", "convenience store", "スーパー", "コンビニ"]),
    "bookstore": _make("bookstore", bookstore, {"entrance": 110, "shelves": 400, "reading corner": 720, "counter": 960}, ["book store", "bookshop", "本屋", "ほんや"]),
    "restaurant": _make("restaurant", restaurant, {"entrance": 110, "table": 330, "window table": 640, "counter": 930}, ["dining room", "ramen shop", "レストラン"]),
    "train station": _make("train station", train_station, {"entrance": 110, "ticket window": 340, "departures board": 560, "platform": 900}, ["station", "railway station", "train", "えき", "駅"]),
    "museum": _make("museum", museum, {"entrance": 110, "painting": 380, "statue": 690, "bench": 960}, ["gallery", "art museum", "美術館", "びじゅつかん"]),
    "airport": _make("airport", airport, {"entrance": 110, "check-in desk": 330, "departures board": 590, "gate": 900}, ["terminal", "departures", "空港", "くうこう"]),
    "beach": _make("beach", beach, {"palm tree": 120, "umbrella": 400, "shore": 680, "lifeguard tower": 930}, ["seaside", "coast", "うみ", "海"]),
    "apartment": _make("apartment", apartment, {"door": 100, "sofa": 400, "window": 735, "kitchen": 960}, ["home", "flat", "living room", "house", "room", "いえ", "うち", "へや", "家"]),
    "market": _make("market", market, {"fruit stall": 200, "flower stall": 540, "cheese stall": 880}, ["street market", "farmers market", "いちば", "市場"]),
    "library": _make("library", library, {"shelves": 210, "reading table": 550, "desk": 890}, ["reading room", "としょかん", "図書館"]),
    "tower": _make("tower", eiffel_view, {"steps": 130, "viewpoint": 540, "bench": 930}, ["tokyo tower", "viewpoint", "tower view", "observation deck"]),
}
