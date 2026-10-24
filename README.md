# Tiny Japanese – Video Generator

Turn a short Japanese conversation into a 9:16 video (Reels / Shorts) with Mika and Alex.
Free, runs entirely on GitHub Actions – nothing to install.

## Make a video
1. Add a file in `stories/`, e.g. `02-at-the-station.txt`:

```
title: At the Station
episode: 2
scene: auto           # auto (picked from the story) or: cafe station sakura restaurant store bookstore classroom home airport street park beach hospital
                      # new: ramen shrine fuji matsuri arcade aquarium onsen snow bakery rainy
                      #      karaoke rooftop izakaya commute sushi bamboo autumn castle sunset flowers
weather: auto         # optional: petals leaves snow rain wind none (auto = from the scene / story words)

Mika: おはようございます。 | Good morning.
Alex: おはよう！ | Morning!

vocab: おはようございます | ohayou gozaimasu | Good morning (polite)
```
2. Commit it. The workflow renders it automatically (or: Actions → *Generate videos* → Run workflow).
3. Download the MP4 from the `output/` folder or the run's *videos* artifact.

Romaji is generated automatically; add a third `| romaji` part to override it. Speakers: `Mika`, `Alex`.
Voices: Microsoft Edge neural Japanese voices (Nanami / Keita), slightly slowed for learners (`--rate`).

## Backgrounds & weather
33 hand-drawn scenes (Pillow, no image files). Auto-pick matches keywords in the title and dialogue (e.g. ラーメン -> `ramen`, 花火 / festival -> `matsuri`, 雪 / snow -> `snow`).
Aliases also work: `scene: temple`, `hot spring`, `mt fuji`, `game center`, `bread`, `rain`, `subway`, `pub`, `himeji`, `riverside`, `sunflower` ...

Outdoor scenes have animated weather drawn over them (some in front of Mika & Alex, some behind):
petals (sakura, fuji, castle), maple leaves (shrine, autumn), green bamboo leaves, snow, rain with ground splashes, wind streaks with blowing leaves (park, beach, station, rooftop, sunset, flowers), bubbles (aquarium), embers (matsuri).
Fallen petals / leaves also lie on the ground. Weather words in an outdoor story override the default (a rainy day at the park gets rain); force it with `weather: snow`, or turn it off with `weather: none`.

Preview one frame: `python tinyvideo.py stories/xxx.txt --dummy-audio --preview out.png`. Contact sheets: `docs/new-backgrounds.jpg` and `docs/new-backgrounds-2.jpg`.

## Characters
15 original anime-style characters (all drawn in code): Mika, Alex, Haru, Sora, Rin, Yuki, Kenji, Hana, Ryu, Kai, Aoi, Emi, Taro, Sakuya, Daichi. Portraits: `docs/characters.jpg`.
Pick two on the site, or add a line to the story: `cast: haru, rin` (left, right).
`Mika:` always means the left character and `Alex:` the right one; you can also write the character's own name (`Haru: ...`).
Each character has their own look, name tag and voice pitch (the two natural Japanese voices, shifted up or down).
Add your own: copy a `char(...)` entry in `ROSTER` (tinyvideo.py) and run `python portraits.py` to refresh the portraits.
