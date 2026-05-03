import unittest

from app import build_single_prompt_personal_note, split_assistant_sections, strip_think_blocks


class AppRenderingTests(unittest.TestCase):
    def test_split_assistant_sections_folds_evidence_and_sources(self) -> None:
        sections = split_assistant_sections(
            "核心回答。\n\n"
            "回答依据：\n"
            "- 命中厄贝沙坦。\n\n"
            "参考来源：\n"
            "- products.md | 片段：厄贝沙坦"
        )

        self.assertEqual(sections["answer"], "核心回答。")
        self.assertIn("命中厄贝沙坦", sections["reasoning"])
        self.assertIn("products.md", sections["sources"])

    def test_strip_think_blocks_hides_model_reasoning(self) -> None:
        content = "<think>隐藏推理</think>\n\n用户可见答案。"

        self.assertEqual(strip_think_blocks(content), "用户可见答案。")
        self.assertEqual(split_assistant_sections(content)["answer"], "用户可见答案。")

    def test_build_single_prompt_personal_note_marks_single_turn_scope(self) -> None:
        note = build_single_prompt_personal_note("我对青霉素过敏，请以后提醒我。")

        self.assertIn("单次提问", note)
        self.assertIn("用户明确选择加入个人信息库", note)
        self.assertIn("青霉素过敏", note)


if __name__ == "__main__":
    unittest.main()
