"""Script parser for Tiny Japanese Story mode.

One format for everything (UTF-8):
  header lines      title: / episode: / scene: / cast: / cover:
  dialogue          Mika: おはよう！ | Good morning!          (optional 3rd part = romaji override; romaji is automatic)
  vocabulary        vocab: おはよう | Good morning            (or  vocab: おはよう | ohayou | Good morning)
  stage directions  > Mika walks to counter   /  & Alex nods   /  @scene cafe       (optional: plain dialogue is directed for you)
Sectioned scripts ([story] [vocab] [grammar] [quiz]) are accepted too.
"""
import re
from dataclasses import dataclass, field
from .config import CHARS

class ScriptError(Exception):
    pass

@dataclass
class Say:
    speaker: str; jp: str; en: str; romaji: str; line: int
@dataclass
class Direction:
    text: str; simultaneous: bool; line: int
@dataclass
class SceneChange:
    place: str; line: int
@dataclass
class Vocab:
    term: str; romaji: str; meaning: str; examples: list = field(default_factory=list)   # [(jp, en)]
@dataclass
class Grammar:
    pattern: str; meaning: str; examples: list = field(default_factory=list)
@dataclass
class Quiz:
    question: str; options: dict; answer: str; explanation: str
@dataclass
class Script:
    meta: dict; story: list; vocab: list; grammar: list; quiz: list

LABEL = {n.lower(): n for n in CHARS}
SECTION = re.compile(r"^\[(story|vocab|grammar|quiz)\]\s*$", re.I)
HEADER = re.compile(r"^(title|scene|episode|cover|cast|weather|format)\s*:\s*(.+)$", re.I)
SAY = re.compile(r"^([^\W\d_]+)\s*[:：]\s*(.+)$")
SEP = re.compile(r"\s+[\u2014\u2013]\s+|\s+-\s+|\s+=\s+")
OPT = re.compile(r"^([A-D])[).]\s*(.+)$")
EX = re.compile(r"^Example(?:\s*\d+)?\s*:\s*(.+)$", re.I)

def to_romaji(text):
    try:
        import tinyvideo
        return tinyvideo.to_romaji(text)
    except Exception:
        return ""

def split_cast(value):
    toks = [t for t in re.split(r"[\s,&/|+]+|\band\b", (value or "").strip(), flags=re.I) if t]
    out = []
    for t in toks:
        if t.lower() not in LABEL:
            raise ScriptError(f"unknown character {t!r} in cast:. Characters: {', '.join(CHARS)}")
        out.append(LABEL[t.lower()])
    return out

def _say(m, ln):
    who = LABEL.get(m.group(1).lower())
    if not who: return None
    parts = [p.strip() for p in m.group(2).split("|")]
    if not parts[0]:
        raise ScriptError(f"line {ln}: empty spoken line")
    en = parts[1] if len(parts) > 1 else ""
    rom = parts[2] if len(parts) > 2 and parts[2] else to_romaji(parts[0])
    return Say(who, parts[0], en, rom, ln)

def _vocab_parts(body, ln):
    p = [x.strip() for x in body.split("|")] if "|" in body else [x.strip() for x in SEP.split(body, maxsplit=1)]
    if len(p) not in (2, 3) or not all(p):
        raise ScriptError(f"line {ln}: vocab needs 'Japanese | English' (or 'Japanese | romaji | English'): {body!r}")
    return (p[0], p[1], p[2]) if len(p) == 3 else (p[0], to_romaji(p[0]), p[1])

def parse_script(text):
    """-> Script (cast already resolved). Raises ScriptError with line numbers."""
    lines = text.replace("\ufeff", "").splitlines()
    meta, sec = {}, None
    story, vocab, grammar_raw, quiz_raw = [], [], [], []
    cur = None
    for i, raw in enumerate(lines, 1):
        s = raw.strip()
        if not s or s.startswith("#"): continue
        m = SECTION.match(s)
        if m: sec = m.group(1).lower(); cur = None; continue
        if sec in ("vocab", "grammar"):
            if s.startswith(("- ", "* ")):
                body = s[2:].strip()
                if sec == "vocab":
                    t, r, mean = _vocab_parts(body, i); cur = Vocab(t, r, mean); vocab.append(cur)
                else:
                    p = SEP.split(body, maxsplit=1)
                    if len(p) < 2: raise ScriptError(f"line {i}: [grammar] entry needs 'pattern - meaning': {s!r}")
                    cur = Grammar(p[0].strip(), p[1].strip()); grammar_raw.append(cur)
                continue
            m = EX.match(s)
            if m and cur is not None:
                jp, _, en = m.group(1).partition("|"); cur.examples.append((jp.strip(), en.strip())); continue
            raise ScriptError(f"line {i}: unexpected line in [{sec}]: {s!r}")
        if sec == "quiz":
            quiz_raw.append((i, s)); continue
        # header / story area (sec None or story)
        if sec is None:
            m = HEADER.match(s)
            if m: meta[m.group(1).lower()] = m.group(2).strip(); continue
            m = re.match(r"^vocab\s*:\s*(.+)$", s, re.I)
            if m:
                t, r, mean = _vocab_parts(m.group(1), i); vocab.append(Vocab(t, r, mean)); continue
        if s.lower().startswith("@scene"):
            place = s[6:].strip()
            if not place: raise ScriptError(f"line {i}: '@scene' needs a place name")
            story.append(SceneChange(place.lower(), i)); continue
        if s.startswith(">"): story.append(Direction(s[1:].strip(), False, i)); continue
        if s.startswith("&"): story.append(Direction(s[1:].strip(), True, i)); continue
        m = SAY.match(s)
        if m:
            ev = _say(m, i)
            if ev: story.append(ev); continue
            raise ScriptError(f"line {i}: unknown speaker {m.group(1)!r}; characters: {', '.join(CHARS)}")
        raise ScriptError(f"line {i}: can't read this line (dialogue is 'Mika: Japanese | English'; directions start with > or &): {s[:70]!r}")
    if not meta.get("title"): raise ScriptError("missing 'title:' in the header")
    if not any(isinstance(e, Say) for e in story): raise ScriptError("no spoken lines (write lines like 'Mika: こんにちは！ | Hello!')")
    script = Script(meta, story, vocab[:8], grammar_raw, _parse_quiz(quiz_raw))
    assign_cast(script)
    return script

def _parse_quiz(items):
    out, cur = [], None
    def close():
        if cur is None: return
        if len(cur["options"]) < 2: raise ScriptError(f"quiz question {cur['q']!r} needs at least 2 options")
        if cur["answer"] not in cur["options"]: raise ScriptError(f"quiz question {cur['q']!r}: Answer must be one of {sorted(cur['options'])}")
        out.append(Quiz(cur["q"], cur["options"], cur["answer"], cur["exp"]))
    for ln, s in items:
        if s.upper().startswith("Q:"): close(); cur = dict(q=s[2:].strip(), options={}, answer=None, exp="")
        elif cur is None: raise ScriptError(f"line {ln}: [quiz] must start with 'Q:'")
        elif OPT.match(s): m = OPT.match(s); cur["options"][m.group(1)] = m.group(2).strip()
        elif s.lower().startswith("answer:"): cur["answer"] = s.split(":", 1)[1].strip().upper()[:1]
        elif s.lower().startswith("explanation:"): cur["exp"] = s.split(":", 1)[1].strip()
        else: raise ScriptError(f"line {ln}: unexpected line in [quiz]: {s!r}")
    close()
    return out

def assign_cast(script):
    """Resolve who is on stage, like Small mode: 'cast: kage, sayo' puts them in the left/right slots; a classic Mika:/Alex: script then
    means left/right. Without cast:, the speakers (in order of speaking) are the cast. Rewrites speakers and directions to the real names."""
    meta = script.meta
    says = [e for e in script.story if isinstance(e, Say)]
    order = list(dict.fromkeys(e.speaker for e in says))
    declared = split_cast(meta.get("cast", ""))
    if len(declared) > 2: raise ScriptError("cast: pick exactly two characters.")
    if len(declared) == 2 and declared[0] == declared[1]: raise ScriptError("cast: pick two different characters.")
    if len(order) > 2: raise ScriptError(f"Story mode has two characters per episode; this script has {len(order)} speakers: {', '.join(order)}.")
    if not declared:
        cast = list(order)
        if len(cast) == 1: cast.append("Alex" if cast[0] != "Alex" else "Mika")
        mapping = {}
    else:
        cast = list(declared)
        if len(cast) == 1: cast.append("Alex" if cast[0] != "Alex" else "Mika")
        mapping, used = {}, {n for n in order if n in cast}
        for n in order:
            if n in cast: continue
            if n in ("Mika", "Alex"): mapping[n] = cast[0 if n == "Mika" else 1]
            else:
                free = [c for c in cast if c not in used and c not in mapping.values()]
                if not free: raise ScriptError(f"{n} is not in cast: {', '.join(cast)}")
                mapping[n] = free[0]
        if len(set(mapping.values()) | {n for n in order if n in cast}) > 2:
            raise ScriptError("Every speaker must be one of the two characters in cast:.")
    if mapping:
        pat = re.compile(r"\b(" + "|".join(re.escape(k) for k in mapping) + r")\b", re.I)
        for e in script.story:
            if isinstance(e, Say): e.speaker = mapping.get(e.speaker, e.speaker)
            elif isinstance(e, Direction): e.text = pat.sub(lambda m: mapping[LABEL[m.group(1).lower()]], e.text)
    meta["cast"] = ", ".join(cast)
    return cast
