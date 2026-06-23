# 操作手册

本文记录本地使用流程、转写流程、验证命令和任务收尾检查。

## 基础分析

检查环境：

```bash
python3 -m watchvideo doctor
```

分析视频链接：

```bash
python3 -m watchvideo analyze "https://example.com/video" -o analysis/demo
```

分析本地文件：

```bash
python3 -m watchvideo analyze ./video.mp4 -o analysis/local
```

输出完成后先看：

```bash
sed -n '1,120p' analysis/demo/report.md
```

如果 `字幕文件数` 为 `0`，且报告里出现“没有可用字幕”，说明需要走音频转写。

## 自动使用 whisper.cpp 转字幕

如果系统没有 `whisper` CLI，可以在当前仓库内构建 `whisper.cpp`，再把二进制和模型路径传给 `analyze`。

这些目录已在 `.gitignore` 中忽略：

```text
.tools/
.venv/
analysis/
```

准备构建工具：

```bash
PROJECT_ROOT="$(pwd)"
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip cmake
```

下载并构建 `whisper.cpp`：

```bash
mkdir -p .tools
git clone --depth 1 https://github.com/ggerganov/whisper.cpp .tools/whisper.cpp
cd .tools/whisper.cpp
bash models/download-ggml-model.sh base
PATH="$PROJECT_ROOT/.venv/bin:$PATH" cmake -B build -DCMAKE_BUILD_TYPE=Release
PATH="$PROJECT_ROOT/.venv/bin:$PATH" cmake --build build --config Release -j 6
cd "$PROJECT_ROOT"
```

自动分析并转写：

```bash
python3 -m watchvideo analyze "https://example.com/video" \
  --whisper-cpp-bin .tools/whisper.cpp/build/bin/whisper-cli \
  --whisper-model .tools/whisper.cpp/models/ggml-base.bin \
  --whisper-prompt "Prompt, Loop Engineering, Agent, Webhook, Cron job, Claude Code, Codex, AI 编程, skill, GitHub" \
  --language zh \
  --max-keyframes 80 \
  -o analysis/demo
```

如果需要手工排查 `whisper.cpp`，`analyze` 会在 `transcript/audio.wav` 留下抽出的音频；也可以单独运行：

```bash
.tools/whisper.cpp/build/bin/whisper-cli \
  -m .tools/whisper.cpp/models/ggml-base.bin \
  -f analysis/demo/transcript/audio.wav \
  -l zh \
  -t 8 \
  -osrt \
  -otxt \
  -of analysis/demo/transcript/base \
  --prompt "Prompt, Loop Engineering, Agent, Webhook, Cron job, Claude Code, Codex, AI 编程, skill, GitHub"
```

然后让 Codex 读取：

```text
analysis/demo/report.md
analysis/demo/transcript/base.srt
analysis/demo/keyframes/
```

并要求它输出：

- 一句话总结；
- 分段摘要；
- 关键观点；
- 需要人工确认的可疑转写。

总结完成后，把最终内容写回 `report.md` 的 `视频内容总结` 区块。报告里不要逐张列出关键帧路径或 score；只保留关键帧数量和目录。

## 生成摘要输入包

`summarize` 会把 `report.json` 里的元信息、warning、关键帧目录和字幕 cue 按时间段整理成 Markdown。**它不调用任何 LLM**。

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

## 抖音验证记录

对链接 `https://v.douyin.com/Iny_KZKsoe8/` 的实测结果：

- `yt-dlp` 下载成功；
- 视频实际时长是 `20:24`；
- 分辨率是 `1280x720`；
- 平台字幕为 `0`；
- `whisper.cpp base` 生成了 `174` 条字幕，约 `7676` 字；
- `--keyframe-interval 5` 生成了 `245` 张关键帧，数量偏多。

这个验证说明下载、探测、抽帧、转写、Codex 总结的组合流程可用。现在 CLI 已补 `whisper.cpp` 自动接入和关键帧数量限制。

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
