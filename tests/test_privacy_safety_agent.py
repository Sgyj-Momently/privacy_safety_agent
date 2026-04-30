from fastapi.testclient import TestClient
from unittest import TestCase

from src.api_server import app
from src.privacy_guard import detect_sensitive_signals, screen_bundle


class PrivacySafetyAgentTest(TestCase):
    def test_allows_public_photo(self):
        result = screen_bundle({"photos": [{"file_name": "IMG_0001.jpg", "photo_summary": {"summary": "cake"}}]})

        self.assertEqual(result["privacy_status"], "ok")
        self.assertEqual(result["public_photo_count"], 1)
        self.assertEqual(result["excluded_photo_count"], 0)

    def test_excludes_pre_flagged_photo(self):
        result = screen_bundle(
            {
                "photos": [
                    {
                        "file_name": "IMG_0002.jpg",
                        "photo_summary": {"exclude_from_public_outputs": True},
                    }
                ]
            }
        )

        self.assertEqual(result["public_photo_count"], 0)
        self.assertEqual(result["excluded_photo_count"], 1)
        self.assertIn("pre_flagged_exclusion", result["excluded_photos"][0]["exclusion_reason"])

    def test_detects_sensitive_filename_and_ocr_patterns(self):
        signals = detect_sensitive_signals(
            {
                "file_name": "passport_scan.jpg",
                "photo_summary": {"ocr_text": ["Call me at 010-1234-5678", "a@example.com"]},
            }
        )

        self.assertIn("sensitive_filename", signals)
        self.assertIn("phone", signals)
        self.assertIn("email", signals)

    def test_health_endpoint(self):
        client = TestClient(app)

        response = client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "privacy_safety_agent")

    def test_review_endpoint(self):
        client = TestClient(app)

        response = client.post(
            "/api/v1/privacy-safety",
            json={"project_id": "sample", "photos": [{"file_name": "credit_card.jpg"}]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["project_id"], "sample")
        self.assertEqual(response.json()["excluded_photo_count"], 1)

