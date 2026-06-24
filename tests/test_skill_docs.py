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


if __name__ == "__main__":
    unittest.main()
