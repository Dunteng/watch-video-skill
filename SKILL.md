---
name: watch-video
description: Use when the user asks to watch, analyze, summarize, transcribe, OCR, extract keyframes from, or make notes from a video file or URL. Triggers include Douyin, TikTok, YouTube, yt-dlp, mp4/mov, subtitles, transcript, keyframes, video report, and "this video says what". Do not use for editing, generation, playback UI, or maintaining code.
---

# Watch Video

## Overview

Use `watchvideo` to turn a video file or URL into evidence, then synthesize from the report, transcript, and keyframes.

The CLI prepares evidence, including local ASR; the Agent reads it, writes understanding, and persists it to `report.md` when requested or when the report exists.

## Routing Boundaries

Use this skill for:

- Video links or files the user wants summarized, transcribed, inspected, or converted into notes.
- Requests involving `report.md`, `report.json`, `summary-input.md`, transcripts, keyframes, OCR, or video-derived notes.
- Existing analysis directories where the user wants the Agent to finish or write back.

Do not use this skill for:

- Editing, cutting, transcoding, compressing, publishing, or generating video assets.
- Building media players, playback UI, or video processing product features.
- Debugging or extending the `watchvideo` source code; use normal coding/debugging workflows for that.
- Generic article/PDF/webpage summarization when no video artifact or `watchvideo` output is involved.

## Workflow

1. Locate the skill repo containing this `SKILL.md` and `watchvideo/cli.py`. Run CLI commands there with `python3 -m watchvideo ...`.
2. Keep analysis outputs in the user's current workspace, unless the user confirms another path. The CLI may cache `whisper.cpp` under `.tools/`. For command details, read `references/workflow.md`.
3. Run or inspect analysis, then read generated artifacts before summarizing. For artifact priority and output rules, read `references/artifacts.md`.
4. If tools, subtitles, OCR, downloads, or long-running processes fail, read `references/troubleshooting.md`.
5. When a `report.md` exists and you produce the final video understanding, write the summary into its `视频内容总结` section. You may use `scripts/update_report_summary.py`.

## Evidence Rules

- Do not summarize from the video URL, title, description, search results, or same-topic materials.
- If video/transcript/keyframe evidence cannot be produced, stop and report the blocker.
- Do not read browser cookies or login state without user confirmation.
- Prefer platform subtitles; otherwise let the CLI use system `whisper` or auto-prepare local `whisper.cpp` unless disabled.
- Use keyframes to verify slides, code, diagrams, on-screen text, and visual context.
- Mark uncertain transcription, OCR, names, dates, and technical terms as needing confirmation.
- Keep summaries concise, structured, and grounded in visible/transcribed evidence.

## Quick Reference

| Task | Read or run |
| --- | --- |
| New video analysis | `references/workflow.md` |
| Existing analysis directory | `references/artifacts.md` |
| No subtitles or bad transcript | `references/troubleshooting.md` |
| Write summary into report | `scripts/update_report_summary.py` |

## Common Mistakes

- Stopping after `analyze` without reading the evidence files.
- Treating noisy ASR text as exact quotes without caveats.
- Leaving the final summary only in chat when `report.md` is the durable output.
- Running OCR by default; enable it only when visual text matters.
