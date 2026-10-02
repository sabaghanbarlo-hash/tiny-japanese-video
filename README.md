# Tiny Japanese – Video Generator

Turn a short Japanese conversation into a 9:16 video (Reels / Shorts) with Mika and Alex.
Free, runs entirely on GitHub Actions – nothing to install.

## Make a video
1. Add a file in `stories/`, e.g. `02-at-the-station.txt`:

```
title: At the Station
episode: 2
scene: station        # cafe | station | sakura

Mika: おはようございます。 | Good morning.
Alex: おはよう！ | Morning!

vocab: おはようございます | ohayou gozaimasu | Good morning (polite)
```
2. Commit it. The workflow renders it automatically (or: Actions → *Generate videos* → Run workflow).
3. Download the MP4 from the `output/` folder or the run's *videos* artifact.

Romaji is generated automatically; add a third `| romaji` part to override it. Speakers: `Mika`, `Alex`.
Voices: Microsoft Edge neural Japanese voices (Nanami / Keita), slightly slowed for learners (`--rate`).
