# Workflow

Use this reference when starting a new video analysis or choosing which `watchvideo` command to run.

## 1. Locate The CLI

Use the directory that contains this skill's `SKILL.md` as the project root. It should also contain `watchvideo/cli.py`.

```bash
cd <watch-video-skill-repo>
python3 -m watchvideo doctor
```

If the package has been installed into the environment, this form may also work:

```bash
watchvideo doctor
```

If neither works, tell the user the skill repository or package is unavailable and ask for the installed skill path or clone URL.

## 2. Prepare Output Path

Create a readable output slug under the user's current workspace. If you need to `cd` into the skill repository to run `python3 -m watchvideo`, save the user's workspace first and pass an absolute output path:

```bash
TASK_WORKDIR="$(pwd)"
cd <watch-video-skill-repo>
python3 -m watchvideo analyze "<source>" -o "$TASK_WORKDIR/analysis/<source-or-topic-slug>"
```

Keep generated media, transcripts, keyframes, and reports inside the output directory. Do not write analysis outputs into the skill installation directory unless it is also the user's current project workspace. The CLI may maintain its local transcription cache under `.tools/whisper.cpp`; never add `analysis/`, `.tools/`, `.venv/`, or model files to git.

## 3. Check Tools

Run:

```bash
python3 -m watchvideo doctor
```

Required tools: `python3`, `yt-dlp`, `ffmpeg`, `ffprobe`.

Optional tools: `git` and `bash` for automatic `whisper.cpp` setup; `cmake` for system builds with `.tools/.venv` fallback; `whisper` for system ASR; `tesseract` for OCR.

`doctor` prints `REQUIRED_OK` or `REQUIRED_MISSING` for required tools, and `OPTIONAL_OK` or `OPTIONAL_MISSING` for optional tools. Stop on `REQUIRED_MISSING`. Continue on `OPTIONAL_MISSING`; missing `git` or `bash` prevents automatic `whisper.cpp` setup, while missing `cmake` triggers a local `.tools/.venv` fallback that may still fail if Python venv or package download is unavailable.

## 4. Analyze Video

Local file:

```bash
python3 -m watchvideo analyze "$TASK_WORKDIR/video.mp4" -o "$TASK_WORKDIR/analysis/local-video"
```

Remote URL:

```bash
python3 -m watchvideo analyze "https://example.com/video" -o "$TASK_WORKDIR/analysis/remote-video"
```

For remote URLs, evidence acquisition order is mandatory:

1. Run `watchvideo analyze`, which tries plain `yt-dlp`.
2. On cookies/login/bot errors, the CLI retries `yt-dlp --cookies-from-browser chrome` by default. Do not open Chrome UI.
3. If `yt-dlp` still fails, the CLI fetches the mobile share page, structurally parses `window._ROUTER_DATA` / `video.play_addr.url_list` before regex fallbacks, then downloads `aweme/v1/playwm` or CDN URLs with mobile UA and Referer.
4. If all attempts fail, stop and ask for a local video file or an accessible direct video URL.

`report.md`, `report.json`, and `summary-input.md` include download diagnostics when remote acquisition was attempted. Use them to explain which step failed instead of guessing from the URL or title.

Do not replace missing video evidence with the page title, description, search results, public subtitles for a similar title, or same-topic articles. Those sources can explain the blocker or help craft a prompt after evidence exists; they are not video evidence.

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

Enable OCR only when visual text, slides, code, tables, or screenshots matter:

```bash
python3 -m watchvideo analyze "$TASK_WORKDIR/video.mp4" --ocr -o "$TASK_WORKDIR/analysis/local-video"
```

## 5. Use Local Transcription When Needed

If no subtitle is available, `analyze` first tries system `whisper`, then automatically prepares `.tools/whisper.cpp` and transcribes with the `base` model. Use a domain-specific prompt when the video has known jargon:

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --whisper-prompt "Agent, Codex, AI 编程, skill, GitHub" \
  --language zh \
  --max-keyframes 80 \
  -o "$TASK_WORKDIR/analysis/demo"
```

Use `--no-auto-transcribe-setup` only when the user wants to avoid tool downloads/builds. Use `--tools-dir <path>` to place the `whisper.cpp` cache somewhere explicit. If the user provides `--whisper-cpp-bin` or `--whisper-model`, treat those paths as intentional and fix missing paths instead of silently replacing them.

## 6. Generate Summary Input

After `report.json` exists:

```bash
python3 -m watchvideo summarize "$TASK_WORKDIR/analysis/demo/report.json" \
  -o "$TASK_WORKDIR/analysis/demo/summary-input.md" \
  --chunk-seconds 300
```

Then read `report.md`, `summary-input.md`, transcripts, and keyframes before writing conclusions.

## 7. Finish And Check Processes

For long downloads or transcription runs:

```bash
python3 -m watchvideo processes
```

The process check only reports. Do not kill processes unless the user confirms the PID and command are from this task.
