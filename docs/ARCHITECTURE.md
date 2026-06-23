# 架构说明

本文记录当前实现的真实边界。这个仓库的目标是把视频整理成可供 Codex 理解的材料，而不是直接替代 Codex 做完整内容分析。

## 数据流

```text
source
  -> classify_source
  -> YtDlpClient 或本地文件
  -> FfmpegClient.probe
  -> 字幕加载或 WhisperTranscriber 或 WhisperCppTranscriber
  -> FfmpegClient.extract_keyframes，可限制数量
  -> 可选 TesseractOcr
  -> AnalysisReport
  -> report.json / report.md
```

## 模块边界

- `watchvideo/cli.py`
  命令行入口。负责参数解析、调用分析器、写出报告、生成摘要输入包和打印进程检查结果。

- `watchvideo/analyzer.py`
  编排层。负责决定先下载字幕、再下载视频、再加载字幕或转写、最后抽关键帧。这里不直接写下载、转写或抽帧细节。

- `watchvideo/downloader.py`
  `yt-dlp` 适配层。负责平台字幕下载和网络视频下载。

- `watchvideo/media.py`
  `ffmpeg` / `ffprobe` 适配层。负责读取视频元信息、抽候选帧、保存代表帧。

- `watchvideo/keyframes.py`
  关键帧策略。当前按固定时间窗口取三个候选点，避开窗口首尾，然后用 PPM 图片的边缘变化做清晰度评分。

- `watchvideo/subtitles.py`
  字幕解析。支持 `.srt` 和 `.vtt`，会清理标签、合并多行文本、去掉相邻重复句。

- `watchvideo/transcription.py`
  自动转写入口。支持系统 PATH 上名为 `whisper` 的 CLI，也支持显式传入本地 `whisper.cpp` 的 `whisper-cli` 和模型路径。

- `watchvideo/ocr.py`
  OCR 入口。当前只在用户传 `--ocr` 时调用 `tesseract`，并只处理已经抽出的关键帧。

- `watchvideo/summarizer.py`
  摘要输入包生成器。读取 `report.json` 字典，把元信息、警告、关键帧目录和字幕分段整理成 Markdown，不调用 LLM。

- `watchvideo/processes.py`
  进程检查。扫描 `watchvideo`、`yt-dlp`、`ffmpeg`、`whisper-cli` 等相关命令，只报告不清理。

- `watchvideo/reporting.py`
  报告写出。生成 `report.json` 和 `report.md`。Markdown 报告面向人阅读，不逐张列出关键帧；关键帧明细保留在 JSON。

- `watchvideo/models.py`
  数据模型。集中定义 source、media、subtitle、keyframe、report 等结构。

## 大模型能力边界

仓库代码本身不调用 OpenAI、Claude、Gemini 或其他云端 LLM API。

当前大模型相关能力分两类：

- 语音识别：如果安装 `whisper` CLI，或提供 `whisper.cpp` 参数，脚本会本地生成字幕。
- 内容理解：目前由 Codex 在对话中读取报告、摘要输入包和关键帧后完成，不在代码里自动执行。

本地 `whisper.cpp` 流程已经纳入 `python3 -m watchvideo analyze` 的自动路径，但需要用户显式提供二进制和模型路径。

如果 Codex 已经得出“视频讲了什么”的最终总结，调用方应把总结写入 `AnalysisReport.summary_text`，让 `report.md` 出现 `视频内容总结` 区块。总结不能只存在于对话上下文里。

## 当前限制

- 没有场景检测，当前是固定窗口采样加清晰度评分。
- 没有内置摘要生成，视频总结仍需要 Codex 或其他 LLM 读取报告后完成。
- OCR 只处理关键帧，不覆盖所有视频帧。
- 进程检查只报告，不自动结束进程。
- `summarize` 只生成输入包，不调用模型。

## 下一步设计方向

优先级从高到低：

1. 增加场景检测或镜头切分，减少固定窗口采样的冗余。
2. 改进 OCR 区域选择，只处理底部字幕区或关键帧主要文本区。
3. 增加可选 LLM 集成，把 `summarize` 输入包送入 OpenAI API。
4. 增加更完整的集成测试，覆盖真实短视频样本。
