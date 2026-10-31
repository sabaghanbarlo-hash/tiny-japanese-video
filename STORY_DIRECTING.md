# STORY_DIRECTING.md - what the Tiny Japanese engine can act out

Generated from the code (python -m tinyjp.docsgen). Everything below is implemented and tested; anything else is rejected with a line-numbered error before rendering starts.

## Script layout
- header lines: title:, episode:, scene: (first scene, or `auto` to pick the place from the story), optional cover: (short English cover title), optional `cast: Alia, Nino` (exactly two names; any of the 31 Small-mode characters)
- optional sections: [story] (dialogue and directions), [vocab], [grammar], [quiz]. Plain scripts need none of them: `vocab: おはよう | Good morning` lines at the end are enough
- Shortcut: plain dialogue (the Small-mode format: title:, optional scene:, Name: Japanese | English lines, vocab: lines, no sections) is directed automatically: place chosen from the dialogue, entrances, walking to the scene's spots, reactions, food and drinks. Vocabulary is spoken as Japanese, "means ...", Japanese.
- Spoken line: Mika: こんにちは！ | Hello!   (Japanese, a bar, English translation; an optional third field overrides the automatic romaji)
- Speakers: Mika, Alex, Haru, Sora, Rin, Yuki, Kenji, Hana, Ryu, Kai, Aoi, Emi, Taro, Sakuya, Daichi, Kage, Sayo, Rex, Marin, Bolt, Takeru, Tomoe, Luna, Hoshi, Eldo, Mia, Noa, Rei, Mei, Gen, Zed. Each Reel uses at most two selected characters; `cast:` declares the pair and every spoken line must use one of those names. Without `cast:`, the dialogue speakers determine the pair.
- A line starting with > is a direction and starts a new beat. A line starting with & runs at the same time as the previous beat.
- @scene <place> cuts to a new scene; the selected pair starts at their home spots (first selected character left, second right) unless the next directions say enters.
- Directions never speak. Characters finish a beat before the next spoken line starts.

## Directions
Any selected character name, or Both + one of:
- enters left|right [to <spot>]
- exits left|right
- walks to <spot>
- runs to <spot>
- looks <feeling>
- looks at <name>
- faces <name|left|right>
- waves
- jumps
- laughs
- nods
- cheers
- holds <item>
- picks up <item>
- buys <item>
- eats [item]
- drinks [item]
- drops|puts away|finishes [item]
- gives <item> to <name>
- wait <seconds>

Base verbs also work with Both (Both walk to counter). Targets for walks to / enters ... to: a scene spot, left, center, right, home, next to <name>, or a percentage such as 40%.
- A character whose first direction in a scene is enters starts off screen; otherwise they are already standing at home.
- Walking to a spot keeps at least a body width between the two characters; if they must pass each other, one walks behind the other.
- gives needs the giver to hold the item and the receiver to have empty hands; the giver walks over first if too far away.
- eats works on: baguette, croissant, ice cream, macaron, onigiri, ramen. drinks works on: coffee, juice, tea. Eaten food disappears; a cup stays until puts away.
- A character can hold one item at a time.

## Feelings (looks <feeling>)
confused, embarrassed, excited, happy, neutral, sad, shy, surprised, worried (also accepted: glad, smiling, puzzled, shocked, nervous, thrilled)

## Scenes
| Scene (@scene / scene:) | Also accepted | Named spots |
|---|---|---|
| street | town, road, city, まち, みち | lamp, bench, shop window |
| bakery | bakery shop, pastry shop, パン屋 | entrance, window, counter, display |
| cafe | café, coffee shop, カフェ | entrance, table, counter |
| park | garden, こうえん, 公園 | bench, fountain |
| classroom | school, class, がっこう, 学校, きょうしつ | door, board, desk |
| metro | metro station, subway, underground, 地下鉄, ちかてつ | entrance, ticket machine, platform |
| supermarket | grocery, grocery store, store, convenience store, スーパー, コンビニ | entrance, fruit stand, shelves, checkout |
| bookstore | book store, bookshop, 本屋, ほんや | entrance, shelves, reading corner, counter |
| restaurant | dining room, ramen shop, レストラン | entrance, table, window table, counter |
| train station | station, railway station, train, えき, 駅 | entrance, ticket window, departures board, platform |
| museum | gallery, art museum, 美術館, びじゅつかん | entrance, painting, statue, bench |
| airport | terminal, departures, 空港, くうこう | entrance, check-in desk, departures board, gate |
| beach | seaside, coast, うみ, 海 | palm tree, umbrella, shore, lifeguard tower |
| apartment | home, flat, living room, house, room, いえ, うち, へや, 家 | door, sofa, window, kitchen |
| market | street market, farmers market, いちば, 市場 | fruit stall, flower stall, cheese stall |
| library | reading room, としょかん, 図書館 | shelves, reading table, desk |
| tower | tokyo tower, viewpoint, tower view, observation deck | steps, viewpoint, bench |

## Objects
croissant, baguette, macaron, coffee, juice, menu, book, notebook, bag, ticket, phone, map, umbrella, flowers, ice cream, onigiri, ramen, tea

## Reel facts
- 1080x1920, 24 fps, Japanese voices: every character keeps the voice and pitch they have in Small mode.
- The video shows: title card, animated story, vocabulary cards, grammar card, one quiz question with its answer, closing card.
- Keep spoken lines short: each line is also shown as Japanese, romaji and English on screen.

## Not supported yet (do not use)
Objects: bicycle, pen, chopsticks in hand. Weather, falling petals and the 33 Small-mode backgrounds (ramen shop, shrine, snow ...): Small mode only. Story mode has the scenes listed above.

## Working example
```
title: At the Cafe
episode: 1
scene: cafe

@scene cafe
> Mika enters left
& Alex enters right
> Mika waves
Mika: こんにちは！ | Hello!
> Alex nods
Alex: こんにちは。 | Hello.
> Mika walks to counter
Mika: コーヒーをください。 | Coffee, please.
> Mika buys a coffee
> Alex walks to counter
Alex: わたしも、コーヒーをください。 | Coffee for me too, please.
> Alex buys a coffee
> Mika drinks the coffee
Mika: おいしい！ | Delicious!
> Alex looks happy
> Both wave
Alex: またね！ | See you!

vocab: コーヒー | coffee
vocab: ください | please give me
vocab: おいしい | delicious
```
