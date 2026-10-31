"""Story-mode characters: the SAME drawing as the Small videos (tinyvideo.render_char: same hair, eyes, outfit, accessories),
with the arms taken off, a pair of legs added underneath, animated arms/hands, and the Story expressions.
One sprite per character: poses only change legs, arms, face and held item.

draw(name, P) -> RGBA sprite SWxSH, feet at FY, body centred on CX.
P: face(+1/-1), expr, walking(0..1), phase, act, ap, item, bites, mouth(0..1), t
"""
import functools, math
from PIL import Image, ImageDraw
from .config import CHARS
from . import items as IT
import tinyvideo as T

SW, SH, CX, FY = 840, 1040, 420, 960
K = 1.2                       # story size of the Small sprite
HIP = FY - 190                # torso bottom when standing
TORSO_LOCAL = 690 * 0.9 * K   # torso bottom inside the resized sprite (design y 690)
CENTER_LOCAL = 280 * 0.9 * K  # body centre inside the resized sprite
SHOULDER = 227                # shoulder height above the hip
HALF = 103                    # shoulder offset from the body centre
EXPR_OK = ("neutral", "happy", "excited", "surprised", "sad", "worried", "confused", "embarrassed", "shy", "laugh")
LEGS = {"sailor": (52, 68, 132), "kimono": (86, 70, 96), "gi": (60, 60, 70), "samurai": (70, 66, 90), "ninja": None, "pirate": (86, 64, 52),
        "chef": (70, 72, 82), "labcoat": (76, 86, 106), "blazer": (46, 52, 74), "trench": (74, 66, 58), "magical": (255, 244, 250), "robe": (60, 46, 90)}

def _shade(c, f): return tuple(int(v * f) for v in c)

def legs_of(c):
    col = LEGS.get(c["outfit"], "x")
    if col is None: return _shade(c["top"], 0.9)
    if col == "x": return _shade(c["top"], 0.52)
    return col

def shoes_of(c): return (60, 52, 58) if c["outfit"] in ("ninja", "pirate", "samurai", "gi", "blazer", "trench") else (250, 246, 240)

@functools.lru_cache(maxsize=48)
def _body(cid, level, blink, expr):
    im = T.render_char(T.ROSTER[cid], level, blink, arms=False, expr=expr)
    return im.resize((int(im.width * K), int(im.height * K)), Image.LANCZOS)

def _level(m): return 0 if m < 0.15 else (1 if m < 0.55 else 2)

def _arm(d, sx, sy, hx, hy, col, skin, side, w=50):
    ex, ey = sx + (hx - sx) * 0.5 + side * 14, sy + (hy - sy) * 0.5 + 6
    d.line((sx, sy, ex, ey), fill=col, width=w); d.line((ex, ey, hx, hy), fill=col, width=w - 6)
    d.ellipse((sx - w // 2, sy - w // 2, sx + w // 2, sy + w // 2), fill=col); d.ellipse((ex - w // 2 + 3, ey - w // 2 + 3, ex + w // 2 - 3, ey + w // 2 - 3), fill=col)
    d.ellipse((hx - 27, hy - 27, hx + 27, hy + 27), fill=skin)

def draw(name, P):
    c = CHARS[name]; img = Image.new("RGBA", (SW, SH), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    act, ap, t = P["act"], P["ap"], P["t"]; expr = P["expr"] if P["expr"] in EXPR_OK else "neutral"
    walk = P["walking"]; ph = P["phase"]
    dy = 0.0; low = 0
    if walk: dy -= 9 * abs(math.sin(ph))
    if act == "jump": dy -= 150 * math.sin(math.pi * ap)
    elif act == "hop": dy -= 46 * math.sin(math.pi * ap)
    elif act == "cheer": dy -= 46 * abs(math.sin(2 * math.pi * ap * 2))
    elif act == "laugh": dy -= 8 * abs(math.sin(ap * 30)); expr = "laugh"
    elif act == "bend": low = int(46 * math.sin(math.pi * ap))
    if act == "nod": dy += 14 * math.sin(2 * math.pi * ap * 2)
    if P["mouth"] > 0.1: dy += 2 * math.sin(t * 22)
    y = FY + dy; hip = HIP + dy + low
    cx = CX
    d.ellipse((cx - 120, FY - 14, cx + 120, FY + 22), fill=(0, 0, 0, 46))
    s = math.sin(ph) * walk
    trouser, shoe, skin = legs_of(c), shoes_of(c), c["skin"]
    arm_col = c["arm"] or c["top"]
    for side in (-1, 1):
        sw = s * 48 * (1 if side > 0 else -1); lift = max(0, math.sin(ph + (0 if side > 0 else math.pi))) * 22 * walk
        hx, hyp = cx + side * 46, hip - 20; fx, fyp = cx + side * 46 + sw, y - 14 - lift
        d.line((hx, hyp, fx, fyp), fill=trouser, width=62); d.ellipse((hx - 31, hyp - 31, hx + 31, hyp + 31), fill=trouser)
        d.rounded_rectangle((fx - 40 + 6, fyp - 8, fx + 40 + 6, fyp + 26), radius=14, fill=shoe)
    shy = hip - SHOULDER
    sx0 = cx - HALF; bx, by = sx0 - 12 - s * 6, shy + 178 + s * 22 + low
    if act == "cheer": bx, by = sx0 - 56, shy - 150 + 22 * math.sin(ap * 40)
    if act == "jump": bx, by = sx0 - 66, shy - 40
    _arm(d, sx0, shy, bx, by, arm_col, skin, -1)
    blink = (int(t * 1000) % 3300) < 120
    body = _body(c["id"], _level(P["mouth"]), blink and expr != "laugh", expr)
    img.paste(body, (int(cx - CENTER_LOCAL), int(hip - TORSO_LOCAL)), body)
    d = ImageDraw.Draw(img)
    sx1 = cx + HALF; item = P["item"]
    hx, hyy = sx1 + 12 + s * 6, shy + 178 - s * 22 + low
    mouth_pt = (cx, int(hip - TORSO_LOCAL + 415 * 0.9 * K))
    if item and act not in ("eat", "drink", "give", "wave", "cheer", "jump"): hx, hyy = sx1 + 66, shy + 112
    if act == "wave": hx, hyy = sx1 + 66 + 26 * math.sin(ap * 2 * math.pi * 3), shy - 170
    elif act == "cheer": hx, hyy = sx1 + 58, shy - 150 + 22 * math.sin(ap * 40)
    elif act == "jump": hx, hyy = sx1 + 66, shy - 40
    elif act == "give": u = math.sin(math.pi * min(1.0, ap)); hx, hyy = sx1 + 40 + 150 * u, shy + 80
    elif act in ("eat", "drink"):
        q = (ap * (3 if act == "eat" else 1.2)) % 1.0; u = math.sin(math.pi * q)
        hx, hyy = sx1 + 66 + (mouth_pt[0] - sx1 - 66) * u, shy + 112 + (mouth_pt[1] + 30 - shy - 112) * u
    elif act == "bend": hx, hyy = sx1 + 86, shy + 170 + 60 * math.sin(math.pi * ap)
    _arm(d, sx1, shy, hx, hyy, arm_col, skin, 1)
    if item:
        IT.draw(d, item, int(hx + 28), int(hyy - 34), P["bites"])
        d.ellipse((hx - 27, hyy - 27, hx + 27, hyy + 27), fill=skin)
    if P["face"] < 0: img = img.transpose(Image.FLIP_LEFT_RIGHT)
    return img
