# Troubleshooting

Use this reference when the video workflow has missing tools, missing subtitles, noisy output, or long-running local processes.

## Tool Missing

If `doctor` reports `REQUIRED_MISSING`, stop and report the specific missing command. Required tools are `python3`, `yt-dlp`, `ffmpeg`, and `ffprobe`.

If optional tools are missing:

- `OPTIONAL_MISSING whisper`: continue; `analyze` can still use platform subtitles or auto-prepare `whisper.cpp`;
- `OPTIONAL_MISSING git` or `OPTIONAL_MISSING bash`: continue for videos with subtitles, but automatic `whisper.cpp` setup will fail when transcription is needed;
- `OPTIONAL_MISSING cmake`: continue; `analyze` will try to install a local `cmake` under `.tools/.venv`;
- `OPTIONAL_MISSING tesseract`: continue without OCR and mention that visual text was not OCR'd;
- missing explicitly configured `whisper.cpp` binary or model: fix the paths, or remove `--whisper-cpp-bin`/`--whisper-model` so automatic setup can run.

## No Subtitle Or Transcript

If `report.md` has `字幕文件数: 0` or says no transcript is available:

1. Rerun `analyze` with automatic transcription enabled, optionally adding `--whisper-prompt` and `--language`.
2. If the user disabled setup or setup failed, fix missing `git`/`bash`, inspect local `cmake` setup under `.tools/.venv`, or provide explicit `--whisper-cpp-bin` and `--whisper-model` paths.
3. If local transcription is still unavailable, summarize only visual/keyframe evidence and clearly state the limitation.
4. Do not claim exact spoken content without transcript evidence.

## Noisy Transcription

ASR may corrupt technical terms, English names, acronyms, and Chinese homophones. Mark uncertain terms as "疑似" or "需确认". Use keyframes to correct slide titles, code identifiers, and visible keywords.

## Too Many Keyframes

Use `--max-keyframes 80` for normal videos. For short videos, a lower limit such as 30-50 is usually enough. More keyframes are only useful when visual content changes rapidly.

## Download Failure

For a URL failure:

- preserve the exact URL in the report to the user;
- read `failure.md` / `failure.json` if normal reports were not produced;
- otherwise read `下载诊断` in `report.md` / `summary-input.md`, or `download_attempts` in `report.json`, before explaining the blocker;
- mention that `watchvideo` tried plain `yt-dlp`, browser-cookie `yt-dlp`, and structural mobile share-page `window._ROUTER_DATA` / `RENDER_DATA` / `play_addr.url_list` extraction when applicable;
- do not open Chrome UI; `--cookies-from-browser chrome` reads the existing browser profile directly;
- ask for an accessible direct video URL or a local downloaded file if the platform still blocks download;
- stop without summarizing when no MP4, transcript, or keyframes exist.

Do not use the title, description, platform metadata, public search results, or same-topic materials as a substitute for video evidence.

## Long Running Work

Downloads, `ffmpeg`, OCR, and transcription can be slow and CPU-heavy. Give progress updates during long runs. After completion, run:

```bash
python3 -m watchvideo processes
```

Only stop processes after confirming command, path, and PID with the user.

## Existing Project Edits

Using this skill should not require editing the `watchvideo` source code. If a CLI bug appears, switch to normal debugging workflow and treat that as a separate code task.
