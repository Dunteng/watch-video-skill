# watchvideo

`watchvideo` 是一个给 Codex 辅助使用的视频分析工作台原型。它把本地视频或网络视频链接整理成可读材料，再交给 Codex 或其他 LLM 做理解和总结。

这个仓库同时是：

- **Codex Skill**：根目录的 `SKILL.md` 负责告诉 Agent 何时使用、如何运行和如何总结视频。
- **Python CLI 工具**：`watchvideo/` 包含可直接运行的本地视频分析代码。

作为 Skill 使用时，Agent 应从本仓库根目录运行 `python3 -m watchvideo ...`，不需要依赖旧项目目录。

当前仓库仍不是完整的一键式视频理解产品。准确边界是：

- **脚本自动做**：下载视频、下载平台字幕、探测视频信息、解析字幕、抽关键帧、生成报告。
- **脚本可选做**：调用系统 `whisper` CLI、调用本地 `whisper.cpp`、限制最大关键帧数量、对关键帧做 OCR、生成摘要输入包、检查疑似残留进程。
- **Codex 参与做**：读取 `report.md`、`summary-input.md`、字幕和关键帧，提炼“视频讲了什么”。
- **暂未自动做**：云端 LLM 摘要、复杂场景检测、自动结束残留进程。

## 能力

输入可以是：

- 本地视频文件，例如 `./video.mp4`；
- 网络视频链接，例如抖音短链、YouTube 链接或其他 `yt-dlp` 支持的链接。

输出包含：

- `report.json`：结构化报告，适合继续给程序处理；
- `report.md`：人类可读报告，包含字幕文本和可选的视频内容总结；
- `video/`：网络视频下载结果；
- `subtitles/`：平台字幕或自动字幕；
- `transcript/`：音频转写结果，如果转写成功；
- `keyframes/`：从稳定区域里选出的关键帧。
- `summary-input.md`：由 `summarize` 命令生成，供 Codex 或其他 LLM 阅读。

## 环境要求

必需：

```bash
python3
yt-dlp
ffmpeg
ffprobe
```

可选：

```bash
whisper
tesseract
whisper.cpp 的 whisper-cli
whisper.cpp 模型文件
```

说明：

- 系统 Whisper 转写会自动查找名为 `whisper` 的 CLI。
- `whisper.cpp` 通过 `--whisper-cpp-bin` 和 `--whisper-model` 接入，流程见 [docs/OPERATIONS.md](docs/OPERATIONS.md)。
- `tesseract` 通过 `--ocr` 启用；默认关闭，避免长视频额外耗时。

## 快速使用

检查本机工具：

```bash
python3 -m watchvideo doctor
```

分析本地视频：

```bash
python3 -m watchvideo analyze ./video.mp4 -o analysis/local-video
```

分析网络视频：

```bash
python3 -m watchvideo analyze "https://example.com/video" -o analysis/remote-video
```

常用参数：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --max-height 1080 \
  --keyframe-interval 10 \
  --max-keyframes 80 \
  --sub-lang "zh.*" \
  --sub-lang "en.*" \
  -o analysis/demo
```

使用本地 `whisper.cpp`：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --whisper-cpp-bin .tools/whisper.cpp/build/bin/whisper-cli \
  --whisper-model .tools/whisper.cpp/models/ggml-base.bin \
  --whisper-prompt "Agent, Codex, AI 编程" \
  --language zh \
  -o analysis/demo
```

启用 OCR 和结束后进程检查：

```bash
python3 -m watchvideo analyze ./video.mp4 \
  --ocr \
  --check-processes \
  -o analysis/local-video
```

生成摘要输入包：

```bash
python3 -m watchvideo summarize analysis/demo/report.json \
  -o analysis/demo/summary-input.md \
  --chunk-seconds 300
```

单独检查疑似残留进程：

```bash
python3 -m watchvideo processes
```

## 用 Codex 得到视频摘要

当前推荐流程：

1. 先跑 `analyze` 生成视频、字幕和关键帧材料。
2. 如果平台没有字幕，优先用 `--whisper-cpp-bin` 和 `--whisper-model` 让 CLI 自动转写。
3. 跑 `summarize` 生成 `summary-input.md`。
4. 让 Codex 读取 `report.md`、`summary-input.md`、`transcript/*.srt` 和关键帧，输出总摘要、分段摘要和关键观点。
5. 把最终“视频讲了什么”的内容写回 `report.md` 的 `视频内容总结` 区块。

脚本本身仍只负责材料准备和输入包整理，最后的中文理解和总结来自 Codex。

报告规范：

- `report.md` 不逐张列出关键帧路径或 score，只保留关键帧数量和目录。
- 关键帧明细保留在 `report.json`，供程序或 Codex 需要时读取。
- 最终给人的视频内容总结必须写进 `report.md`，不要只留在对话里。

## 项目文档

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)：模块边界和数据流。
- [docs/OPERATIONS.md](docs/OPERATIONS.md)：本地操作、手动转写、验证和收尾检查。
- [docs/PUBLISHING.md](docs/PUBLISHING.md)：上传 GitHub 前的文件清单、验证步骤和隐私检查。
- [evals/skill_scenarios.md](evals/skill_scenarios.md)：验证 Agent 是否正确使用本 skill 的行为场景。

## 开发验证

本项目暂时不依赖 pytest，使用标准库测试：

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall watchvideo tests
```

当前本机没有 `ruff`、`mypy`、`pytest`。如果之后引入这些开发依赖，再把对应命令加入验证流程。

## 长期维护

这个仓库作为长期通用 skill 时，`tests/`、`evals/`、`docs/` 都应该随源码一起保留并上传。不要上传 `analysis/`、本地模型、真实视频、转写结果、关键帧、`.env` 或用户笔记。
