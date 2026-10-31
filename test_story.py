"""Story mode tests (python -m unittest test_story -v). No network, no ffmpeg, no voices needed."""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import tinyvideo as T
from tinyjp import acting, scenes, rig, render as R, config as C, docsgen
from tinyjp.autodirect import parse_any
from tinyjp.parser import parse_script, ScriptError, Say, Direction
from tinyjp.meta import caption

PLAIN = open("story-examples/01-at-the-cafe-plain.txt", encoding="utf-8").read()
DIRECTED = open("story-examples/02-at-the-cafe.txt", encoding="utf-8").read()
BASE = dict(face=1, expr="neutral", walking=0, phase=0, act=None, ap=0, item=None, bites=0, mouth=0.0, t=0.5)


class Parsing(unittest.TestCase):
    def test_plain_script(self):
        s = parse_script(PLAIN)
        says = [e for e in s.story if isinstance(e, Say)]
        self.assertEqual(len(says), 8); self.assertEqual(s.meta["cast"], "Mika, Alex")
        self.assertEqual([v.term for v in s.vocab], ["コーヒー", "ください", "おいしい"])
        self.assertTrue(all(isinstance(e, Say) for e in s.story))      # no directions yet: autodirect adds them

    def test_third_field_overrides_romaji(self):
        s = parse_script("title: T\nMika: こんにちは | Hello | KON-nichi-wa\n")
        self.assertEqual(s.story[0].romaji, "KON-nichi-wa")

    def test_cast_maps_mika_alex_to_left_right(self):
        s = parse_script("title: T\ncast: kage, sayo\nMika: はい | Yes\nAlex: いいえ | No\n> Mika nods\n")
        self.assertEqual([e.speaker for e in s.story if isinstance(e, Say)], ["Kage", "Sayo"])
        self.assertEqual([e.text for e in s.story if isinstance(e, Direction)], ["Kage nods"])
        self.assertEqual(s.meta["cast"], "Kage, Sayo")

    def test_real_names_without_cast(self):
        s = parse_script("title: T\nHaru: はい | Yes\nRin: いいえ | No\n")
        self.assertEqual(s.meta["cast"], "Haru, Rin")

    def test_single_speaker_gets_silent_partner(self):
        s = parse_script("title: T\nMika: はい | Yes\n"); self.assertEqual(s.meta["cast"], "Mika, Alex")

    def test_errors_have_line_numbers(self):
        for text, frag in (("title: T\nBob: hi | hi\n", "line 2"), ("title: T\nMika: はい | Yes\nhello there\n", "line 3"),
                           ("Mika: はい | Yes\n", "title"), ("title: T\ncast: nobody, mika\nMika: a | a\n", "unknown character"),
                           ("title: T\nMika: a | a\nAlex: b | b\nHaru: c | c\n", "two characters")):
            with self.assertRaises(ScriptError, msg=text) as cm: parse_script(text)
            self.assertIn(frag, str(cm.exception))

    def test_sectioned_script(self):
        s = parse_script("title: T\n[story]\nMika: はい | Yes\n[vocab]\n- はい — yes\n- いいえ | iie | no\n[grammar]\n- A は B です — A is B\nExample: わたしはミカです。 | I am Mika.\n")
        self.assertEqual(len(s.vocab), 2); self.assertEqual(s.vocab[1].romaji, "iie"); self.assertEqual(len(s.grammar[0].examples), 1)

    def test_small_mode_accepts_format_header(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f: f.write("format: story\n" + PLAIN)
        meta, lines, vocab = T.parse_story(f.name); os.unlink(f.name)
        self.assertEqual(meta["format"], "story"); self.assertEqual(len(lines), 8)


class Directing(unittest.TestCase):
    def test_plain_dialogue_is_directed_and_valid(self):
        s = parse_any(PLAIN)
        dirs = [e.text for e in s.story if isinstance(e, Direction)]
        self.assertTrue(any("enters left" in d for d in dirs)); self.assertTrue(any("buys a coffee" in d for d in dirs))
        self.assertTrue(any("waves" in d for d in dirs))
        acting.check(s)

    def test_directed_script_is_played_as_written(self):
        s = parse_any(DIRECTED); self.assertEqual(sum(isinstance(e, Direction) for e in s.story), 11)

    def test_unknown_direction_is_a_line_error(self):
        with self.assertRaises(ScriptError) as cm: parse_any("title: T\nscene: cafe\n> Mika flies to the moon\nMika: はい | Yes\n")
        self.assertIn("line 3", str(cm.exception))

    def test_every_scene_can_be_acted_in(self):
        for k, v in scenes.SCENES.items():
            lines = ["title: Test " + k, "scene: " + k, "@scene " + k, "> Mika enters left", "& Alex enters left", "Mika: はい | Yes"]
            for i, sp in enumerate(v["spots"]):
                who = "Mika" if i % 2 == 0 else "Alex"; lines += [f"> {who} walks to {sp}", f"{who}: はい | Yes"]
            acting.check(parse_script("\n".join(lines) + "\n"))

    def test_scene_chosen_from_japanese_words(self):
        for text, scene in (("えきで でんしゃを まっています", "train station"), ("コーヒーをください", "cafe"), ("ラーメンを ちゅうもんします", "restaurant"),
                            ("こうえんを さんぽします", "park"), ("うみで およぎます", "beach")):
            s = parse_script(f"title: T\nMika: {text} | x\n"); self.assertEqual(scenes.scene_for(s), scene, text)

    def test_all_characters_can_be_cast(self):
        for name in C.CHARS:
            other = "Alex" if name != "Alex" else "Mika"
            s = parse_any(f"title: T\ncast: {name}, {other}\nscene: park\n{name}: こんにちは！ | Hello!\n{other}: こんにちは！ | Hello!\n")
            self.assertEqual(s.meta["cast"], f"{name}, {other}")


class Drawing(unittest.TestCase):
    def test_every_character_fits_the_canvas_in_every_pose(self):
        for n in C.CHARS:
            for kw in (dict(), dict(expr="happy", mouth=0.9), dict(walking=1, phase=1.0), dict(act="wave", ap=0.4), dict(act="eat", ap=0.3, item="onigiri"), dict(face=-1, expr="surprised")):
                im = rig.draw(n, dict(BASE, **kw)); bb = im.getbbox()
                self.assertEqual(im.size, (rig.SW, rig.SH)); self.assertIsNotNone(bb, (n, kw))
                self.assertTrue(bb[0] >= 0 and bb[2] <= rig.SW and bb[1] >= 0 and bb[3] <= rig.SH, (n, kw, bb))

    def test_extreme_poses_fit_the_canvas(self):
        for kw in (dict(act="jump", ap=0.5), dict(act="bend", ap=0.5), dict(act="cheer", ap=0.3), dict(act="laugh", ap=0.2), dict(act="give", ap=0.5, item="book")):
            bb = rig.draw("Rex", dict(BASE, **kw)).getbbox(); self.assertTrue(bb[0] >= 0 and bb[2] <= rig.SW and bb[1] >= 0 and bb[3] <= rig.SH, (kw, bb))

    def test_all_expressions_differ_from_neutral(self):
        base = np.asarray(rig.draw("Mika", BASE))
        for e in ("happy", "excited", "surprised", "sad", "worried", "confused", "embarrassed", "shy"):
            self.assertTrue((np.asarray(rig.draw("Mika", dict(BASE, expr=e))) != base).any(), e)

    def test_story_head_is_the_small_mode_head(self):
        """Story sprite = Small-mode sprite with the arms removed: everything above the arms is pixel-identical."""
        for cid in ("mika", "alex", "kage"):
            a = np.asarray(T.render_char(T.ROSTER[cid], 0, False)); b = np.asarray(T.render_char(T.ROSTER[cid], 0, False, arms=False))
            self.assertEqual(a.shape, b.shape); self.assertTrue((a[:420] == b[:420]).all(), cid + ": head area changed")

    def test_small_mode_sprites_unchanged_by_story_options(self):
        a = T.render_char(T.ROSTER["mika"], 1, False); b = T.render_char(T.ROSTER["mika"], 1, False, arms=True, expr="neutral")
        self.assertTrue((np.asarray(a) == np.asarray(b)).all())

    def test_scenes_render_vertical_and_not_blank(self):
        for k in scenes.SCENES:
            im = scenes.background(k); self.assertEqual(im.size, (1080, 1920), k)
            self.assertGreater(float(np.asarray(im.convert("L"), dtype=float).std()), 15, k + " looks blank")

    def test_japanese_text_has_real_glyphs(self):
        f = T.font(60)
        a = Image.new("L", (400, 100)); ImageDraw.Draw(a).text((10, 10), "こんにちは", font=f, fill=255)
        b = Image.new("L", (400, 100)); ImageDraw.Draw(b).text((10, 10), "\uffff\uffff\uffff\uffff\uffff", font=f, fill=255)
        self.assertTrue((np.asarray(a) != np.asarray(b)).any(), "Japanese font missing (install fonts-noto-cjk)")

    def test_long_lines_stay_inside_the_subtitle_panel(self):
        img = Image.new("RGBA", (1080, 1920)); d = ImageDraw.Draw(img)
        jp = "きょうは、ともだちといっしょに、とても大きなこうえんへいって、おいしいおべんとうをたべました。"
        en = "Today I went to a very big park with my friend and we ate a delicious lunch together outside."
        y = R.stack(d, 540, 1292, [(jp, 58, C.NAVY, True, 2), (T.to_romaji(jp), 32, C.ROMA, False, 2), (en, 38, C.MUTED, False, 2)], maxh=C.SAFE_BOTTOM + 8 - 1292)
        self.assertLessEqual(y, C.SAFE_BOTTOM + 20)

    def test_render_timeline_with_dummy_audio(self):
        with tempfile.TemporaryDirectory() as out:
            for text in (PLAIN, DIRECTED):
                s = parse_any(text); info = R.render(s, out, "t", dummy=True, preview=out + "/f", no_video=True)
                self.assertGreater(info["seconds"], 20); self.assertTrue(os.path.exists(out + "/f/00-title.png"))
                self.assertTrue(os.path.exists(out + "/t.srt"))

    def test_caption(self):
        c = caption(parse_any(PLAIN)); self.assertIn("#learnjapanese", c); self.assertLessEqual(len(c), 2200); self.assertIn("コーヒー", c)


class Docs(unittest.TestCase):
    def test_generated_docs_are_current(self):
        self.assertEqual(open("STORY_DIRECTING.md", encoding="utf-8").read(), docsgen.directing())
        self.assertEqual(open("STORY_DIRECTOR_PROMPT.md", encoding="utf-8").read(), docsgen.prompt())


if __name__ == "__main__":
    unittest.main()
