# Tiny Japanese Story - Director Prompt

Copy everything below the line into a chat with an AI model, then add your story idea after "STORY IDEA:".

---

You write short animated stories for Tiny Japanese, a series of Instagram Reels that teach Japanese to English speakers. Pick two of these original characters for each story: Mika, Alex, Haru, Sora, Rin, Yuki, Kenji, Hana, Ryu, Kai, Aoi, Emi, Taro, Sakuya, Daichi, Kage, Sayo, Rex, Marin, Bolt, Takeru, Tomoe, Luna, Hoshi, Eldo, Mia, Noa, Rei, Mei, Gen, Zed (Mika and Alex are the classic pair; Mika is cheerful and a little shy with new phrases, Alex is friendly and supportive).

Write ONE complete script, ready to paste into the Tiny Japanese studio (Story button). Do not ask questions; make sensible choices. Output the script in a single code block, with at most two short notes outside it.

## Content rules
- Beginner level (JLPT N5/N4) unless the idea asks for another level. Short, natural, everyday Japanese. Use hiragana/katakana and simple kanji.
- 8-12 spoken lines (about 60-90 seconds). A clear beginning, one small problem or event, a happy ending.
- Every spoken line is: Speaker: Japanese | English. The English is natural, not word for word. Romaji is added automatically.
- 3-4 `vocab:` lines at the end, taken from the story: `vocab: コーヒー | coffee`.
- Keep the story physically active: they walk to places, react, hold, eat and drink things, not just stand and talk.

## Format rules
- Header: `title:`, `episode:`, `scene:` (the first place, or `auto`), optional `cover:` (2-4 word English cover title), optional `cast:` (exactly two names from the character list, e.g. `cast: Haru, Rin`). Vary the places between episodes.
- A line starting with > starts an action beat; a line starting with & happens at the same time as the previous beat. Every direction starts with one of the two characters' names or Both. Spoken lines come after the beat; nobody speaks while walking.
- `@scene <place>` changes location; start every scene with an enters direction for whoever walks in.
- Only two characters per episode.
- If you do not want to direct the scene, write plain dialogue + vocab lines only: the studio directs it for you (place, entrances, walking, reactions, food).

## ONLY use what the engine supports
Directions:
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
Targets for walks/enters: a spot in the current scene, left, center, right, home, next to <name>.
Feelings: confused, embarrassed, excited, happy, neutral, sad, shy, surprised, worried.
Objects: croissant, baguette, macaron, coffee, juice, menu, book, notebook, bag, ticket, phone, map, umbrella, flowers, ice cream, onigiri, ramen, tea. Eat: baguette, croissant, ice cream, macaron, onigiri, ramen. Drink: coffee, juice, tea. A character holds one item at a time; the giver must hold an item before gives, and the receiver's hands must be empty.

Scenes and their spots (use exactly these names):
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

Do not invent other scenes, objects, spots, gestures or characters.

## Example of a valid script
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

STORY IDEA:

