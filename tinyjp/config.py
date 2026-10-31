"""Tiny Japanese Story mode - shared settings (vertical Reels format, 1080x1920).

The characters are the SAME 31 as the Small videos: tinyvideo.ROSTER is the single source of truth for their
looks, names and voices, so a character can never look different in Small and Story mode.
"""
import os
import tinyvideo as T

W, H, FPS, SR = 1080, 1920, 24, 24000
# Instagram overlays the top ~220px and bottom ~380px of a Reel: keep text inside this band.
SAFE_TOP, SAFE_BOTTOM = 220, H - 380
CHAR_SCALE = 0.62          # every story scene draws the full-body characters at this scale (per-scene: scenes.SCENE_TUNING)
BODY_W = 315               # width the characters occupy (used to keep them apart)
NAVY = (52, 40, 44); LAVENDER = (240, 186, 202); BLUSH = (250, 214, 222); SKY = (169, 208, 245)
CREAM = (255, 246, 238); GREEN = (184, 214, 193); MUTED = (110, 96, 100); BRAND = (222, 110, 134); ROMA = (176, 110, 128)

CHARS = {}
for _id, _c in T.ROSTER.items():
    CHARS[_c["label"]] = dict(_c, id=_id, jacket=_c["accent"])
NARRATOR_VOICE = "en-US-AriaNeural"   # English "means ..." in the vocabulary section and quiz narration
EN_VOICE = NARRATOR_VOICE
VOICE_RATE = os.environ.get("TF_VOICE_RATE", "-12%")   # slightly slow for learners (same as Small mode)
