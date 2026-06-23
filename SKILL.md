---
name: watch-video
description: Use when the user asks to watch, analyze, summarize, transcribe, OCR, extract keyframes from, or turn a local video file or video URL into a structured report, Chinese summary, interview-answer note, learning note, or Obsidian note. Triggers include Douyin, TikTok, YouTube, yt-dlp links, mp4/mov files, subtitles, transcript, keyframes, video report, and "this video says what". Do not use for video editing, video generation, playback UI, or maintaining the watchvideo codebase itself.
---

# Watch Video

## Overview

Use the `watchvideo` CLI to turn a local video file or supported video URL into Agent-readable materials, then synthesize a grounded summary from the generated report, transcript, and keyframes.

The core boundary: the CLI prepares evidence; the Agent reads that evidence, writes the final understanding, and persists it back to the report when requested or when a report file exists.

## Routing Boundaries

Use this skill for:

- Video links or local video files the user wants summarized, transcribed, inspected, or converted into notes.
- Requests involving `report.md`, `report.json`, `summary-input.md`, `transcript/*.srt`, `keyframes/`, OCR, or video-derived learning/interview notes.
- Existing `watchvideo` analysis directories where the user wants the Agent to finish, improve, or write back the video summary.

Do not use this skill for:

- Editing, cutting, transcoding, compressing, publishing, or generating video assets.
- Building media players, frontend playback UI, or video processing product features.
- Debugging or extending the `watchvideo` source code; use normal coding/debugging workflows for that.
- Generic article/PDF/webpage summarization when no video artifact or `watchvideo` output is involved.

## Workflow

1. Locate the CLI. Prefer `python3 -m watchvideo` inside a checkout that contains `watchvideo/cli.py`; otherwise try `watchvideo` on `PATH`. On this machine, if needed, check `/Users/dt/WORK/watchVideo`.
2. Run or inspect analysis. For command details, read `references/workflow.md`.
3. Read the generated artifacts before summarizing. For artifact priority and output rules, read `references/artifacts.md`.
4. If tools, subtitles, OCR, downloads, or long-running processes fail, read `references/troubleshooting.md`.
5. When a `report.md` exists and you produce the final video understanding, write the summary into its `视频内容总结` section. You may use `scripts/update_report_summary.py`.

## Evidence Rules

- Do not summarize from the video URL alone.
- Prefer platform subtitles when available; otherwise use local transcription if configured.
- Use keyframes to verify slides, code, diagrams, on-screen text, and visual context.
- Mark uncertain transcription, OCR, names, dates, and technical terms as needing confirmation.
- Keep final summaries concise, structured, and grounded in visible/transcribed evidence.

## Quick Reference

| Task | Read or run |
| --- | --- |
| New video analysis | `references/workflow.md` |
| Existing analysis directory | `references/artifacts.md` |
| No subtitles or bad transcript | `references/troubleshooting.md` |
| Write summary into report | `scripts/update_report_summary.py` |

## Common Mistakes

- Stopping after `analyze` without reading `summary-input.md`, transcript, or keyframes.
- Treating noisy ASR text as exact quotes without caveats.
- Leaving the final summary only in chat when `report.md` is the durable output.
- Running OCR by default on every video; enable it only when visual text matters.
