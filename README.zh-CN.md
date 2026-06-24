# watchvideo

[English](README.md) | [中文](README.zh-CN.md)

**面向 Codex 的证据优先视频理解 skill。**

`watchvideo` 是一个 **Codex skill + 本地视频分析 CLI**。它把本地视频或网络视频链接整理成可验证证据，再让 Codex 基于报告、字幕、转写、OCR 和关键帧写总结。拿不到视频证据时，Agent 应该停止并说明阻塞原因，而不是靠标题、简介或搜索结果猜内容。

**核心边界：CLI 负责准备证据，Agent 负责理解和写总结。** 这个项目不内置云端 LLM 摘要，也不是视频剪辑、转码、发布或播放器工具。

## 为什么做这个

通用 Agent 很容易在“总结这个视频”时走捷径：读取 URL、标题、简介或搜索结果，然后给出一段看似合理的归纳。`watchvideo` 把这条捷径关掉：它要求先下载或读取视频，抽取字幕/转写、关键帧和 OCR，再把证据整理成 Agent 可读取的报告。

适合这些场景：

- 让 Codex 总结技术视频、面试视频、教程视频或产品演示；
- 保留可追溯的 `report.md` / `summary-input.md`，而不是只得到一段聊天答案；
- 遇到 Douyin/TikTok/YouTube 下载失败时，看清楚卡在哪一步；
- 分享一个长期可复用、可测试的 Agent skill。

## 快速体验

安装到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/Dunteng/watch-video-skill ~/.codex/skills/watch-video
cd ~/.codex/skills/watch-video
python3 -m watchvideo doctor
```

重启 Codex 会话后，直接说：

```text
用 $watch-video 总结这个视频：https://example.com/video
```

CLI 会生成证据包，Codex 读取后输出文档级总结。示例输出：

- [examples/technical-interview-summary.zh.md](examples/technical-interview-summary.zh.md)
- [examples/failure-report.zh.md](examples/failure-report.zh.md)
- [examples/download-diagnostics.zh.md](examples/download-diagnostics.zh.md)

英文示例见 `examples/*.en.md`。

## 和普通视频摘要工具的区别

| 能力 | watchvideo 的做法 |
| --- | --- |
| 证据边界 | 没有 MP4、字幕/转写或关键帧时不总结 |
| 下载诊断 | 记录普通 `yt-dlp`、浏览器 cookies、SSR `play_addr`、直链下载每一步 |
| 本地转写 | 先用系统 `whisper`，必要时自动准备 `.tools/whisper.cpp` |
| 视觉校正 | 抽关键帧，可选 OCR，用画面校正屏幕文字和 ASR 错词 |
| Agent 交接 | 生成 `report.md`、`report.json`、`summary-input.md` 供 Codex 读取 |
| 清理策略 | 远程下载 MP4 默认分析后删除，本地输入文件不删除 |

## 功能

CLI 可以自动处理：

- 下载 `yt-dlp` 支持的视频链接；
- 遇到登录或 bot 校验时，用浏览器 cookies 重试；
- `yt-dlp` 失败时，结构化解析移动端分享页 SSR 里的 `_ROUTER_DATA` / `RENDER_DATA` / `play_addr` 视频直链；
- 在报告里记录每一步下载尝试；
- 下载平台字幕或自动字幕；
- 探测视频时长、分辨率等元信息；
- 解析 `.srt` / `.vtt` 字幕；
- 没有字幕时调用系统 `whisper`，必要时自动准备 `.tools/whisper.cpp` 转写；
- 抽取关键帧，并跳过高度相似的重复画面；
- 生成 `report.json`、`report.md` 和 `summary-input.md`；
- 检查疑似残留的高负载进程。

可选能力：

- 使用 `tesseract` 对关键帧做 OCR；
- 限制关键帧数量，避免长视频产物过大；
- 使用 `--keep-video` 保留远程下载 MP4。

不会自动处理：

- 调用 OpenAI、Claude、Gemini 或其他云端 LLM；
- 剪辑、压缩、转码、发布或播放视频；
- 保证所有平台都能下载；
- 打开 Chrome 页面或操作浏览器 UI；
- 自动结束进程。

## 系统依赖

必需工具：

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

可选工具：

```bash
git
bash
cmake
whisper
tesseract
```

`git` 和 `bash` 用于在没有可用字幕时自动准备本 skill 私有的 `.tools/whisper.cpp`。如果系统没有 `cmake`，CLI 会尝试使用 `.tools/.venv` 的本地 fallback。缺少可选工具不会影响已有字幕的视频，但可能影响转写或 OCR。

检查环境：

```bash
cd ~/.codex/skills/watch-video
python3 -m watchvideo doctor
```

## 用 Codex 分析视频

```text
用 $watch-video 分析这个视频：https://example.com/video
```

或：

```text
用 $watch-video 总结这个本地视频：/path/to/video.mp4
```

对于总结、分析、看懂或“这个视频讲什么”类请求，Agent 应先运行或读取 CLI 产物，再回答。如果 `report.md` 存在，最终理解应写入 `## 视频内容总结`，除非用户明确要求不要写文件。

**不要只凭视频 URL、标题、简介、搜索结果或同主题文章总结。** 总结必须基于 MP4、字幕/转写、OCR 和关键帧证据。缺少证据时，应说明阻塞原因，并要求用户提供本地视频或可访问直链。

## 手动运行 CLI

建议先保存当前工作目录，再从 skill 仓库运行 CLI，并把输出写回当前工作区：

```bash
TASK_WORKDIR="$(pwd)"
cd ~/.codex/skills/watch-video
python3 -m watchvideo analyze "https://example.com/video" \
  -o "$TASK_WORKDIR/analysis/demo"
```

本地视频：

```bash
TASK_WORKDIR="$(pwd)"
cd ~/.codex/skills/watch-video
python3 -m watchvideo analyze "$TASK_WORKDIR/video.mp4" \
  -o "$TASK_WORKDIR/analysis/local-video"
```

常用参数：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --max-height 1080 \
  --keyframe-interval 10 \
  --max-keyframes 80 \
  --sub-lang "zh.*" \
  --sub-lang "en.*" \
  -o "$TASK_WORKDIR/analysis/demo"
```

远程下载的 MP4 默认会在探测、转写、抽帧和 OCR 完成后删除。需要保留原始下载文件时：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --keep-video \
  -o "$TASK_WORKDIR/analysis/demo"
```

生成摘要输入包：

```bash
python3 -m watchvideo summarize "$TASK_WORKDIR/analysis/demo/report.json" \
  -o "$TASK_WORKDIR/analysis/demo/summary-input.md" \
  --chunk-seconds 300
```

## 输出产物

成功分析通常会生成：

- `report.json`：结构化报告；
- `report.md`：人类可读报告，包含元信息、证据质量、时间线、下载诊断、清理记录、转写信息、字幕文本和可选总结；
- `summary-input.md`：面向 Agent 的摘要输入包；
- `subtitles/`：平台字幕或自动字幕；
- `transcript/`：本地转写结果；
- `keyframes/`：关键帧图片；
- `video/`：网络视频临时下载目录；默认分析完成后删除下载 MP4。

如果没有拿到可分析证据，会生成：

- `failure.json`：结构化失败原因和下载尝试；
- `failure.md`：人类可读失败报告，明确禁止基于标题、简介或搜索结果总结。

**不要提交运行产物。** `.gitignore` 已忽略 `analysis/`、`.tools/`、`.models/`、媒体文件、模型文件、`.env` 和缓存目录。

## 本地转写和 OCR

默认行为：

- 优先使用平台字幕或旁路字幕；
- 没有字幕时先尝试系统 `whisper` CLI；
- `whisper` 不可用或没有结果时，默认在 `.tools/whisper.cpp` 下 clone、下载 `base` 模型并构建 `whisper-cli`；
- 系统没有 `cmake` 时，尝试 `.tools/.venv` fallback；
- 不自动安装系统级依赖。

`report.md` 会记录 ASR 来源、模型、语言参数、是否使用 prompt，以及逐字稿文件。

启用 OCR：

```bash
python3 -m watchvideo analyze "$TASK_WORKDIR/video.mp4" \
  --ocr \
  -o "$TASK_WORKDIR/analysis/local-video"
```

## 开发验证

项目使用标准库 `unittest`：

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall watchvideo tests
python3 -m watchvideo doctor
```

## 文档

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)：模块边界和数据流。
- [docs/OPERATIONS.md](docs/OPERATIONS.md)：本地操作、转写、OCR 和进程检查。
- [docs/PUBLISHING.md](docs/PUBLISHING.md)：公开发布检查清单。
- [docs/PROMOTION.md](docs/PROMOTION.md)：公开宣传定位、发布文案和 demo 脚本。
- [examples/](examples/)：脱敏示例报告和下载诊断。
- [evals/skill_scenarios.md](evals/skill_scenarios.md)：Agent 行为评估场景。

## 维护和发布

作为长期通用 skill，仓库应保留：

- `SKILL.md`
- `references/`
- `watchvideo/`
- `scripts/`
- `tests/`
- `evals/`
- `docs/`
- `examples/`

公开发布前，确认没有提交真实视频、音频、字幕、关键帧、转写报告、Cookie、token、`.env`、私有链接或用户 Obsidian 笔记。
