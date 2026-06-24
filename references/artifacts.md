# Artifacts

Use this reference when an analysis directory already exists or after running `analyze`.

## Priority Order

1. `report.md`: human-readable report, durable place for the final summary.
2. `summary-input.md`: model-friendly packet with metadata, warnings, download diagnostics, transcription info, keyframe timestamps, OCR, and chunked transcript.
3. `transcript/*.srt` or `transcript/*.txt`: raw transcription with timestamps.
4. `keyframes/`: visual evidence for slides, code, diagrams, screenshots, and scene changes.
5. `report.json`: structured source of paths, timestamps, warnings, OCR, and keyframe metadata.

## How To Read

If `failure.md` exists, read it first. It means no usable MP4, transcript, or keyframes were produced; report the blocker and do not summarize video content.

Start with `report.md` to understand source, duration, resolution, evidence quality, timeline preview, subtitle count, download diagnostics, transcription info, warnings, and whether a summary already exists.

Read `summary-input.md` for chunked transcript. If it is missing, generate it from `report.json` with the `summarize` command.

Inspect keyframes when:

- the transcript is noisy or incomplete;
- the video likely contains slides, code, diagrams, product UI, charts, or on-screen text;
- the user wants a learning note, interview answer, tutorial outline, or visual explanation.

Use `report.json` for exact paths, timestamps, and the structured `download_attempts` list. Use `failure.json` for structured failure details when normal reports are absent. Do not copy the full JSON into the final answer unless the user asks.

Use `转写信息` to judge transcript reliability: system whisper versus whisper.cpp, model name, language parameter, prompt usage, and generated transcript files.

## Summary Output Standard

**Final summaries must stay evidence-grounded and easy to scan.**

For technical, interview, tutorial, or methodology videos, use this default report shape:

- 一句话总结：state the claim, target scenario, and core conclusion;
- 视频主线：3-6 timestamped nodes showing problem, view, evidence, and conclusion;
- 核心概念拆解：use `概念 / 定义 / 边界 / 例子 / 为什么重要 / 视频证据`;
- 常见误区：use `误区 / 为什么错 / 正确说法 / 证据`;
- 可执行方法：use `前提 / 步骤 / 检查清单 / 适用场景 / 不适用场景`;
- 面试回答模板：include `30 秒版 / 2 分钟版 / 追问应对 / 不推荐回答`;
- 转写校正说明：use `可疑原文 / 建议校正 / 置信度 / 校正依据`.

For other videos, produce:

- one-sentence summary;
- timeline summary with timestamps where possible;
- structured summary by topic;
- key points and takeaways;
- evidence notes for major claims, using transcript timestamps, OCR text, or keyframe context;
- suspicious transcription/OCR items that need confirmation;
- practical examples or answer templates when the video is interview/tutorial content.

In the technical/interview shape, keep every section but write `视频未明确提到` when the evidence does not support that section. The interview template must not become generic advice detached from the video.

Do not treat title, description, search results, or same-topic material as video evidence. If transcript, OCR, or keyframes are weak, state the limit in the summary instead of filling gaps.

Keep wording in Chinese unless the user asks otherwise.

## Persisting The Result

For 总结/分析/看懂/讲了什么 requests, when `report.md` exists, the Agent must write final understanding into the `## 视频内容总结` section unless the user explicitly asks not to write files. If the section does not exist, insert it before `## 关键帧` or before the transcript section.

Use the helper script from the skill repository root:

```bash
python3 scripts/update_report_summary.py \
  "$TASK_WORKDIR/analysis/demo/report.md" \
  --summary-file /tmp/video-summary.md
```

Or pipe summary text through stdin:

```bash
printf '%s\n' "总结内容" | python3 scripts/update_report_summary.py "$TASK_WORKDIR/analysis/demo/report.md"
```

Do not overwrite unrelated sections such as warnings, keyframe hints, OCR, or transcript.

## Obsidian Notes

If the user asks for an Obsidian note, use the user's configured vault path when available. If the target note is outside the current workspace, first state the target path, why it is needed, and what will be changed, then wait for user confirmation before writing. Include source URL, title if known, processed date, tags, core conclusion, evidence excerpts, and personal整理.
