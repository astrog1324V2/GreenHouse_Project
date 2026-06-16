try:
    import ujson as json
except ImportError:
    import json

from http_client import post_json


class Uploader:
    def __init__(self, server_url, timeout_s=10, upload_token=None):
        self.server_url = server_url
        self.timeout_s = timeout_s
        self.upload_token = upload_token

    def send(self, payload):
        headers = None
        if self.upload_token:
            headers = {"Authorization": "Bearer %s" % self.upload_token}
        status_code, latency_ms, response_text = post_json(
            self.server_url, payload, timeout_s=self.timeout_s, headers=headers
        )
        success = 200 <= status_code < 300
        return success, status_code, latency_ms, response_text
