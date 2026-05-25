import unittest

from app import (
    build_single_prompt_personal_note,
    chat_attachment_file_types,
    normalize_chat_prompt,
    split_assistant_sections,
    strip_think_blocks,
)


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

    def test_split_assistant_sections_folds_attachment_report(self) -> None:
        sections = split_assistant_sections(
            "核心回答。\n\n"
            "附件解析：\n"
            "- report.pdf：文本、OCR"
        )

        self.assertEqual(sections["answer"], "核心回答。")
        self.assertIn("report.pdf", sections["reasoning"])

    def test_build_single_prompt_personal_note_marks_single_turn_scope(self) -> None:
        note = build_single_prompt_personal_note("我对青霉素过敏，请以后提醒我。")

        self.assertIn("单次提问", note)
        self.assertIn("用户明确选择加入个人信息库", note)
        self.assertIn("青霉素过敏", note)

    def test_chat_attachment_file_types_are_streamlit_ready(self) -> None:
        file_types = chat_attachment_file_types()

        self.assertIn("pdf", file_types)
        self.assertIn("png", file_types)
        self.assertIn("webp", file_types)
        self.assertNotIn(".pdf", file_types)

    def test_normalize_chat_prompt_allows_attachment_only_question(self) -> None:
        self.assertEqual(normalize_chat_prompt("  二甲双胍怎么吃？ ", False), "二甲双胍怎么吃？")
        self.assertIn("本轮附件", normalize_chat_prompt("", True))
        self.assertEqual(normalize_chat_prompt("", False), "")


if __name__ == "__main__":
    unittest.main()
