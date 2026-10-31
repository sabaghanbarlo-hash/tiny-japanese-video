"""Story-mode reel cover (1080x1920): the lesson's scene, both characters standing apart and greeting, and a title card."""
from PIL import Image, ImageDraw
from . import scenes as SC, rig, acting
from .cover import compose

COVER_SCALE, FEET_Y = 0.92, 1630      # head tops land at ~y=990, below the title card

def make_cover(script, path):
    scene = SC.scene_for(script) or "street"
    img = SC.background(scene).convert("RGBA"); d = ImageDraw.Draw(img, "RGBA")
    base = dict(face=1, expr="happy", walking=0, phase=0, act=None, ap=0, item=None, bites=0, mouth=0.0, t=0.2)
    cast = acting.cast_of(script)[0][:2]          # the episode's own two characters
    for n, (x, face, act, ap) in zip(cast, ((330, 1, "wave", 0.3), (750, -1, None, 0))):
        spr = rig.draw(n, dict(base, face=face, act=act, ap=ap))
        spr = spr.resize((int(spr.width * COVER_SCALE), int(spr.height * COVER_SCALE)), Image.BILINEAR)
        d.ellipse((x - 150 * COVER_SCALE, FEET_Y - 18, x + 150 * COVER_SCALE, FEET_Y + 18), fill=(40, 44, 78, 60))
        img.paste(spr, (int(x - rig.CX * COVER_SCALE), int(FEET_Y - rig.FY * COVER_SCALE)), spr)
    title = script.meta.get("cover") or script.meta["title"]
    compose(img, title, script.meta.get("episode"), cy=610).save(path)
