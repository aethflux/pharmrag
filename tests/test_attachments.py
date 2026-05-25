import unittest
from unittest.mock import patch

from config import APP_CONFIG
from rag.attachments import (
    AttachmentContext,
    build_attachments_prompt,
    build_personal_knowledge_attachment_summary,
    parse_attachment_bytes,
)
from rag.ocr import OcrUnavailableError


class AttachmentTests(unittest.TestCase):
    def test_parse_text_attachment_extracts_content(self) -> None:
        context = parse_attachment_bytes(
            "report.txt",
            "空腹血糖 7.2 mmol/L".encode("utf-8"),
            question="报告怎么看？",
        )

        self.assertTrue(context.can_reference)
        self.assertIn("空腹血糖", context.extracted_text)
        self.assertFalse(context.is_image)

    def test_parse_unsupported_attachment_returns_warning(self) -> None:
        context = parse_attachment_bytes("virus.exe", b"abc")

        self.assertFalse(context.can_reference)
        self.assertIn("不支持的附件类型", context.warnings[0])

    def test_parse_oversized_attachment_returns_warning(self) -> None:
        with patch.dict(APP_CONFIG, {"attachment_max_bytes": 3}):
            context = parse_attachment_bytes("large.txt", b"1234")

        self.assertFalse(context.can_reference)
        self.assertIn("附件超过大小限制", context.warnings[0])

    def test_image_attachment_uses_ocr_and_vision_summary(self) -> None:
        def fake_vision(data_url: str, question: str, filename: str) -> str:
            self.assertTrue(data_url.startswith("data:image/png;base64,"))
            self.assertEqual(filename, "drug.png")
            return "视觉摘要：可见药盒文字。"

        with patch("rag.attachments.image_bytes_to_text", return_value="OCR：药品名称"):
            context = parse_attachment_bytes(
                "drug.png",
                b"fake-image",
                content_type="image/png",
                question="这个药怎么吃？",
                vision_summarizer=fake_vision,
            )

        self.assertTrue(context.can_reference)
        self.assertTrue(context.is_image)
        self.assertIn("药品名称", context.ocr_text)
        self.assertIn("可见药盒文字", context.vision_summary)

    def test_image_attachment_records_ocr_failure_and_keeps_vision(self) -> None:
        with patch(
            "rag.attachments.image_bytes_to_text",
            side_effect=OcrUnavailableError("no tesseract"),
        ):
            context = parse_attachment_bytes(
                "wound.jpg",
                b"fake-image",
                content_type="image/jpeg",
                question="外伤怎么办？",
                vision_summarizer=lambda *_: "可见皮肤红肿。",
            )

        self.assertTrue(context.can_reference)
        self.assertIn("图片 OCR 不可用", context.warnings[0])
        self.assertIn("皮肤红肿", context.vision_summary)

    def test_build_prompt_and_personal_summary_include_attachment_text(self) -> None:
        context = AttachmentContext(
            filename="report.txt",
            file_type=".txt",
            size=10,
            extracted_text="空腹血糖 7.2 mmol/L",
            can_reference=True,
        )

        prompt = build_attachments_prompt([context])
        summary = build_personal_knowledge_attachment_summary("请记住这份报告", [context])

        self.assertIn("附件 1", prompt)
        self.assertIn("空腹血糖", summary)


if __name__ == "__main__":
    unittest.main()
