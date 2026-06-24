# watchvideo

[English](README.md) | [中文](README.zh-CN.md)

**Evidence-first video understanding skill for Codex.**

`watchvideo` is a **Codex skill plus a local video-analysis CLI**. It turns local video files or video URLs into verifiable evidence, then lets Codex summarize from reports, transcripts, OCR, and keyframes. If it cannot produce video evidence, the agent should stop and explain the blocker instead of guessing from the title, description, or search results.

**Boundary:** the CLI prepares evidence; the agent reads that evidence and writes the final understanding. This project does not call a cloud LLM by itself, and it is not a video editor, transcoder, publisher, or player.

## Why This Exists

General-purpose agents often take a shortcut when asked to summarize a video: they read the URL, page title, description, or search results and produce a plausible answer. That is useful-looking, but it is not video understanding.

`watchvideo` closes that shortcut. It requires the workflow to first download or read the video, obtain subtitles or local transcription, extract keyframes, optionally run OCR, and then write evidence packages that an agent can inspect.

Use it when you want to:

- summarize technical talks, interview-prep videos, tutorials, demos, or product walkthroughs;
- keep traceable `report.md` and `summary-input.md` files instead of only a chat answer;
- debug Douyin/TikTok/YouTube download failures with explicit diagnostics;
- share a reusable, testable agent skill instead of a one-off prompt.

## Quick Start

Install the skill into Codex:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/Dunteng/watch-video-skill ~/.codex/skills/watch-video
cd ~/.codex/skills/watch-video
python3 -m watchvideo doctor
```

Restart your Codex session so `$watch-video` is discovered, then ask:

```text
Use $watch-video to summarize this video: https://example.com/video
```

Chinese prompts work too:

```text
用 $watch-video 总结这个视频：https://example.com/video
```

The CLI prepares evidence. Codex reads the artifacts and writes the final summary. Example outputs:

- [examples/technical-interview-summary.en.md](examples/technical-interview-summary.en.md)
- [examples/failure-report.en.md](examples/failure-report.en.md)
- [examples/download-diagnostics.en.md](examples/download-diagnostics.en.md)

Chinese examples are also available under `examples/*.zh.md`.

## How It Differs From Generic Video Summarizers

| Capability | What `watchvideo` does |
| --- | --- |
| Evidence boundary | No MP4, transcript, or keyframes means no content summary |
| Download diagnostics | Records plain `yt-dlp`, browser-cookie retry, SSR `play_addr`, and direct download steps |
| Local transcription | Uses system `whisper` first, then auto-prepares `.tools/whisper.cpp` when needed |
| Visual grounding | Extracts keyframes and can run OCR to verify screen text and ASR errors |
| Agent handoff | Writes `report.md`, `report.json`, and `summary-input.md` for Codex to inspect |
| Cleanup | Deletes remote MP4 downloads after analysis by default; never deletes local source videos |

## Features

The CLI can automatically:

- download video URLs supported by `yt-dlp`;
- retry `yt-dlp` with browser cookies when platforms require login or bot verification;
- structurally parse mobile share-page SSR data such as `_ROUTER_DATA`, `RENDER_DATA`, and `play_addr` URLs when `yt-dlp` fails;
- record every download attempt in the final report;
- download platform subtitles or auto-subtitles;
- probe duration, resolution, and media metadata;
- parse `.srt` and `.vtt` subtitles;
- use system `whisper`, or auto-prepare local `.tools/whisper.cpp`, when subtitles are missing;
- extract keyframes and skip highly similar frames;
- generate `report.json`, `report.md`, and `summary-input.md`;
- check for likely leftover high-load processes.

Optional capabilities:

- run `tesseract` OCR on keyframes;
- limit the number of keyframes for long videos;
- keep downloaded remote MP4 files with `--keep-video`.

The CLI does not:

- call OpenAI, Claude, Gemini, or any other cloud LLM;
- edit, cut, compress, transcode, publish, or play videos;
- guarantee that every platform can be downloaded;
- open Chrome UI or operate the browser interface;
- kill processes automatically.

## Requirements

Required tools:

```bash
python3
yt-dlp
ffmpeg
ffprobe
```

macOS:

```bash
brew install yt-dlp ffmpeg
```

Optional tools:

```bash
git
bash
cmake
whisper
tesseract
```

`git` and `bash` are used when the CLI needs to prepare local `whisper.cpp`. If system `cmake` is missing, the CLI tries a local `.tools/.venv` fallback. Missing optional tools do not block videos that already have usable subtitles, but they may limit transcription or OCR.

Check the environment:

```bash
cd ~/.codex/skills/watch-video
python3 -m watchvideo doctor
```

`doctor` output:

- `REQUIRED_OK`: required tool is available;
- `REQUIRED_MISSING`: install this before analysis;
- `OPTIONAL_OK`: optional capability is available;
- `OPTIONAL_MISSING`: workflow can continue, but transcription or OCR may be limited.

## Use With Codex

Ask Codex directly:

```text
Use $watch-video to analyze this video: https://example.com/video
```

or:

```text
Use $watch-video to summarize this local video: /path/to/video.mp4
```

For summarize/analyze/watch/what-is-this-video-about requests, the agent should run or inspect the CLI artifacts before answering. If `report.md` exists, the final understanding should be written into the `## 视频内容总结` section unless the user explicitly asks not to write files.

**Do not summarize only from a URL, title, description, search result, or same-topic article.** The summary must be grounded in MP4 evidence, subtitles/transcripts, OCR, and keyframes. If evidence is missing, report the blocker and ask for a local video file or an accessible direct URL.

## Manual CLI Usage

If you are not using Codex, run the CLI manually from the skill repository. Save the original workspace first and write outputs back into that workspace:

```bash
TASK_WORKDIR="$(pwd)"
cd ~/.codex/skills/watch-video
python3 -m watchvideo analyze "https://example.com/video" \
  -o "$TASK_WORKDIR/analysis/demo"
```

Local file:

```bash
TASK_WORKDIR="$(pwd)"
cd ~/.codex/skills/watch-video
python3 -m watchvideo analyze "$TASK_WORKDIR/video.mp4" \
  -o "$TASK_WORKDIR/analysis/local-video"
```

Typical higher-signal run:

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --max-height 1080 \
  --keyframe-interval 10 \
  --max-keyframes 80 \
  --sub-lang "zh.*" \
  --sub-lang "en.*" \
  -o "$TASK_WORKDIR/analysis/demo"
```

Remote MP4 downloads are temporary by default. They are deleted after probe, transcription, keyframe extraction, and OCR finish. `report.md` and `summary-input.md` record the cleanup. Keep the downloaded MP4 only when needed:

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --keep-video \
  -o "$TASK_WORKDIR/analysis/demo"
```

Browser-cookie behavior:

```bash
# Disable browser-cookie retry.
python3 -m watchvideo analyze "https://example.com/video" \
  --no-browser-cookies \
  -o "$TASK_WORKDIR/analysis/demo"

# Try chrome, chromium, edge, then firefox.
python3 -m watchvideo analyze "https://example.com/video" \
  --cookies-from-browser auto \
  -o "$TASK_WORKDIR/analysis/demo"
```

Generate the summary input packet:

```bash
python3 -m watchvideo summarize "$TASK_WORKDIR/analysis/demo/report.json" \
  -o "$TASK_WORKDIR/analysis/demo/summary-input.md" \
  --chunk-seconds 300
```

Check likely leftover processes:

```bash
python3 -m watchvideo processes
```

## Artifacts

A successful run normally creates:

- `report.json`: structured report for programs and follow-up tooling;
- `report.md`: human-readable report with metadata, evidence quality, timeline preview, download diagnostics, cleanup records, transcription metadata, transcript text, and optional summary;
- `summary-input.md`: agent-friendly packet with writing requirements, report shape, download diagnostics, cleanup records, transcription metadata, keyframe timestamps, OCR, and chunked transcript;
- `subtitles/`: platform subtitles or auto-subtitles;
- `transcript/`: local transcription output;
- `keyframes/`: extracted keyframe images;
- `video/`: temporary remote download directory; remote MP4s are deleted by default unless `--keep-video` is used.

If no usable evidence can be produced:

- `failure.json`: structured failure details and download attempts;
- `failure.md`: human-readable failure report that explicitly forbids title/description/search-based summaries.

**Do not commit runtime artifacts.** `.gitignore` excludes `analysis/`, `.tools/`, `.models/`, media files, model files, `.env`, and cache directories.

## Local Transcription And OCR

Default behavior:

- prefer platform or sidecar subtitles;
- try the system `whisper` CLI when subtitles are missing;
- if system `whisper` is unavailable or produces no cues, auto-prepare `.tools/whisper.cpp`, download the `base` model, and build `whisper-cli`;
- if system `cmake` is missing, try a local `.tools/.venv` fallback;
- never install system-level packages automatically.

`report.md` records the ASR source, model, language parameter, prompt usage, and transcript files.

Disable automatic `whisper.cpp` setup:

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --no-auto-transcribe-setup \
  -o "$TASK_WORKDIR/analysis/demo"
```

Use a custom tools cache:

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --tools-dir "$TASK_WORKDIR/.tools" \
  --whisper-prompt "Agent, Codex, AI coding" \
  --language zh \
  -o "$TASK_WORKDIR/analysis/demo"
```

Use preinstalled `whisper.cpp`:

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --whisper-cpp-bin .tools/whisper.cpp/build/bin/whisper-cli \
  --whisper-model .tools/whisper.cpp/models/ggml-base.bin \
  --whisper-prompt "Agent, Codex, AI coding" \
  --language zh \
  --max-keyframes 80 \
  -o "$TASK_WORKDIR/analysis/demo"
```

Enable OCR:

```bash
python3 -m watchvideo analyze "$TASK_WORKDIR/video.mp4" \
  --ocr \
  -o "$TASK_WORKDIR/analysis/local-video"
```

If `tesseract` is missing, the main workflow continues and records a warning.

## Development Verification

The project uses stdlib `unittest`; `pytest` is not required.

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall watchvideo tests
python3 -m watchvideo doctor
```

The downloader tests include sanitized share-page fixtures for `_ROUTER_DATA`, `play_addr.url_list`, `aweme/v1/playwm`, and CDN MP4 redirects.

`doctor` must not show `REQUIRED_MISSING`. `OPTIONAL_MISSING` is acceptable, but it affects transcription or OCR capabilities.

## Documentation

- [README.zh-CN.md](README.zh-CN.md): Chinese README.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): module boundaries and data flow.
- [docs/OPERATIONS.md](docs/OPERATIONS.md): local operations, transcription, OCR, and process checks.
- [docs/PUBLISHING.md](docs/PUBLISHING.md): public repository checklist.
- [docs/PROMOTION.md](docs/PROMOTION.md): public positioning, launch copy, and demo script.
- [examples/](examples/): sanitized example reports and download diagnostics.
- [evals/skill_scenarios.md](evals/skill_scenarios.md): agent behavior scenarios.

## Maintenance And Publishing

Keep these directories and files in the long-term reusable skill:

- `SKILL.md`
- `references/`
- `watchvideo/`
- `scripts/`
- `tests/`
- `evals/`
- `docs/`
- `examples/`

Before publishing, confirm that the repository does not include real videos, audio, subtitles, keyframes, transcripts, cookies, tokens, `.env`, private links, or user Obsidian notes.
