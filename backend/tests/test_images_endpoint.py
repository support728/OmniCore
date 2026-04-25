import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app


class ImagesEndpointTests(unittest.TestCase):
    @patch("backend.app.routes.image_router.generate_image_result")
    def test_images_endpoint_returns_strict_contract(self, image_mock):
        image_mock.return_value = {
            "type": "images",
            "content": "Generated image",
            "image_url": "https://example.com/generated.png",
            "actions": ["Regenerate", "Make variations"],
            "meta": {
                "prompt": "Create a luxury real estate poster",
                "style": "editorial",
                "aspect_ratio": "4:5",
            },
        }

        with TestClient(app) as client:
            response = client.post(
                "/api/images",
                json={
                    "prompt": "Create a luxury real estate poster",
                    "style": "editorial",
                    "aspect_ratio": "4:5",
                },
            )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["type"], "images")
        self.assertEqual(payload["content"], "Generated image")
        self.assertEqual(payload["image_url"], "https://example.com/generated.png")
        self.assertEqual(payload["actions"], ["Regenerate", "Make variations"])
        self.assertEqual(payload["meta"]["aspect_ratio"], "4:5")

    def test_images_endpoint_requires_prompt(self):
        with TestClient(app) as client:
            response = client.post("/api/images", json={"prompt": ""})

        payload = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertEqual(payload["type"], "error")
        self.assertEqual(payload["content"], "Image prompt is required.")
        self.assertEqual(payload["actions"], ["Retry"])


if __name__ == "__main__":
    unittest.main()
