from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SkillDocsTests(unittest.TestCase):
    def test_summary_requests_persist_to_report_unless_user_opts_out(self):
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        artifacts_text = (ROOT / "references" / "artifacts.md").read_text(
            encoding="utf-8"
        )
        combined = f"{skill_text}\n{artifacts_text}"

        self.assertIn("总结/分析/看懂/讲了什么", combined)
        self.assertIn("must write", combined)
        self.assertIn("unless the user explicitly asks not to write files", combined)
        self.assertIn("## 视频内容总结", combined)

    def test_plain_summary_requests_require_document_grade_deliverable(self):
        skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        artifacts_text = (ROOT / "references" / "artifacts.md").read_text(
            encoding="utf-8"
        )
        scenarios_text = (ROOT / "evals" / "skill_scenarios.md").read_text(
            encoding="utf-8"
        )
        combined = f"{skill_text}\n{artifacts_text}\n{scenarios_text}"

        self.assertIn("document-grade", combined)
        self.assertIn("not an abbreviated chat answer", combined)
        self.assertIn("mirror it to `outputs/`", combined)
        self.assertIn("普通提问和文档提问输出质量一致", combined)

    def test_public_readme_keeps_promotion_entry_points(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        promotion = (ROOT / "docs" / "PROMOTION.md").read_text(encoding="utf-8")
        examples = (ROOT / "examples" / "README.md").read_text(encoding="utf-8")

        self.assertIn("Evidence-first video understanding skill for Codex", readme)
        self.assertIn("[中文](README.zh-CN.md)", readme)
        self.assertIn("examples/technical-interview-summary.en.md", readme)
        self.assertIn("docs/PROMOTION.md", readme)
        self.assertIn("No video evidence -> no summary", promotion)
        self.assertIn("sanitized demo materials", examples)

    def test_public_docs_are_english_first_without_dropping_chinese_materials(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        promotion = (ROOT / "docs" / "PROMOTION.md").read_text(encoding="utf-8")

        self.assertIn("## Why This Exists", readme)
        self.assertIn("## Quick Start", readme)
        self.assertIn("## Chinese Community Copy", promotion)
        self.assertTrue((ROOT / "examples" / "technical-interview-summary.en.md").exists())
        self.assertTrue((ROOT / "examples" / "technical-interview-summary.zh.md").exists())
        self.assertTrue((ROOT / "examples" / "failure-report.en.md").exists())
        self.assertTrue((ROOT / "examples" / "failure-report.zh.md").exists())

        publishing = (ROOT / "docs" / "PUBLISHING.md").read_text(encoding="utf-8")
        self.assertIn("README.zh-CN.md", publishing)


if __name__ == "__main__":
    unittest.main()
