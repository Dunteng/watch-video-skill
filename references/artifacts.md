# Artifacts

Use this reference when an analysis directory already exists or after running `analyze`.

## Priority Order

1. `report.md`: human-readable report, durable place for the final summary.
2. `summary-input.md`: model-friendly packet with metadata, warnings, keyframe directory, OCR, and chunked transcript.
3. `transcript/*.srt` or `transcript/*.txt`: raw transcription with timestamps.
4. `keyframes/`: visual evidence for slides, code, diagrams, screenshots, and scene changes.
5. `report.json`: structured source of paths, timestamps, warnings, OCR, and keyframe metadata.

## How To Read

Start with `report.md` to understand source, duration, resolution, subtitle count, warnings, and whether a summary already exists.

Read `summary-input.md` for chunked transcript. If it is missing, generate it from `report.json` with the `summarize` command.

Inspect keyframes when:

- the transcript is noisy or incomplete;
- the video likely contains slides, code, diagrams, product UI, charts, or on-screen text;
- the user wants a learning note, interview answer, tutorial outline, or visual explanation.

Use `report.json` for exact paths and timestamps. Do not copy the full JSON into the final answer unless the user asks.

## Summary Output Standard

For a normal video summary, produce:

- one-sentence summary;
- structured summary by topic or timeline;
- key points and takeaways;
- suspicious transcription/OCR items that need confirmation;
- practical examples or answer templates when the video is interview/tutorial content.

Keep wording in Chinese unless the user asks otherwise.

## Persisting The Result

When `report.md` exists, final understanding should be written into the `## 视频内容总结` section. If the section does not exist, insert it before `## 关键帧` or before the transcript section.

Use the helper script from the skill directory:

```bash
python3 /Users/dt/.codex/skills/watch-video/scripts/update_report_summary.py \
  analysis/demo/report.md \
  --summary-file /tmp/video-summary.md
```

Or pipe summary text through stdin:

```bash
printf '%s\n' "总结内容" | python3 /Users/dt/.codex/skills/watch-video/scripts/update_report_summary.py analysis/demo/report.md
```

Do not overwrite unrelated sections such as warnings, keyframe hints, OCR, or transcript.

## Obsidian Notes

If the user asks for an Obsidian note, use the user's vault path when available:

```text
/Users/dt/Documents/obsidian-vault
```

Include source URL, title if known, processed date, tags, core conclusion, evidence excerpts, and personal整理. Respect current user instructions before creating or modifying files outside the current workspace.
