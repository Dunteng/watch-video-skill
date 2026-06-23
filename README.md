# watchvideo

`watchvideo` 是一个 **Codex skill + 本地视频分析 CLI**。它把本地视频或网络视频链接整理成可读证据，再由 Codex 基于报告、字幕、转写和关键帧完成总结。

**核心边界：CLI 负责准备证据，Agent 负责理解和写总结。** 这个项目不内置云端 LLM 摘要，也不是视频剪辑、转码或播放器工具。

## 功能

脚本可以自动处理：

- 下载 `yt-dlp` 支持的视频链接；
- `yt-dlp` 失败时结构化解析移动端分享页 SSR 里的 `_ROUTER_DATA` / `RENDER_DATA` / `play_addr` 视频直链；
- 在报告里记录普通下载、浏览器 cookies 重试、SSR 解析和直链下载的诊断；
- 下载平台字幕或自动字幕；
- 探测视频时长、分辨率等元信息；
- 解析 `.srt` / `.vtt` 字幕；
- 没有字幕时调用系统 `whisper`，必要时自动准备 `.tools/whisper.cpp` 转写；
- 抽取关键帧，并跳过高度相似的重复画面；
- 生成 `report.json` 和 `report.md`；
- 生成面向 Agent 阅读的 `summary-input.md`；
- 检查疑似残留的高负载进程。

脚本可以按需处理：

- 使用 `tesseract` 对关键帧做 OCR；
- 限制关键帧数量，避免长视频产物过大。

脚本不会自动处理：

- 云端 LLM 总结；
- 视频剪辑、压缩、转码、发布；
- 完整场景检测；
- 自动结束进程。
- 打开 Chrome 页面或操作浏览器 UI。

## 安装为 Codex Skill

把仓库放到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/Dunteng/watch-video-skill ~/.codex/skills/watch-video
```

更新已安装版本：

```bash
cd ~/.codex/skills/watch-video
git pull
```

安装或更新后，**重启 Codex 会话**，让 Codex 重新发现 `$watch-video`。

## 系统依赖

必需工具：

```bash
python3
yt-dlp
ffmpeg
ffprobe
```

macOS 可以用 Homebrew 安装：

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

`git` 和 `bash` 用于在没有可用字幕时自动准备本 skill 私有的 `.tools/whisper.cpp`。如果系统没有 `cmake`，CLI 会尝试在 `.tools/.venv` 安装本地 `cmake` wheel；这些准备步骤失败时，有字幕的视频仍可分析，无字幕视频会在报告里记录转写限制。

检查环境：

```bash
cd ~/.codex/skills/watch-video
python3 -m watchvideo doctor
```

`doctor` 输出含义：

- `REQUIRED_OK`：必需工具可用；
- `REQUIRED_MISSING`：必须先安装，否则分析流程会失败；
- `OPTIONAL_OK`：可选能力可用；
- `OPTIONAL_MISSING`：可选能力不可用，但主流程可以继续；无字幕视频可能无法完成本地转写或 OCR。

## 用 Codex 分析视频

在 Codex 里直接请求：

```text
用 $watch-video 分析这个视频：https://example.com/video
```

或：

```text
用 $watch-video 总结这个本地视频：/path/to/video.mp4
```

Agent 会按 skill 流程运行 CLI、读取证据文件、输出总结，并在已有 `report.md` 时把最终总结写回 `## 视频内容总结`。

**不要只凭视频 URL、标题、简介或搜索结果总结。** 这个 skill 要求先生成或读取分析产物，再基于 MP4、字幕/转写和关键帧证据下结论。遇到 cookies 拦截时 CLI 会直接用 Chrome cookies 重试；拿不到证据时应说明下载阻塞，并要求用户提供本地视频或可访问直链。

如果分析失败，CLI 会在输出目录写入 `failure.md` 和 `failure.json`。Agent 应读取失败报告里的下载诊断，只说明阻塞原因和下一步需要的证据。

## 手动运行 CLI

如果不通过 Codex，也可以手动运行。建议先保存用户工作目录，再从 skill 仓库运行 CLI，并把输出写回当前工作区：

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

默认遇到 cookies/login/bot 拦截时，会用 `yt-dlp --cookies-from-browser chrome` 重试，不会打开 Chrome 页面。需要关闭时加：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --no-browser-cookies \
  -o "$TASK_WORKDIR/analysis/demo"
```

需要自动尝试多个浏览器 cookies 时加：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --cookies-from-browser auto \
  -o "$TASK_WORKDIR/analysis/demo"
```

生成摘要输入包：

```bash
python3 -m watchvideo summarize "$TASK_WORKDIR/analysis/demo/report.json" \
  -o "$TASK_WORKDIR/analysis/demo/summary-input.md" \
  --chunk-seconds 300
```

检查残留进程：

```bash
python3 -m watchvideo processes
```

## 输出产物

一次分析通常会生成：

- `report.json`：结构化报告，适合程序继续处理；
- `report.md`：人类可读报告，包含元信息、下载诊断、转写信息、字幕文本和可选总结；
- `summary-input.md`：面向 Agent 的摘要输入包，包含下载诊断和分段字幕；
- `video/`：网络视频下载结果；
- `subtitles/`：平台字幕或自动字幕；
- `transcript/`：本地转写结果；
- `keyframes/`：关键帧图片。

如果没有拿到可分析证据，会生成：

- `failure.json`：结构化失败原因和下载尝试；
- `failure.md`：人类可读失败报告，明确禁止基于标题、简介或搜索结果总结。

**不要提交运行产物。** `.gitignore` 已忽略 `analysis/`、`.tools/`、`.models/`、媒体文件、模型文件、`.env` 和缓存目录。

## 本地转写和 OCR

默认行为：

- 优先使用平台字幕或旁路字幕；
- 没有字幕时先尝试系统 PATH 上的 `whisper` CLI；
- `whisper` 不可用或没有结果时，默认在 skill 仓库的 `.tools/whisper.cpp` 下 clone、下载 `base` 模型并构建 `whisper-cli`；
- 系统没有 `cmake` 时，会尝试在 `.tools/.venv` 内准备本地 `cmake`，不修改系统环境；
- `.tools/` 和模型文件已被 `.gitignore` 忽略，不应提交。

`report.md` 会记录 ASR 来源、模型、语言参数、是否使用 prompt，以及生成的逐字稿文件。

禁用自动准备：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --no-auto-transcribe-setup \
  -o "$TASK_WORKDIR/analysis/demo"
```

把工具缓存放到自定义目录：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --tools-dir "$TASK_WORKDIR/.tools" \
  --whisper-prompt "Agent, Codex, AI 编程" \
  --language zh \
  -o "$TASK_WORKDIR/analysis/demo"
```

使用已经预装好的 `whisper.cpp`：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --whisper-cpp-bin .tools/whisper.cpp/build/bin/whisper-cli \
  --whisper-model .tools/whisper.cpp/models/ggml-base.bin \
  --whisper-prompt "Agent, Codex, AI 编程" \
  --language zh \
  --max-keyframes 80 \
  -o "$TASK_WORKDIR/analysis/demo"
```

启用 OCR：

```bash
python3 -m watchvideo analyze "$TASK_WORKDIR/video.mp4" \
  --ocr \
  -o "$TASK_WORKDIR/analysis/local-video"
```

`tesseract` 缺失时，主流程会继续，只是不会识别画面文字。

## 开发验证

本项目使用标准库 `unittest`，不要求 `pytest`：

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall watchvideo tests
python3 -m watchvideo doctor
```

下载链路有脱敏分享页 fixture，覆盖 `_ROUTER_DATA`、`play_addr.url_list`、`aweme/v1/playwm` 和 CDN MP4 跳转诊断。

`doctor` 中不能出现 `REQUIRED_MISSING`。`OPTIONAL_MISSING` 可以接受，但会影响本地转写或 OCR 能力。

如果 `OPTIONAL_MISSING git` 或 `OPTIONAL_MISSING bash` 出现，自动准备 `whisper.cpp` 会失败。`OPTIONAL_MISSING cmake` 会触发 `.tools/.venv` 兜底，只有本地 `cmake` 安装失败时才影响无字幕视频转写。

## 文档

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)：模块边界和数据流。
- [docs/OPERATIONS.md](docs/OPERATIONS.md)：本地操作、转写、OCR 和进程检查。
- [docs/PUBLISHING.md](docs/PUBLISHING.md)：发布到 GitHub 前的检查清单。
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

公开发布前，确认没有提交真实视频、音频、字幕、关键帧、转写报告、Cookie、token、`.env`、私有链接或用户 Obsidian 笔记。
