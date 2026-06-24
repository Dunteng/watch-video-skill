# Promotion Kit

本文是 `watchvideo` 的公开宣传素材和发布执行清单。目标是让开发者快速理解它不是普通视频摘要工具，而是一个**证据优先的视频理解 skill**。

## 一句话定位

英文：

```text
Evidence-first video understanding skill for Codex: download, transcribe, keyframe, OCR, and summarize only from evidence.
```

中文：

```text
一个让 Codex 真正“先拿证据再总结”的视频理解 skill：下载、转写、抽关键帧、OCR，拿不到证据就不瞎猜。
```

## GitHub 仓库包装

建议仓库 description：

```text
Evidence-first video understanding skill for Codex: yt-dlp, Douyin SSR fallback, local whisper.cpp, keyframes, OCR, and grounded reports.
```

建议 GitHub topics：

```text
codex
codex-skills
agent-skills
video-analysis
video-transcription
whisper-cpp
yt-dlp
douyin
tiktok
ocr
keyframes
evidence-first
```

README 首屏需要持续满足：

- 10 秒内说明：这是 Codex skill + 本地 CLI。
- 明确差异：**不基于标题、简介、搜索结果总结**。
- 有安装命令、最短使用 prompt 和示例报告链接。
- 有失败报告示例，展示拿不到证据时如何停止。
- 有限制说明，避免宣传成“支持任何视频”。

## Demo 视频脚本

建议录一个 45-60 秒 GIF 或短视频，放到 README 顶部或社交帖里。

当前可用公开 demo 链接：

```text
https://www.youtube.com/watch?v=J6CHZWoygeM
```

本地验证结果（2026-06-24）：

- 标题：`The React + AI Stack for 2026`
- 时长：`00:06:40`
- 普通 `yt-dlp` 被 YouTube bot 校验拦截；
- CLI 使用 Chrome cookies 重试成功；
- 平台字幕下载失败，随后用本地 `whisper.cpp` `base` 模型转写；
- 抽取 `23` 张关键帧；
- 远程下载 MP4 已按默认策略删除；
- 分析目录：`analysis/demo-youtube-j6chzwoygem`，该目录被 `.gitignore` 忽略，不应提交。

### 分镜

1. `0-8s`：展示 prompt。

   ```text
   用 $watch-video 总结这个技术视频：https://example.com/video
   ```

2. `8-18s`：展示 CLI 运行，重点扫过 `yt-dlp`、转写、关键帧、`report.md`。
3. `18-30s`：打开 `report.md`，展示 `证据质量`、`下载诊断`、`转写信息`。
4. `30-45s`：展示最终 `视频内容总结`，包含“一句话总结 / 视频主线 / 核心概念拆解 / 面试回答模板”。
5. `45-60s`：展示失败报告一句话：`不要基于标题、简介或搜索结果总结视频内容。`

### 屏幕上要出现的关键词

- Evidence-first
- report.md
- transcript
- keyframes
- download diagnostics
- no evidence, no summary

## Show HN

标题：

```text
Show HN: A Codex skill that makes agents watch videos before summarizing them
```

首条评论：

```text
I built this because I kept seeing agents summarize videos from titles, descriptions, or search results instead of actual video evidence.

watchvideo is a Codex skill plus a local CLI. It downloads or reads the video, gets subtitles or transcribes with local Whisper/whisper.cpp, extracts keyframes, optionally runs OCR, and writes report.md / report.json / summary-input.md for Codex to read.

The main rule is: if it cannot produce video evidence, it refuses to summarize and writes a failure report instead.

Interesting details:
- yt-dlp first, then browser-cookie retry, then Douyin/mobile SSR play_addr fallback
- local whisper.cpp auto-setup when no transcript is available
- structured reports for technical/interview/tutorial videos
- remote MP4s are cleaned up after analysis by default

It is not a video editor, and it does not call a cloud LLM by itself. The CLI prepares evidence; Codex does the final synthesis.
```

## Reddit / r/codex

标题：

```text
I made a Codex skill that refuses to summarize videos without evidence
```

正文：

```text
I built watchvideo, a Codex skill + local CLI for evidence-first video analysis.

The problem: agents often summarize a video from the URL, page title, description, or search results. That is useful-looking but not actually video understanding.

watchvideo forces a stricter workflow:
- download/read the video
- get subtitles or transcribe locally with whisper / whisper.cpp
- extract keyframes and optionally OCR them
- write report.md, report.json, and summary-input.md
- if no MP4/transcript/keyframes exist, stop and write a failure report

It also includes Douyin/mobile SSR play_addr fallback, download diagnostics, technical/interview report templates, and automatic cleanup of remote MP4 downloads.

Repo: https://github.com/Dunteng/watch-video-skill

I would especially appreciate feedback on the skill instructions and failure cases where an agent still tries to guess from metadata.
```

## X / Twitter Thread

```text
I built a Codex skill that makes agents actually watch videos before summarizing them.

The rule is simple:
No video evidence -> no summary.

Most agents will happily summarize from a URL title, description, or search results. watchvideo forces a stricter pipeline:

1. download/read the video
2. get subtitles or transcribe locally
3. extract keyframes
4. optionally OCR visual text
5. write an evidence report for Codex

It produces:
- report.md
- report.json
- summary-input.md
- transcript files
- keyframes
- failure reports when evidence is missing

It also handles practical annoyances:
- yt-dlp first
- browser-cookie retry
- Douyin/mobile SSR play_addr fallback
- local whisper.cpp auto-setup
- remote MP4 cleanup after analysis

Repo:
https://github.com/Dunteng/watch-video-skill
```

## V2EX

标题：

```text
做了一个让 Codex 先拿视频证据再总结的 skill
```

正文：

```text
我做了一个 Codex skill + 本地 CLI，叫 watchvideo。

起因是我发现 Agent 在总结视频时很容易偷懒：下载不到视频后，转而根据标题、简介、搜索结果或同主题资料做归纳。这样看起来有用，但不是视频理解。

这个 skill 的规则比较硬：

- 必须先拿到 MP4、字幕/转写或关键帧证据；
- 没字幕时尝试系统 whisper，不行就自动准备本地 whisper.cpp；
- 抽关键帧，可选 OCR；
- 抖音这类链接在 yt-dlp 失败后，会尝试解析移动端分享页 SSR 里的 play_addr；
- 拿不到证据就只报告阻塞原因，不总结；
- 最终生成 report.md / report.json / summary-input.md，方便 Codex 写文档级总结。

项目地址：https://github.com/Dunteng/watch-video-skill

比较希望大家帮忙看两类问题：
1. skill 指令还有没有 Agent 容易钻空子的地方；
2. 不同平台的视频下载/转写失败时，失败报告是否足够清楚。
```

## Awesome List PR 文案

标题：

```text
Add watchvideo evidence-first video analysis skill
```

正文：

```text
This PR adds watchvideo, a Codex skill + local CLI for evidence-first video analysis.

It helps Codex summarize videos only after producing evidence: downloaded/local video, subtitles or local transcription, keyframes, optional OCR, and structured reports. If video evidence cannot be produced, it writes a failure report and instructs the agent not to summarize from title/description/search results.

Repository: https://github.com/Dunteng/watch-video-skill
```

## 发布节奏

1. GitHub README 和 examples 准备好。
2. 设置 repo description 和 topics。
3. 发一个 GitHub release，例如 `v0.1.0`。
4. 录制 45-60 秒 demo GIF。
5. 先投 awesome list，再发社区帖。
6. 社区帖里请求具体反馈：下载失败样本、skill 指令漏洞、报告结构。
7. 根据反馈开 issues，快速修第一批真实问题。

## 不要这样宣传

- 不要说“支持任何视频”。
- 不要说“完全自动理解所有平台视频”。
- 不要上传真实用户视频、字幕、关键帧、cookie 或私有链接。
- 不要只宣传“视频总结”，这个定位太泛。
- 不要回避限制：平台反爬、依赖 `yt-dlp` / `ffmpeg`、无证据时会停止。

## 需要用户配合的素材

- 一段可公开的视频 URL，最好是技术/面试/教程类。
- 一张或一段 README 顶部 demo GIF。
- GitHub repo topics 和 description 需要仓库 owner 在 GitHub 页面设置，或确认后用 GitHub CLI/API 设置。
- 如果要发 Show HN，需要用户本人账号发帖，避免看起来像代发广告。
