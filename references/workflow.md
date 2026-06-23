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

Keep generated media, transcripts, keyframes, and reports inside the output directory. Do not write analysis outputs into the skill installation directory unless it is also the user's current project workspace. Do not add `analysis/`, `.tools/`, `.venv/`, or model files to git.

## 3. Check Tools

Run:

```bash
python3 -m watchvideo doctor
```

Required tools: `python3`, `yt-dlp`, `ffmpeg`, `ffprobe`.

Optional tools: `whisper`, `tesseract`, `whisper.cpp` `whisper-cli` and model.

`doctor` prints `REQUIRED_OK` or `REQUIRED_MISSING` for required tools, and `OPTIONAL_OK` or `OPTIONAL_MISSING` for optional tools. Stop on `REQUIRED_MISSING`. Continue with evidence limits on `OPTIONAL_MISSING`.

## 4. Analyze Video

Local file:

```bash
python3 -m watchvideo analyze "$TASK_WORKDIR/video.mp4" -o "$TASK_WORKDIR/analysis/local-video"
```

Remote URL:

```bash
python3 -m watchvideo analyze "https://example.com/video" -o "$TASK_WORKDIR/analysis/remote-video"
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

Enable OCR only when visual text, slides, code, tables, or screenshots matter:

```bash
python3 -m watchvideo analyze "$TASK_WORKDIR/video.mp4" --ocr -o "$TASK_WORKDIR/analysis/local-video"
```

## 5. Use Local whisper.cpp When Needed

If `report.md` says there are no subtitles or no transcript, rerun with local transcription when configured:

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --whisper-cpp-bin .tools/whisper.cpp/build/bin/whisper-cli \
  --whisper-model .tools/whisper.cpp/models/ggml-base.bin \
  --whisper-prompt "Agent, Codex, AI 编程, skill, GitHub" \
  --language zh \
  --max-keyframes 80 \
  -o "$TASK_WORKDIR/analysis/demo"
```

Use a domain-specific prompt when the video has known jargon. Do not invent jargon not supported by the content.

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
