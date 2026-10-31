"""Story mode from plain dialogue.

The same script you write for Small mode (title:, optional scene:/cast:, `Mika: おはよう！ | Good morning!` lines, `vocab:` lines)
is turned into a fully directed story: the place is chosen from what the characters talk about, they enter and walk to the named
spots of that place (counter, table, bench...), move again as the conversation goes on, wave, react, and pick up / eat / drink the
food they ask for. A script that already contains stage directions (> / & / @scene) is played exactly as written.
"""
import re
from . import scenes as SC
from .config import CHARS, W
from .acting import MIN_GAP
from .parser import Script, Say, Direction, SceneChange, parse_script, ScriptError

GREET = re.compile(r"(こんにちは|おはよう|こんばんは|はじめまして|やあ|ただいま|いらっしゃい|hello|good morning|good evening|nice to meet)", re.I)
BYE = re.compile(r"(さようなら|またね|じゃあね|じゃあ、また|また明日|またあした|おやすみ|バイバイ|いってきます|いってらっしゃい|see you|bye|good night)", re.I)
THANKS = re.compile(r"(ありがとう|すごい|おいしい|いいね|やった|うれしい|たのしい|すてき|かわいい|最高|よかった|thank|great|delicious|wonderful|awesome)", re.I)
REQUEST = re.compile(r"(ください|お願い|おねがい|いただき|ほしい|欲しい|にします|おねがいします|please|i'll have|i would like|can i have)", re.I)
ITEMS = [("コーヒー", "coffee", "drinks"), ("珈琲", "coffee", "drinks"), ("おちゃ", "tea", "drinks"), ("お茶", "tea", "drinks"), ("ジュース", "juice", "drinks"),
         ("アイス", "ice cream", "eats"), ("おにぎり", "onigiri", "eats"), ("ラーメン", "ramen", "eats"), ("クロワッサン", "croissant", "eats"), ("パン", "croissant", "eats")]
ITEM_SCENES = ("bakery", "cafe", "restaurant")
ENTRANCE = ("entrance", "door")
MOVE_EVERY = 3                      # a character changes spot every 3rd line of the conversation


def _spots(scene):
    sp = SC.SCENES[scene]["spots"]
    standing = sorted(((n, x) for n, x in sp.items() if n not in ENTRANCE), key=lambda kv: kv[1])
    if len(standing) < 2: standing = sorted(sp.items(), key=lambda kv: kv[1])
    near = lambda target: min(standing, key=lambda kv: abs(kv[1] - target))
    a, b = near(W * 0.3), near(W * 0.7)
    if a[0] == b[0] or abs(a[1] - b[1]) < MIN_GAP:
        a = standing[0]; b = max(standing, key=lambda kv: abs(kv[1] - a[1]))
    return a, b, standing


def direct(script, items=True):
    """Plain dialogue -> directed Script."""
    meta, says = dict(script.meta), [e for e in script.story if isinstance(e, Say)]
    probe = Script(dict(meta), list(says), [], [], [])
    scene = SC.scene_for(probe)
    if not scene:
        raise ScriptError(f"unknown scene {meta.get('scene')!r}; use one of: auto, {', '.join(SC.SCENES)}")
    meta["scene"] = scene
    a, b, standing = _spots(scene)
    names = [n.strip() for n in meta["cast"].split(",") if n.strip()]
    if len(names) != 2 or any(n not in CHARS for n in names):
        raise ScriptError(f"Story mode cast must contain exactly two known characters; found: {', '.join(names)}")
    at = {names[0]: a, names[1]: b}                   # current spot (name, x) of each character
    first = says[0].line
    ev = [SceneChange(scene, first),
          Direction(f"{names[0]} enters left to {a[0]}", False, first),
          Direction(f"{names[1]} enters right to {b[0]}", True, first)]
    orders, rot = [], 0                                 # food/drink requests: asked at line i, bought after the reply, enjoyed after that
    for i, s in enumerate(says):
        me, other = s.speaker, [n for n in names if n != s.speaker][0]
        D = lambda text, sim=False: Direction(text, sim, s.line)
        if i == 0 and GREET.search(s.jp + " " + s.en):
            ev.append(D(f"{me} waves"))
        elif i > 0 and i % MOVE_EVERY == 0 and len(standing) > 2:
            far = [(n, x) for n, x in standing if n != at[me][0] and abs(x - at[other][1]) >= MIN_GAP + 20]
            if far:
                at[me] = far[rot % len(far)]; rot += 1
                ev.append(D(f"{me} walks to {at[me][0]}"))
        ev.append(s)
        for o in list(orders):                           # the reply came: the customer buys; one line later they enjoy it
            if o["stage"] == 0 and i == o["i"] + 1:
                ev.append(D(f"{o['who']} buys a {o['item']}")); o["stage"] = 1
            elif o["stage"] == 1 and i >= o["i"] + 2:
                ev.append(D(f"{o['who']} {o['verb']} the {o['item']}"))
                if o["verb"] == "drinks": ev.append(D(f"{o['who']} puts away the {o['item']}", True))
                orders.remove(o)
        if items and scene in ITEM_SCENES and REQUEST.search(s.jp + " " + s.en) and not any(o["who"] == me for o in orders):
            for key, item, verb in ITEMS:
                if key in s.jp:
                    orders.append(dict(who=me, item=item, verb=verb, i=i, stage=0)); break
        if i == len(says) - 1 and BYE.search(s.jp + " " + s.en):
            ev.append(D("Both wave"))
        elif THANKS.search(s.jp + " " + s.en):
            ev.append(D(f"{other} looks happy"))
        elif s.jp.rstrip().endswith(("!", "！")) and i < len(says) - 1 and not orders:
            ev.append(D(f"{other} nods"))
    return Script(meta, ev, script.vocab, script.grammar, script.quiz)


def vocab_examples(script):
    """Attach to each vocabulary word the first spoken line that contains it (used on its vocabulary card)."""
    says = [e for e in script.story if isinstance(e, Say)]
    for v in script.vocab:
        if not v.examples:
            key = re.sub(r"[。、！？!?.,\s]", "", v.term)
            ex = next(((s.jp, s.en) for s in says if key and key in re.sub(r"[。、！？!?.,\s]", "", s.jp)), None)
            if ex: v.examples = [ex]
    return script


def parse_any(text):
    """Plain dialogue (directed automatically) or a script that already has stage directions (played as written)."""
    from .acting import check
    script = parse_script(text)
    if any(isinstance(e, (Direction, SceneChange)) for e in script.story):
        check(script); return vocab_examples(script)
    directed = direct(script)
    try:
        check(directed)
    except ScriptError:                                 # a prop rule was not met: tell the story without props
        directed = direct(script, items=False); check(directed)
    return vocab_examples(directed)
