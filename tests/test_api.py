"""Тесты REST API. Тест играет роль драйвера: заменяет модули ввода и отчёта."""
import http.client
import json
import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import api_server  # noqa: E402


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.server = api_server.create_server("127.0.0.1", 0, quiet=True)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def call(self, method, path, body=None, raw=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        headers = {}
        if raw is None and body is not None:
            raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        if raw is not None:
            headers["Content-Type"] = "application/json; charset=utf-8"
        conn.request(method, path, body=raw, headers=headers)
        resp = conn.getresponse()
        data = json.loads(resp.read().decode("utf-8"))
        conn.close()
        return resp.status, data

    @staticmethod
    def student(name, gpa):
        return {"last_name": name, "first_name": "Иван", "patronymic": "",
                "group": "ИС-21", "gpa": gpa}


class TestApi(ApiTestCase):
    def test_post_valid_returns_201(self):
        status, data = self.call("POST", "/students", self.student("Иванов", 4.5))
        self.assertEqual(status, 201)
        self.assertEqual((data["id"], data["last_name"]), (1, "Иванов"))

    def test_post_invalid_gpa_returns_400(self):
        status, data = self.call("POST", "/students", self.student("Иванов", 7))
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_post_broken_json_returns_400(self):
        status, data = self.call("POST", "/students", raw="{не json".encode("utf-8"))
        self.assertEqual(status, 400)

    def test_post_json_array_returns_400(self):
        status, _ = self.call("POST", "/students", body=[1, 2, 3])
        self.assertEqual(status, 400)

    def test_post_empty_body_returns_400(self):
        status, _ = self.call("POST", "/students", raw=b"")
        self.assertEqual(status, 400)

    def test_get_sorted_order(self):
        for name, gpa in (("А", 3.5), ("Б", 4.9), ("В", 4.1)):
            self.call("POST", "/students", self.student(name, gpa))
        status, data = self.call("GET", "/students/sorted")
        self.assertEqual(status, 200)
        self.assertEqual([s["last_name"] for s in data], ["Б", "В", "А"])

    def test_get_unsorted_keeps_input_order(self):
        for name, gpa in (("А", 3.5), ("Б", 4.9)):
            self.call("POST", "/students", self.student(name, gpa))
        _, data = self.call("GET", "/students")
        self.assertEqual([s["last_name"] for s in data], ["А", "Б"])

    def test_empty_list(self):
        self.assertEqual(self.call("GET", "/students/sorted"), (200, []))

    def test_unknown_path_returns_404(self):
        self.assertEqual(self.call("GET", "/unknown")[0], 404)
        self.assertEqual(self.call("POST", "/unknown", body={})[0], 404)

    def test_delete_clears_store(self):
        self.call("POST", "/students", self.student("А", 4))
        self.assertEqual(self.call("DELETE", "/students"), (200, {"deleted": 1}))
        self.assertEqual(self.call("GET", "/students"), (200, []))


if __name__ == "__main__":
    unittest.main()
