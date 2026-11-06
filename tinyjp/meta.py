"""Instagram caption (UTF-8 text, <= 2200 chars) generated from the story itself."""
HASHTAGS = ["#learnjapanese", "#japanese", "#nihongo", "#japaneselanguage", "#jlpt", "#japaneseforbeginners", "#tinyjapanese"]
LIMIT = 2200

import re
_NOTE = re.compile(r"[ \t]*\((?:your|this is your|keep|note|tip|top post|best post)[^)]*\)", re.I)

def clean_caption(text):
    """Drop stray generator notes such as '(Your top post pattern: ...)' so they never reach Instagram."""
    text = _NOTE.sub("", text)
    return re.sub(r"[ \t]+\n", "\n", text).strip()


def caption(script):
    from .acting import cast_of
    m = script.meta; lines = [f"{m['title']} in Japanese 🌸 Say it like this 👇", ""]
    if script.vocab:
        lines.append("Today's words:")
        for v in script.vocab[:5]:
            lines.append(f"• {v.term} ({v.romaji}) = {v.meaning}" if v.romaji else f"• {v.term} = {v.meaning}")
        lines.append("")
    if script.quiz: lines += ["Quiz at the end: can you get it? 🧠", ""]
    lines += ["Send this to someone learning Japanese 💌", "Save it to practice later 📌", "", f"Learn Japanese with {' & '.join(cast_of(script)[0][:2])}, one tiny story at a time.", "", " ".join(HASHTAGS)]
    text = "\n".join(lines)
    if len(text) > LIMIT: text = text[:LIMIT - 1] + "…"
    return text

def write_caption(script, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f: f.write(caption(script) + "\n")
