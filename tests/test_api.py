import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import api


class FakeAgent:
    provider = "modelscope"
    provider_config = {"model": "test-model"}

    def __init__(self) -> None:
        self.medical_knowledge_enabled = True
        self.personal_knowledge_enabled = False

    def set_knowledge_enabled(self, medical_enabled: bool, personal_enabled: bool) -> None:
        self.medical_knowledge_enabled = medical_enabled
        self.personal_knowledge_enabled = personal_enabled

    def summarize_image_attachment(self, data_url: str, question: str, filename: str) -> str:
        return "视觉摘要"

    def chat(self, message: str, attachments=None) -> str:
        return f"回答：{message}\n\n附件解析：\n- ok"

    def _assess_medical_risk(self, message: str, attachments=None) -> dict:
        return {"level": "normal", "flags": []}


class ApiTests(unittest.TestCase):
    def test_health_returns_defaults(self) -> None:
        client = TestClient(api.app)

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["default_provider"], "modelscope")

    def test_chat_accepts_multipart_file(self) -> None:
        client = TestClient(api.app)

        with patch("api._get_agent", return_value=FakeAgent()):
            response = client.post(
                "/chat",
                data={
                    "message": "根据附件回答",
                    "medical_knowledge_enabled": "true",
                    "personal_knowledge_enabled": "false",
                    "provider": "modelscope",
                    "api_key": "test-key",
                    "embedding_provider": "none",
                },
                files={"files": ("note.txt", b"hello", "text/plain")},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("回答", payload["answer"])
        self.assertEqual(payload["provider"], "modelscope")
        self.assertEqual(payload["attachment_reports"][0]["filename"], "note.txt")


if __name__ == "__main__":
    unittest.main()
