import unittest
from tinyjp.meta import clean_caption


class CaptionGuard(unittest.TestCase):
    def test_strips_generator_notes(self):
        raw = "Train Ticket 🌸 (Your top post pattern: keep the practical scenario!)\n\nSave this 💌"
        out = clean_caption(raw)
        self.assertNotIn("top post", out); self.assertNotIn("Your", out); self.assertIn("Save this", out)

    def test_keeps_normal_parentheses(self):
        line = "• おはよう (ohayou) = good morning"
        self.assertEqual(clean_caption(line), line)


if __name__ == "__main__":
    unittest.main()
