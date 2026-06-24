# 发布清单

本文记录把 `watch-video` 作为长期通用 skill 上传到 GitHub 前需要检查的内容。

## 应上传

- `SKILL.md`
- `references/`
- `watchvideo/`
- `scripts/`
- `tests/`
- `evals/`
- `docs/`
- `examples/`
- `README.md`
- `README.zh-CN.md`
- `pyproject.toml`
- `.gitignore`
- `agents/openai.yaml`
- `LICENSE`

## 不应上传

- `analysis/`、`reports/`、`keyframes/`、`subtitles/`、`transcript/`、`video/`
- `.tools/`、`.models/`、`.venv/`
- 真实视频、音频、字幕、关键帧、转写报告
- Cookie、token、`.env`、私有链接和平台登录材料
- 用户 Obsidian vault 里的笔记

## 发布前验证

运行代码验证：

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall watchvideo tests
python3 -m watchvideo doctor
```

`doctor` 输出中不应出现 `REQUIRED_MISSING`。`OPTIONAL_MISSING` 可以接受，但发布说明应如实描述缺少的能力；缺少 `git` 或 `bash` 会影响自动准备 `whisper.cpp`，缺少 `cmake` 会触发 `.tools/.venv` 兜底。

运行 skill 行为验证：

```text
按 evals/skill_scenarios.md 抽测至少场景 1、1B、2、4、5、7。
```

检查 Git 状态：

```bash
git status --short --ignored
```

只允许被忽略项中出现本地缓存、运行产物、模型、媒体或虚拟环境。

## 公开仓库注意事项

- 不要把示例链接换成真实视频链接，除非确认链接可公开、可复现且不含隐私。
- 不要把 `analysis/` 里的报告作为 fixture 提交；需要 fixture 时使用脱敏短样本或 `examples/` 中的虚构示例。
- README 应明确：CLI 准备证据，最终理解由 Agent 读取证据后完成。
- README should be English-first for GitHub discovery, with `README.zh-CN.md` linked at the top.
- Public examples should keep English `.en.md` files and Chinese `.zh.md` files when both audiences matter.
- 修改 `SKILL.md` 或 `references/` 后，应同步更新 `evals/skill_scenarios.md`。
- 修改公开定位、示例或社区文案后，应同步更新 `docs/PROMOTION.md`。

## 版本发布建议

首次公开发布前：

1. 确认许可证符合预期。
2. 确认 `.gitignore` 能挡住大文件和隐私材料。
3. 跑完代码测试和行为场景。
4. 用全新目录克隆仓库，按 README 从零运行一次 `doctor` 和单元测试。
