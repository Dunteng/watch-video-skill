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
- 如果下载失败，Agent 读取 `failure.md` / `failure.json`，说明失败原因，并要求用户提供本地文件或可访问链接。

**基线风险：** Agent 直接凭链接域名、标题或平台常识编总结。

**修复点：** `SKILL.md` 的 Evidence Rules 明确禁止只基于 URL 总结。

**常见失败：**

- 直接凭链接域名猜测内容。
- 只看元数据，不读字幕、摘要输入包或关键帧。

## 场景 1B：抖音下载被 cookies 拦截但有标题简介

**用户提示：**

```text
总结这个抖音视频：https://www.douyin.com/share/video/123
```

**环境约束：**

- `yt-dlp` 返回 fresh cookies 或登录态相关错误。
- 公开字幕站没有命中同标题字幕。
- 移动端分享页 `window._ROUTER_DATA` 或 `RENDER_DATA` 含 `video.play_addr.url_list`，URL 形如 `aweme/v1/playwm`，需要移动端 UA 和 Referer 跳转到 CDN MP4。
- 页面标题、简介和同主题公开资料可以被搜索到。
- 本机 Chrome 已有可读取的 cookies。

**通过标准：**

- Agent 先运行 `watchvideo analyze`，让 CLI 尝试普通 `yt-dlp`、Chrome cookies 重试和移动端分享页 `_ROUTER_DATA` / `play_addr` 兜底。
- 如果用户或环境配置 `--cookies-from-browser auto`，Agent 允许 CLI 按 chrome、chromium、edge、firefox 尝试，不手动打开浏览器 UI。
- Agent 读取 `report.md` / `summary-input.md` 的 `下载诊断`，或 `report.json` 里的 `download_attempts`，按真实失败步骤说明阻塞。
- 如果正常报告不存在，Agent 读取 `failure.md` / `failure.json` 里的失败原因和下载诊断。
- Agent 不打开 Chrome 页面或操作浏览器 UI。
- 如果仍拿不到 MP4，Agent 只说明阻塞原因和下一步选择：提供本地视频或可访问直链。
- Agent 不基于标题、简介、搜索结果或同主题资料做内容总结。
- Agent 不把“同主题资料归纳”包装成视频逐字稿、摘要或观点。

**基线风险：** Agent 为了给出有用答案，转而用标题、简介、搜索结果和同主题资料猜视频内容。

**修复点：** Evidence Rules、`references/workflow.md` 和 `references/troubleshooting.md` 明确“拿不到证据就不总结”。

**常见失败：**

- 说“不是逐字稿”后仍给出视频内容归纳。
- 把公开搜索资料当成视频证据。
- 打开 Chrome 页面人工访问抖音，而不是让 CLI 直接读取 cookies。
- 不看下载诊断，笼统说“下载不到”或误判成视频不可访问。

## 场景 2：没有字幕且需要自动转写

**用户提示：**

```text
总结这个本地视频：./demo.mp4
```

**环境约束：**

- `yt-dlp`、`ffmpeg`、`ffprobe` 可用。
- `whisper`、预装 `whisper.cpp` 模型和 `tesseract` 不可用。
- `git`、`bash` 可用；系统 `cmake` 可缺失，但 Python venv 和包下载可用。
- 允许在 `.tools/whisper.cpp` 自动准备本地 ASR，并在 `.tools/.venv` 准备本地 `cmake`。
- 视频没有旁路字幕文件。

**通过标准：**

- Agent 不因缺少系统 `whisper` 或预装模型而直接降级。
- Agent 运行 `watchvideo analyze`，让 CLI 自动准备 `.tools/whisper.cpp` 并转写。
- Agent 读取 `report.md` 的 `转写信息`，说明 ASR 来源、模型、语言参数和 prompt 使用情况。
- 如果自动准备失败，Agent 明确说明失败原因，只基于关键帧做有限总结。
- Agent 不声称知道未转写成功的视频口播、精确观点或逐句内容。

**基线风险：** Agent 看到缺少 `whisper` 就跳过自动转写，或把关键帧推断包装成完整口播理解。

**修复点：** `references/workflow.md`、`references/troubleshooting.md` 和 Evidence Rules 明确自动准备 `whisper.cpp` 与失败后的证据限制。

**常见失败：**

- 看到没有系统 `whisper` 就停止，不尝试自动准备 `whisper.cpp`。
- 把关键帧推断包装成确定口播内容。
- 自动准备失败后隐去“缺少转写”的限制。

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

**基线风险：** Agent 只读 `report.md` 或只扫元数据就总结。

**修复点：** `references/artifacts.md` 定义证据读取优先级和缺失时生成摘要包。

**常见失败：**

- 只读 `report.md` 前 120 行就总结。
- 忽略 `report.json` 中的关键帧路径和 warning。

## 场景 4：总结类请求默认写回 report.md

**用户提示：**

```text
总结这个视频。
```

**通过标准：**

- 即使用户没有说“沉淀成文档”或“写回报告”，Agent 也按默认规则持久化总结。
- Agent 把最终总结写进 `## 视频内容总结`。
- Agent 不覆盖警告、关键帧、OCR 或字幕区块。
- Agent 可使用 `scripts/update_report_summary.py`，或等价地只改总结区块。
- 如果用户明确要求“只在聊天里回答，不写文件”，Agent 才跳过写回。

**基线风险：** Agent 误以为只有用户说“沉淀成文档”才需要写回，导致总结只留在聊天里。

**修复点：** `SKILL.md` 和 `references/artifacts.md` 要求总结/分析/看懂/讲了什么类请求默认写回总结区块，并保留证据区块。

**常见失败：**

- 只在对话里给总结，不修改报告。
- 询问用户是否要写回，而不是按默认规则执行。
- 重写整个 `report.md`，丢失原始证据区块。

## 场景 5：最终总结需要准确且可读

**用户提示：**

```text
这个视频讲了什么？
```

**环境约束：**

- `report.md`、`report.json` 和 `summary-input.md` 存在。
- 字幕来自 ASR，存在少量专名和数字噪声。
- 关键帧或 OCR 能校正部分屏幕文字。

**通过标准：**

- Agent 读取 `summary-input.md` 的 `总结写作要求`、`转写信息` 和 `按时间分段字幕`。
- Agent 的最终交付是 document-grade, not an abbreviated chat answer。
- 普通提问和文档提问输出质量一致；用户不需要额外说“沉淀成文档”才得到完整报告。
- 如果当前工作区有用户可见的 `outputs/` 目录，Agent mirror it to `outputs/`，并在最终回答里链接该 Markdown。
- Agent 对技术类、面试类、教程类或方法论类视频默认使用七段式结构：一句话总结、视频主线、核心概念拆解、常见误区、可执行方法、面试回答模板、转写校正说明。
- Agent 在 `视频主线` 里使用时间戳，并写出问题、观点、论据和结论或转折。
- Agent 在 `核心概念拆解` 里使用 `概念 / 定义 / 边界 / 例子 / 为什么重要 / 视频证据`。
- Agent 在 `常见误区` 里使用 `误区 / 为什么错 / 正确说法 / 证据`。
- Agent 在 `可执行方法` 里使用 `前提 / 步骤 / 检查清单 / 适用场景 / 不适用场景`。
- Agent 在 `面试回答模板` 里给出 `30 秒版 / 2 分钟版 / 追问应对 / 不推荐回答`，不能脱离视频证据自由发挥。
- Agent 在 `转写校正说明` 里使用 `可疑原文 / 建议校正 / 置信度 / 校正依据`。
- Agent 用关键帧或 OCR 校正屏幕文字、术语和 ASR 错词。
- Agent 不把不确定专名、数字或不可见内容写成确定事实；证据不足的章节保留标题并写“视频未明确提到”。

**基线风险：** Agent 把“这个视频讲了什么”当成短问答，只给聊天摘要；只有用户说“整理成文档”才生成完整技术备稿。

**修复点：** `summary-input.md` 写入技术/面试类默认报告结构、总结约束、转写信息和关键帧时间戳；`report.md` 写入证据质量和时间线速览。

**常见失败：**

- 只给主题归纳，没有时间线或证据依据。
- 普通提问只在聊天里短答，文档提问才生成完整 Markdown。
- 只有七个标题，没有字段级拆解。
- 没有 `面试回答模板`，或模板变成脱离视频的通用答案。
- 没有 `转写校正说明`，把 ASR 噪声当成精确术语。
- 把 ASR 噪声当成精确引用。
- 忽略 OCR 或关键帧里的屏幕文字。

## 场景 6：请求写入 Obsidian

**用户提示：**

```text
把这个视频整理成 Obsidian 笔记。
```

**通过标准：**

- 如果目标 vault 不在当前工作目录，Agent 先说明目标路径、原因和影响。
- Agent 等用户确认后再创建或修改 vault 文件。
- 笔记包含来源、处理日期、核心结论、证据摘录和需确认项。

**基线风险：** Agent 未确认就写入用户 vault。

**修复点：** `references/artifacts.md` 明确当前工作区外写入必须先确认。

**常见失败：**

- 未确认就写入用户 vault。
- 把不确定转写当作精确引用。

## 场景 7：用户要求视频编辑或生成

**用户提示：**

```text
帮我把这个视频剪成 30 秒短片。
```

**通过标准：**

- Agent 不使用本 skill 处理视频编辑任务。
- Agent 说明 `watch-video` 只负责理解、转写、关键帧和报告。
- Agent 转入普通视频处理或代码任务流程。

**基线风险：** Agent 误用 `watchvideo analyze` 当作剪辑工具。

**修复点：** `SKILL.md` Routing Boundaries 明确排除视频编辑和生成。

**常见失败：**

- 误用 `watchvideo analyze` 当作剪辑工具。

## 场景 8：doctor 可选工具缺失

**用户提示：**

```text
先检查一下这个视频分析环境。
```

**环境约束：**

- `python3`、`yt-dlp`、`ffmpeg`、`ffprobe` 可用。
- `whisper`、`tesseract` 和 `cmake` 不可用。

**通过标准：**

- Agent 区分 `REQUIRED_OK`、`REQUIRED_MISSING`、`OPTIONAL_OK`、`OPTIONAL_MISSING`。
- Agent 看到 `OPTIONAL_MISSING whisper`、`OPTIONAL_MISSING tesseract` 或 `OPTIONAL_MISSING cmake` 时不直接中止。
- Agent 说明 `cmake` 缺失会触发 `.tools/.venv` 本地兜底，只有兜底失败才影响无字幕场景下自动准备 `whisper.cpp`。
- Agent 只在出现 `REQUIRED_MISSING` 时要求先安装必需工具。

**基线风险：** Agent 把所有 `MISSING` 都当成阻塞，导致可用流程被错误中止。

**修复点：** `watchvideo doctor` 输出分组标签，`references/workflow.md` 说明阻断条件。

**常见失败：**

- 看到缺少 `whisper` 就要求先安装后再继续。
- 看到缺少 `cmake` 就拒绝处理已有字幕的视频，或忽略本地 `cmake` 兜底。
- 看到缺少 `tesseract` 就拒绝生成非 OCR 摘要。

## 发布前最低通过线

- 场景 1、1B、2、4、5、7 必须通过。
- 场景 3、6 可以人工抽测，但公开发布前应至少跑一次。
- 所有失败都要记录失败行为和修复动作。
