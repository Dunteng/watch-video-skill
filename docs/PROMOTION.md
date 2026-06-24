# Promotion Kit

This file contains public launch copy, positioning, and distribution checklists for `watchvideo`. The goal is to make developers quickly understand that this is not a generic video summarizer; it is an **evidence-first video understanding skill**.

## One-Line Positioning

English:

```text
Evidence-first video understanding skill for Codex: download, transcribe, keyframe, OCR, and summarize only from evidence.
```

Chinese:

```text
一个让 Codex 真正“先拿证据再总结”的视频理解 skill：下载、转写、抽关键帧、OCR，拿不到证据就不瞎猜。
```

## GitHub Repository Packaging

Suggested repository description:

```text
Evidence-first video understanding skill for Codex: yt-dlp, Douyin SSR fallback, local whisper.cpp, keyframes, OCR, and grounded reports.
```

Suggested GitHub topics:

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

The README first screen should keep satisfying these requirements:

- Explain within 10 seconds that this is a Codex skill plus local CLI.
- Make the key difference explicit: **do not summarize from title, description, or search results**.
- Include install commands, the shortest usable prompt, and example report links.
- Include a failure-report example showing how the workflow stops without evidence.
- State limitations clearly; do not imply that every video platform is supported.

## Demo Video Script

Record a 45-60 second GIF or short video for the README and social posts.

Current public demo URL:

```text
https://www.youtube.com/watch?v=J6CHZWoygeM
```

Local verification result on 2026-06-24:

- Title: `The React + AI Stack for 2026`
- Duration: `00:06:40`
- Plain `yt-dlp` was blocked by YouTube bot verification.
- The CLI retried with Chrome cookies and succeeded.
- Platform subtitle download failed, then local `whisper.cpp` with the `base` model transcribed the audio.
- `23` keyframes were extracted.
- The remote MP4 was deleted by the default cleanup policy.
- Analysis directory: `analysis/demo-youtube-j6chzwoygem`; it is ignored by `.gitignore` and should not be committed.

### Shot List

1. `0-8s`: Show the prompt.

   ```text
   Use $watch-video to summarize this technical video: https://example.com/video
   ```

2. `8-18s`: Show the CLI run, especially `yt-dlp`, transcription, keyframes, and `report.md`.
3. `18-30s`: Open `report.md`, showing evidence quality, download diagnostics, and transcription metadata.
4. `30-45s`: Show the final video summary with one-sentence summary, throughline, concepts, and interview template.
5. `45-60s`: Show the failure-report rule: `Do not summarize from title, description, or search results.`

### On-Screen Keywords

- Evidence-first
- report.md
- transcript
- keyframes
- download diagnostics
- no evidence, no summary

## Show HN

Title:

```text
Show HN: A Codex skill that makes agents watch videos before summarizing them
```

First comment:

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

Title:

```text
I made a Codex skill that refuses to summarize videos without evidence
```

Body:

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

## Chinese Community Copy

Use this section for V2EX, Jike, Zhihu, WeChat, or other Chinese-speaking communities.

### V2EX

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

## Awesome List PR Copy

Title:

```text
Add watchvideo evidence-first video analysis skill
```

Body:

```text
This PR adds watchvideo, a Codex skill + local CLI for evidence-first video analysis.

It helps Codex summarize videos only after producing evidence: downloaded/local video, subtitles or local transcription, keyframes, optional OCR, and structured reports. If video evidence cannot be produced, it writes a failure report and instructs the agent not to summarize from title/description/search results.

Repository: https://github.com/Dunteng/watch-video-skill
```

## Launch Sequence

1. Prepare the GitHub README and examples.
2. Set the repository description and topics.
3. Publish a GitHub release such as `v0.1.0`.
4. Record a 45-60 second demo GIF.
5. Submit to awesome lists before posting broadly to communities.
6. Ask for concrete feedback: download failure samples, skill loopholes, and report structure.
7. Turn feedback into issues and fix the first real problems quickly.

## What Not To Claim

- Do not say "supports any video."
- Do not say "fully understands every platform automatically."
- Do not upload real user videos, subtitles, keyframes, cookies, or private links.
- Do not market it only as "video summarization"; that positioning is too generic.
- Do not hide limitations: platform anti-bot checks, `yt-dlp` / `ffmpeg` dependencies, and no-evidence stops.

## Materials Needed From The Maintainer

- A public video URL, preferably technical, interview, or tutorial content.
- A README-top demo GIF or short screen recording.
- Repository topics and description set from the owner account or authorized GitHub CLI/API session.
- Show HN should be posted from the maintainer's own account, not by a proxy account.
