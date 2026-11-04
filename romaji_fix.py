"""Better romaji for Tiny Japanese: particles (wa/o/e), word spacing, set phrases.
Falls back to the old pykakasi behaviour if sudachipy is not installed."""
import re

_SPECIAL = {"こんにちは": "konnichiwa", "こんばんは": "konbanwa"}
_PARTICLE = {"は": "wa", "を": "o", "へ": "e"}
_COPULA = {"です", "だ", "でした", "でしょう", "だった"}
_PUNCT = {"。": ".", "、": ",", "！": "!", "？": "?", "!": "!", "?": "?", ",": ",", ".": "."}
_kks = _tok = None


def _load():
    global _kks, _tok
    if _tok is None:
        import pykakasi
        from sudachipy import dictionary, tokenizer
        _kks = pykakasi.kakasi()
        _tok = (dictionary.Dictionary().create(), tokenizer.Tokenizer.SplitMode.A)
    return _kks, _tok


def _kana_to_romaji(s):
    kks, _ = _load()
    return "".join(x["hepburn"] for x in kks.convert(s))


def to_romaji(text):
    kks, (tk, mode) = _load()
    words, glue_next, prev_pos = [], False, None
    for m in tk.tokenize(text, mode):
        surf, pos = m.surface(), m.part_of_speech()
        if not surf.strip():
            glue_next = False
            continue
        if surf in _PUNCT:
            if words:
                words[-1] += _PUNCT[surf]
            continue
        if surf in _SPECIAL:
            r = _SPECIAL[surf]
        elif pos[0] == "助詞" and surf in _PARTICLE:
            r = _PARTICLE[surf]
        else:
            r = _kana_to_romaji(m.reading_form() if m.reading_form() else surf)
        copula = pos[0] == "助動詞" and surf in _COPULA          # desu / da stay a separate word
        te_aux = pos[0] == "動詞" and pos[1] == "非自立可能" and prev_pos == ("助詞", "接続助詞") \
            and not surf.startswith("ござ")                       # tabete iru -> tabeteiru
        attach = (pos[0] == "助動詞" and not copula) or pos[0] == "接尾辞" \
            or (pos[0] == "助詞" and pos[1] == "接続助詞") or te_aux
        if glue_next and words is not None:                      # o- / go- prefix joins the next word
            words[-1] += r
            glue_next = False
        elif attach and words:
            words[-1] += r
        else:
            words.append(r)
        if pos[0] == "接頭辞":
            glue_next = True
        prev_pos = (pos[0], pos[1])
    out = " ".join(words).replace("onegai shimasu", "onegaishimasu")
    out = re.sub(r"\s+([!?,.])", r"\1", out)
    return out[:1].upper() + out[1:]
