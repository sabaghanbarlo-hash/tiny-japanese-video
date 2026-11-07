import os, re, sys, tempfile, unittest
sys.path.insert(0, ".")
import tinyvideo

GREETING = re.compile(r"^\W*(こんにちは|おはよう(ございます)?|こんばんは|はじめまして|いらっしゃいませ)\W*$")


def example_script():
    md = open("SMALL_DIRECTOR_PROMPT.md", encoding="utf-8").read()
    return re.search(r"## Example script\n```\n(.*?)\n```", md, re.S).group(1)


class SmallPrompt(unittest.TestCase):
    def test_example_is_valid_and_follows_the_opening_rule(self):
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "ex.txt"); open(p, "w", encoding="utf-8").write(example_script())
            meta, lines, vocab = tinyvideo.parse_story(p)
        self.assertFalse(GREETING.match(lines[0]["jp"]), "the example must not open with a bare greeting")
        self.assertTrue(5 <= len(lines) <= 8, len(lines))
        self.assertTrue(3 <= len(vocab) <= 4, len(vocab))
        self.assertTrue(3 <= len(meta["title"].split()) <= 6, meta["title"])

    def test_caption_example_has_no_comment_ask(self):
        md = open("SMALL_DIRECTOR_PROMPT.md", encoding="utf-8").read()
        cap = re.search(r"## Example caption\n```\n(.*?)\n```", md, re.S).group(1)
        self.assertNotIn("omment", cap); self.assertIn("Send this", cap); self.assertLessEqual(len(cap), 2200)


if __name__ == "__main__":
    unittest.main()
