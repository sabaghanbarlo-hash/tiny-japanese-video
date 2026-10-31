"""Instagram caption (UTF-8 text, <= 2200 chars) generated from the story itself."""
HASHTAGS = ["#learnjapanese", "#japanese", "#nihongo", "#japaneselanguage", "#jlpt", "#japaneseforbeginners", "#tinyjapanese"]
LIMIT = 2200

def caption(script):
    from .acting import cast_of
    m = script.meta; lines = [f"{m['title']} 🌸", f"Learn Japanese with {' & '.join(cast_of(script)[0][:2])}, one tiny story at a time.", ""]
    if script.vocab:
        lines.append("Today's words:")
        for v in script.vocab[:5]:
            lines.append(f"• {v.term} ({v.romaji}) = {v.meaning}" if v.romaji else f"• {v.term} = {v.meaning}")
        lines.append("")
    if script.quiz: lines += ["Can you answer the quiz at the end? Tell us in the comments 👇", ""]
    lines += ["Save this to practice later! 💌", "", " ".join(HASHTAGS)]
    text = "\n".join(lines)
    if len(text) > LIMIT: text = text[:LIMIT - 1] + "…"
    return text

def write_caption(script, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f: f.write(caption(script) + "\n")
