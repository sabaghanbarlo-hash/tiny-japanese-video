# STORY_DIRECTING.md - what the Tiny Japanese engine can act out

Generated from the code (python -m tinyjp.docsgen). Everything below is implemented and tested; anything else is rejected with a line-numbered error before rendering starts.

## Script layout
- header lines: title:, episode:, scene: (first scene, or `auto` to pick the place from the story), optional cover: (short English cover title), optional `cast: Alia, Nino` (exactly two names; any of the 31 Small-mode characters)
- optional sections: [story] (dialogue and directions), [vocab], [grammar], [quiz]. Plain scripts need none of them: `vocab: おはよう | Good morning` lines at the end are enough
- Shortcut: plain dialogue (the Small-mode format: title:, optional scene:, Name: Japanese | English lines, vocab: lines, no sections) is directed automatically: place chosen from the dialogue, entrances, walking to the scene's spots, reactions, food and drinks. Vocabulary is spoken as Japanese, "means ...", Japanese.
- Spoken line: Mika: こんにちは！ | Hello!   (Japanese, a bar, English translation; an optional third field overrides the automatic romaji)
- Speakers: @@SPEAKERS@@. Each Reel uses at most two selected characters; `cast:` declares the pair and every spoken line must use one of those names. Without `cast:`, the dialogue speakers determine the pair.
- A line starting with > is a direction and starts a new beat. A line starting with & runs at the same time as the previous beat.
- @scene <place> cuts to a new scene; the selected pair starts at their home spots (first selected character left, second right) unless the next directions say enters.
- Directions never speak. Characters finish a beat before the next spoken line starts.

## Directions
Any selected character name, or Both + one of:
@@VERBS@@

Base verbs also work with Both (Both walk to counter). Targets for walks to / enters ... to: a scene spot, left, center, right, home, next to <name>, or a percentage such as 40%.
- A character whose first direction in a scene is enters starts off screen; otherwise they are already standing at home.
- Walking to a spot keeps at least a body width between the two characters; if they must pass each other, one walks behind the other.
- gives needs the giver to hold the item and the receiver to have empty hands; the giver walks over first if too far away.
- eats works on: @@EDIBLE@@. drinks works on: @@DRINK@@. Eaten food disappears; a cup stays until puts away.
- A character can hold one item at a time.

## Feelings (looks <feeling>)
@@FEELINGS@@ (also accepted: glad, smiling, puzzled, shocked, nervous, thrilled)

## Scenes
@@SCENES@@

## Objects
@@ITEMS@@

## Reel facts
- 1080x1920, 24 fps, Japanese voices: every character keeps the voice and pitch they have in Small mode.
- The video shows: title card, animated story, vocabulary cards, grammar card, one quiz question with its answer, closing card.
- Keep spoken lines short: each line is also shown as Japanese, romaji and English on screen.

## Not supported yet (do not use)
Objects: bicycle, pen, chopsticks in hand. Weather, falling petals and the 33 Small-mode backgrounds (ramen shop, shrine, snow ...): Small mode only. Story mode has the scenes listed above.

## Working example
@@EXAMPLE@@
