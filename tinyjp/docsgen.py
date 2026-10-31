"""Generates STORY_DIRECTING.md and STORY_DIRECTOR_PROMPT.md from the live registries, so the docs can never list something the renderer cannot do."""
import os
from . import scenes as SC, items as IT, acting
from .config import CHARS

HERE = os.path.dirname(__file__)

def _fill(tpl):
    rows = ["| Scene (@scene / scene:) | Also accepted | Named spots |", "|---|---|---|"]
    for k, v in SC.SCENES.items(): rows.append("| " + k + " | " + ", ".join(v["aliases"]) + " | " + ", ".join(v["spots"]) + " |")
    ex = open("story-examples/02-at-the-cafe.txt", encoding="utf-8").read().strip()
    rep = {"@@SPEAKERS@@": ", ".join(CHARS), "@@VERBS@@": "\n".join("- " + v for v in acting.VERB_LIST), "@@EDIBLE@@": ", ".join(sorted(IT.EDIBLE)),
           "@@DRINK@@": ", ".join(sorted(IT.DRINKABLE)), "@@FEELINGS@@": ", ".join(sorted(set(acting.EXPRS.values()))), "@@SCENES@@": "\n".join(rows),
           "@@ITEMS@@": ", ".join(IT.ITEMS), "@@EXAMPLE@@": "```\n" + ex + "\n```"}
    for k, v in rep.items(): tpl = tpl.replace(k, v)
    return tpl

def _tpl(n): return open(os.path.join(HERE, "templates", n), encoding="utf-8").read()
def directing(): return _fill(_tpl("DIRECTING.tpl.md"))
def prompt(): return _fill(_tpl("PROMPT.tpl.md"))
def example(): return open("story-examples/02-at-the-cafe.txt", encoding="utf-8").read().strip()

if __name__ == "__main__":
    open("STORY_DIRECTING.md", "w", encoding="utf-8").write(directing()); open("STORY_DIRECTOR_PROMPT.md", "w", encoding="utf-8").write(prompt()); print("docs written")
