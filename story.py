#!/usr/bin/env python3
"""Story mode: an animated Tiny Japanese Reel (1080x1920) from a script.

  python story.py stories/<name>.txt -o output          -> output/<name>.mp4, .jpg (cover), .srt, .caption.txt
  python story.py stories/<name>.txt --check            -> only check the script (line-numbered errors, nothing rendered)

The script is the same plain dialogue as Small mode (Mika: Japanese | English, vocab: lines, optional cast:) and is directed
automatically, or it can contain its own stage directions (see STORY_DIRECTING.md).
"""
import argparse, os, sys

from tinyjp.parser import ScriptError
from tinyjp.autodirect import parse_any

MAX_CHARS = 20000


def load(path):
    text = open(path, encoding="utf-8").read()
    if not text.strip():
        raise ScriptError("The script is empty.")
    if len(text) > MAX_CHARS:
        raise ScriptError(f"The script is too long ({len(text)} characters; limit {MAX_CHARS}).")
    return parse_any(text)


def fail(msg):
    print("::error title=Script problem::" + msg.replace("%", "%25").replace("\r", "").replace("\n", "%0A"))
    return 1


def main():
    ap = argparse.ArgumentParser(description="Tiny Japanese Story mode")
    ap.add_argument("script"); ap.add_argument("-o", "--out", default="output")
    ap.add_argument("--check", action="store_true", help="only validate the script")
    ap.add_argument("--preview", metavar="DIR", help="also save still frames of the video to DIR")
    ap.add_argument("--dummy-audio", action="store_true", help="TEST ONLY: tones instead of voices")
    ap.add_argument("--no-video", action="store_true", help="TEST ONLY: build the timeline and previews, do not encode")
    ap.add_argument("--sections", default="story,vocab,grammar,quiz"); ap.add_argument("--max-quiz", type=int, default=1)
    a = ap.parse_args()
    try:
        script = load(a.script)
    except ScriptError as e:
        return fail(str(e))
    if a.check:
        print(f"Script OK: {script.meta.get('title')} ({script.meta.get('cast')})"); return 0
    from tinyjp.render import render
    from tinyjp.meta import write_caption
    from tinyjp.thumb import make_cover
    if a.dummy_audio:
        print("WARNING: --dummy-audio is for tests only; the video will not have Japanese speech.", file=sys.stderr)
    stem = os.path.splitext(os.path.basename(a.script))[0]
    os.makedirs(a.out, exist_ok=True)
    info = render(script, a.out, stem, a.dummy_audio, a.preview, tuple(a.sections.split(",")), a.max_quiz, no_video=a.no_video)
    write_caption(script, os.path.join(a.out, stem + ".caption.txt"))
    try:
        make_cover(script, os.path.join(a.out, stem + ".jpg"))
    except Exception as e:                      # the video is still good; Instagram picks a frame
        print(f"::warning::cover failed: {e}", file=sys.stderr)
    tmp = os.path.join(a.out, ".tmp")
    if os.path.isdir(tmp):
        import shutil; shutil.rmtree(tmp, ignore_errors=True)
    print(info)
    return 0


if __name__ == "__main__":
    sys.exit(main())
