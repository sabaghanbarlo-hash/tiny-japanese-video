# Stories Studio (Instagram Stories for Tiny Japanese)

Extends the Reels tool. Same characters, fonts, scenes and voices (`tinyvideo.py`), same Composio/Instagram connection, same GitHub Pages hosting. Nothing about the Reels workflow was changed except one additive line in `generate.yml` so a Reel render no longer wipes Story media from the Pages site.

## How it works
1. A **sequence** is one JSON file in `ig-stories/sequences/` (see `nemui-01.json`). All text lives there.
2. **Render Stories** (workflow, runs on every edit of a sequence, or by hand) draws 1080x1920 JPEG slides and an MP4 conversation clip, runs QC, and saves everything to `ig-stories/out/<id>/` (plus `manifest.json`).
3. Review at `<your pages site>/stories.html`.
4. Approve by setting `"approved": true` and `"reviewed_by": "your name"` in the JSON (optionally `"publish_at": "2026-10-20T18:00:00+03:30"`).
5. **Publish Stories** (workflow) posts approved sequences. Hourly it publishes anything whose `publish_at` has passed; by hand you can dispatch it with a sequence id (default is a dry run).

Slide types: `intro`, `word`, `convo` (video), `quiz`, `reveal`. Listening challenge and Reel-companion types are not built yet.

## Rules the code enforces
- Never publishes unless approved + `reviewed_by` set + zero QC errors.
- A slide counts as published only when Instagram returns a media id. Progress is saved in `ig-stories/posted.json`; retries resume and never double-post.
- Japanese is drawn as live text from the JSON, never baked into art. `japanese_verified` is always `false`: the QC checks only consistency (dictionary reading match, quiz answer matches the taught meaning, reveal matches quiz, audio transcript == subtitles, safe zones, clip length). Native-speaker review is yours to do.
- A clip with placeholder audio is blocked.

## Instagram API limits (why some things are manual)
Stories via the API are single image or video posts. No stickers (poll, quiz, link), no captions, no native scheduling (the hourly workflow handles timing; GitHub cron can run late). The quiz slide therefore uses plain-text A-D options ("reply with a letter"). If you want the native Quiz sticker, post that slide by hand in the app. The account must be a professional account connected through the existing Composio connection; run **Publish Stories** with `check_only=true` to see what Instagram reports.

## Costs / licences
Free: GitHub Actions + Pages (public repo), edge-tts voices (unofficial Microsoft endpoint, could change), Noto CJK fonts (OFL), Pillow/ffmpeg. No paid services.

## Next sequence
Copy `nemui-01.json`, change the id and content, commit. The renderer warns if the same target word was already used.


## Shorter sequences (optional, per sequence)
Retention drops with every extra frame, so a sequence can leave a slide out: add `"skip": true` to that slide in the JSON.
A skipped slide is not rendered or posted (remaining slides are renumbered), but it still feeds the QC checks, so the quiz/reveal consistency rules keep working.
Suggested 4-frame order: `intro` -> `convo` (video) -> `quiz` -> `reveal`, with the `word` slide skipped and its example sentence moved into the reveal slide's `note` lines.
Add a `"teaser"` to the reveal slide (e.g. `"Tomorrow: 古い (old)"`) to give people a reason to come back.
Existing sequences are unchanged unless you edit them.
