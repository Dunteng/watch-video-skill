# 操作手册

本文记录本地使用流程、转写流程、验证命令和任务收尾检查。

## 基础分析

检查环境：

```bash
python3 -m watchvideo doctor
```

`REQUIRED_MISSING` 表示需要先安装后再分析；`OPTIONAL_MISSING` 只表示对应能力不可用或需要本地兜底，例如没有系统 `whisper`、没有 OCR，或需要在 `.tools/.venv` 准备 `cmake`。

分析视频链接：

```bash
python3 -m watchvideo analyze "https://example.com/video" -o analysis/demo
```

远程视频的下载 MP4 默认是临时文件：CLI 会在完成探测、转写、抽帧和 OCR 后删除它，并在 `report.md`、`report.json`、`summary-input.md` 写入 `清理记录`。如果这次任务需要保留原始下载文件用于人工复查，加 `--keep-video`。本地输入文件不会被删除。

远程视频取证顺序是固定的：先普通 `yt-dlp`，遇到 cookies/login/bot 拦截就用 `--cookies-from-browser chrome` 直接读取已有 Chrome cookies 重试，也可以用 `--cookies-from-browser auto` 按 chrome、chromium、edge、firefox 尝试；再失败后结构化解析公开分享页/SSR 里的 `_ROUTER_DATA` / `RENDER_DATA` / `play_addr`，最后才要求用户提供本地视频或可访问直链。**不要打开 Chrome 页面，也不要用标题、简介、搜索结果或同主题资料替代视频证据。**

分析本地文件：

```bash
python3 -m watchvideo analyze ./video.mp4 -o analysis/local
```

输出完成后先看：

```bash
sed -n '1,120p' analysis/demo/report.md
```

网络视频的 `report.md` 会包含 `下载诊断`，`report.json` 和 `summary-input.md` 会包含同一组下载尝试。下载失败且没有正常报告时，先读 `failure.md` / `failure.json`，再说明卡在普通 `yt-dlp`、浏览器 cookies 重试、SSR 解析还是直链下载。

如果报告里出现 `清理记录` 且状态为 `deleted`，说明远程下载 MP4 已按默认规则清理；不要把它当成证据缺失。继续读取字幕、转写、关键帧、OCR 和时间线。

如果 `字幕文件数` 为 `0`，CLI 会先尝试系统 `whisper`，再按默认配置准备 `.tools/whisper.cpp` 转写。只有转写准备失败或被禁用时，报告才会出现“没有可用字幕”的限制。

`report.md` 的 `转写信息` 会记录 ASR 来源、模型、语言参数、prompt 使用情况和逐字稿文件。摘要偏口播内容时，应先看这个区块判断可信度。

## 默认自动准备 whisper.cpp 转字幕

如果系统没有 `whisper` CLI，`analyze` 会在需要转写时自动把 `whisper.cpp` 准备到 skill 仓库的 `.tools/whisper.cpp`，并下载 `base` 模型。它不会安装系统级依赖。

自动准备依赖：

```text
git
bash
cmake（系统缺失时会尝试安装到 .tools/.venv）
```

这些目录已在 `.gitignore` 中忽略：

```text
.tools/
.venv/
analysis/
```

日常用法只需要正常分析：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --whisper-prompt "视频里的领域术语、产品名、人名或技术词" \
  --language zh \
  --max-keyframes 80 \
  -o analysis/demo
```

禁用自动准备：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --no-auto-transcribe-setup \
  -o analysis/demo
```

保留远程下载 MP4：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --keep-video \
  -o analysis/demo
```

把工具缓存放到指定目录：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --tools-dir "$(pwd)/.tools" \
  --whisper-prompt "视频里的领域术语、产品名、人名或技术词" \
  --language zh \
  -o analysis/demo
```

如果需要预装或手工排查，可以自己构建 `whisper.cpp`，再显式传入二进制和模型路径：

```bash
PROJECT_ROOT="$(pwd)"
mkdir -p .tools
git clone --depth 1 https://github.com/ggerganov/whisper.cpp .tools/whisper.cpp
cd .tools/whisper.cpp
bash models/download-ggml-model.sh base
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j 6
cd "$PROJECT_ROOT"
```

显式使用预装路径：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --whisper-cpp-bin .tools/whisper.cpp/build/bin/whisper-cli \
  --whisper-model .tools/whisper.cpp/models/ggml-base.bin \
  --whisper-prompt "视频里的领域术语、产品名、人名或技术词" \
  --language zh \
  -o analysis/demo
```

`analyze` 会在 `transcript/audio.wav` 留下抽出的音频；也可以单独运行：

```bash
.tools/whisper.cpp/build/bin/whisper-cli \
  -m .tools/whisper.cpp/models/ggml-base.bin \
  -f analysis/demo/transcript/audio.wav \
  -l zh \
  -t 8 \
  -osrt \
  -otxt \
  -of analysis/demo/transcript/base \
  --prompt "视频里的领域术语、产品名、人名或技术词"
```

然后让 Codex 读取：

```text
analysis/demo/report.md
analysis/demo/transcript/base.srt
analysis/demo/keyframes/
```

并要求它输出：

- 一句话总结：主张、适用场景、核心结论；
- 视频主线：3-6 个带时间戳的论证节点；
- 核心概念拆解：概念、定义、边界、例子、为什么重要、视频证据；
- 常见误区：误区、为什么错、正确说法、证据；
- 可执行方法：前提、步骤、检查清单、适用/不适用场景；
- 面试回答模板：30 秒版、2 分钟版、追问应对、不推荐回答；
- 转写校正说明：可疑原文、建议校正、置信度、校正依据。

总结、分析、看懂或“讲了什么”类请求完成后，默认输出**文档级总结**，把最终内容写回 `report.md` 的 `视频内容总结` 区块；当前环境有 `outputs/` 这类用户可见目录时，也同步生成 Markdown 交付文件。只有用户明确要求不要写文件时才跳过。**不要用标题、简介、搜索结果或同主题材料补内容。** 某一节缺少视频证据时，保留标题并写“视频未明确提到”。报告里不要逐张列出关键帧路径或 score；只保留关键帧数量和目录。

## 生成摘要输入包

`summarize` 会把 `report.json` 里的元信息、warning、下载诊断、转写信息、关键帧时间戳和字幕 cue 按时间段整理成 Markdown，并加入最终总结的写作要求。技术类、面试类、教程类或方法论类视频会默认提示 Agent 使用上面的七段式结构。**它不调用任何 LLM**。

```bash
python3 -m watchvideo summarize analysis/demo/report.json \
  -o analysis/demo/summary-input.md \
  --chunk-seconds 300
```

然后让 Codex 读取：

```text
analysis/demo/report.md
analysis/demo/summary-input.md
analysis/demo/transcript/base.srt
analysis/demo/keyframes/
```

## OCR

默认不会跑 OCR。需要识别关键帧里的画面文字时启用：

```bash
python3 -m watchvideo analyze ./video.mp4 \
  --ocr \
  -o analysis/local
```

如果没有安装 `tesseract`，报告会记录 warning，主流程继续完成。

## 开发验证

运行单元测试：

```bash
python3 -m unittest discover -s tests -v
```

检查语法编译：

```bash
python3 -m compileall watchvideo tests
```

查看工作区状态：

```bash
git status --short --ignored
```

不要把这些目录加入提交：

```text
analysis/
.tools/
.venv/
__pycache__/
```

## 任务收尾检查

长视频下载、编译和语音转写会让电脑发热。每次跑完任务后，可以用 CLI 检查是否还有残留高负载进程：

```bash
python3 -m watchvideo processes
```

也可以让 `analyze` 结束时自动打印检查结果：

```bash
python3 -m watchvideo analyze ./video.mp4 --check-processes -o analysis/local
```

如果显示“未发现 watchvideo 相关进程”，说明没有匹配的残留任务。

如果确认某个进程是本次任务遗留，再手动停止它：

```bash
kill <pid>
```

不要对不认识的进程执行 `kill -9`。先确认命令、路径和 PID 属于本项目任务。
