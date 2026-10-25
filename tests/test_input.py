import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import api_server  # noqa: E402
import integration_common as common  # noqa: E402
import student_input as si  # noqa: E402


class TestMapping(unittest.TestCase):
    def test_full_form(self):
        p = si.map_form_to_api({"fio": "Иванов Иван Иванович", "group": "ИС-21", "gpa": "4,5"})
        self.assertEqual(p, {"last_name": "Иванов", "first_name": "Иван",
                             "patronymic": "Иванович", "group": "ИС-21", "gpa": 4.5})

    def test_without_patronymic(self):
        p = si.map_form_to_api({"fio": "Петров Пётр", "group": "ИС-21", "gpa": "3"})
        self.assertEqual((p["patronymic"], p["gpa"]), ("", 3.0))

    def test_extra_spaces(self):
        p = si.map_form_to_api({"fio": "  Сидоров   Сидор  ", "group": " ИС-21 ", "gpa": " 4.0 "})
        self.assertEqual((p["last_name"], p["group"]), ("Сидоров", "ИС-21"))

    def test_bad_input(self):
        for form in ({"fio": "Иванов", "group": "ИС-21", "gpa": "4"},
                     {"fio": "Иванов Иван", "group": "", "gpa": "4"},
                     {"fio": "Иванов Иван", "group": "ИС-21", "gpa": "отлично"}):
            with self.assertRaises(si.InputError):
                si.map_form_to_api(form)


class TestSendToApi(unittest.TestCase):
    def setUp(self):
        self.server = api_server.create_server("127.0.0.1", 0, quiet=True)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def test_send_ok_and_stored(self):
        form = {"fio": "Иванов Иван Иванович", "group": "ИС-21", "gpa": "4,5"}
        resp = si.send_student(self.url, si.map_form_to_api(form))
        self.assertEqual(resp["id"], 1)
        self.assertEqual(len(self.server.store.all()), 1)

    def test_interactive_flow(self):
        answers = iter(["Петров Пётр", "ИС-22", "3,8"])
        resp = si.add_student_interactive(self.url, input_fn=lambda _: next(answers))
        self.assertEqual((resp["last_name"], resp["gpa"]), ("Петров", 3.8))

    def test_server_rejects_out_of_range(self):
        payload = si.map_form_to_api({"fio": "Иванов Иван", "group": "ИС-21", "gpa": "6"})
        with self.assertRaises(common.IntegrationError) as ctx:
            si.send_student(self.url, payload)
        self.assertIn("диапазоне", str(ctx.exception))
        self.assertEqual(self.server.store.all(), [])


class TestServiceUnavailable(unittest.TestCase):
    def test_no_server(self):
        payload = {"last_name": "А", "first_name": "Б", "patronymic": "", "group": "В", "gpa": 4.0}
        with self.assertRaises(common.IntegrationError) as ctx:
            si.send_student("http://127.0.0.1:9", payload, timeout=1)
        self.assertIn("недоступен", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
