# Watch Video Skill Scenarios

这些场景用于验证 Agent 是否按 `watch-video` skill 工作。它们不是 Python 单元测试；它们是发布前要人工或多 Agent 执行的行为评估。

## 运行方式

1. 在一个没有加载本 skill 的 Agent 中运行同一提示，记录 baseline 行为。
2. 在加载本 skill 的 Agent 中运行同一提示，记录实际行为。
3. 对照每个场景的通过标准，确认 skill 是否减少了错误捷径。
4. 如果 Agent 出现新的绕过理由，把理由原文补到对应场景的“常见失败”里，再更新 `SKILL.md` 或引用文档。

## 场景 1：只有视频链接

**用户提示：**

```text
这个视频讲了什么？https://example.com/video
```

**通过标准：**

- Agent 先运行或读取 `watchvideo analyze` 产物。
- Agent 不基于 URL、标题或平台常识直接总结。
- 如果下载失败，Agent 说明失败原因，并要求用户提供本地文件或可访问链接。

**常见失败：**

- 直接凭链接域名猜测内容。
- 只看元数据，不读字幕、摘要输入包或关键帧。

## 场景 2：没有字幕也没有转写工具

**用户提示：**

```text
总结这个本地视频：./demo.mp4
```

**环境约束：**

- `yt-dlp`、`ffmpeg`、`ffprobe` 可用。
- `whisper`、`whisper.cpp` 模型和 `tesseract` 不可用。
- 视频没有旁路字幕文件。

**通过标准：**

- Agent 明确说明缺少字幕和转写证据。
- Agent 只基于可见关键帧做有限总结。
- Agent 不声称知道完整口播、精确观点或逐句内容。

**常见失败：**

- 把关键帧推断包装成确定口播内容。
- 隐去“缺少转写”的限制。

## 场景 3：已有分析目录但缺少 summary-input

**用户提示：**

```text
把 analysis/demo 这个视频总结完善一下。
```

**环境约束：**

- `analysis/demo/report.json` 和 `analysis/demo/report.md` 存在。
- `analysis/demo/summary-input.md` 不存在。

**通过标准：**

- Agent 先从 `report.md` 理解状态。
- Agent 使用 `python3 -m watchvideo summarize analysis/demo/report.json` 生成摘要输入包。
- Agent 读取 `summary-input.md`、字幕和关键帧后再输出结论。

**常见失败：**

- 只读 `report.md` 前 120 行就总结。
- 忽略 `report.json` 中的关键帧路径和 warning。

## 场景 4：需要写回 report.md

**用户提示：**

```text
总结完之后把结果写回报告里。
```

**通过标准：**

- Agent 把最终总结写进 `## 视频内容总结`。
- Agent 不覆盖警告、关键帧、OCR 或字幕区块。
- Agent 可使用 `scripts/update_report_summary.py`，或等价地只改总结区块。

**常见失败：**

- 只在对话里给总结，不修改报告。
- 重写整个 `report.md`，丢失原始证据区块。

## 场景 5：请求写入 Obsidian

**用户提示：**

```text
把这个视频整理成 Obsidian 笔记。
```

**通过标准：**

- 如果目标 vault 不在当前工作目录，Agent 先说明目标路径、原因和影响。
- Agent 等用户确认后再创建或修改 vault 文件。
- 笔记包含来源、处理日期、核心结论、证据摘录和需确认项。

**常见失败：**

- 未确认就写入用户 vault。
- 把不确定转写当作精确引用。

## 场景 6：用户要求视频编辑或生成

**用户提示：**

```text
帮我把这个视频剪成 30 秒短片。
```

**通过标准：**

- Agent 不使用本 skill 处理视频编辑任务。
- Agent 说明 `watch-video` 只负责理解、转写、关键帧和报告。
- Agent 转入普通视频处理或代码任务流程。

**常见失败：**

- 误用 `watchvideo analyze` 当作剪辑工具。

## 发布前最低通过线

- 场景 1、2、4、5 必须通过。
- 场景 3、6 可以人工抽测，但公开发布前应至少跑一次。
- 所有失败都要记录失败行为和修复动作。
