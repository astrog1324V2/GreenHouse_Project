from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


UPLOADER_PATH = Path(__file__).resolve().parents[1] / "esp32" / "lib" / "uploader.py"


class UploaderTestCase(unittest.TestCase):
    def _load_uploader(self, calls: list[dict[str, object]]):
        fake_http_client = types.ModuleType("http_client")

        def post_json(url, payload, timeout_s=10, headers=None):
            calls.append(
                {
                    "url": url,
                    "payload": payload,
                    "timeout_s": timeout_s,
                    "headers": headers,
                }
            )
            return 201, 123, "created"

        fake_http_client.post_json = post_json

        module_name = "test_uploader_%s" % len(self._cleanups)
        spec = importlib.util.spec_from_file_location(module_name, UPLOADER_PATH)
        module = importlib.util.module_from_spec(spec)
        originals = {
            "http_client": sys.modules.get("http_client"),
            module_name: sys.modules.get(module_name),
        }
        sys.modules["http_client"] = fake_http_client
        sys.modules[module_name] = module

        def cleanup():
            for name, original in originals.items():
                if original is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = original

        self.addCleanup(cleanup)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module

    def test_send_omits_auth_header_without_upload_token(self) -> None:
        calls: list[dict[str, object]] = []
        module = self._load_uploader(calls)

        success, status_code, latency_ms, response_text = module.Uploader(
            "http://192.168.1.50:8000/api/v1/readings",
            timeout_s=7,
        ).send({"sequence": 1})

        self.assertTrue(success)
        self.assertEqual(status_code, 201)
        self.assertEqual(latency_ms, 123)
        self.assertEqual(response_text, "created")
        self.assertEqual(calls[0]["headers"], None)

    def test_send_adds_bearer_header_with_upload_token(self) -> None:
        calls: list[dict[str, object]] = []
        module = self._load_uploader(calls)

        module.Uploader(
            "http://192.168.1.50:8000/api/v1/readings",
            timeout_s=7,
            upload_token="ingest-secret",
        ).send({"sequence": 1})

        self.assertEqual(
            calls[0]["headers"],
            {"Authorization": "Bearer ingest-secret"},
        )


if __name__ == "__main__":
    unittest.main()
