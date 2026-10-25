"""Интеграционные тесты: ввод -> REST API (обработка) -> отчёт."""
import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import api_server  # noqa: E402
import integration_common as common  # noqa: E402
import student_input as si  # noqa: E402
import student_report as sr  # noqa: E402


class TestReportFormatting(unittest.TestCase):
    def test_map_row(self):
        row = sr.map_api_to_row({"last_name": "Иванов", "first_name": "Иван",
                                 "patronymic": "Иванович", "group": "ИС-21", "gpa": 4.5}, 1)
        self.assertEqual(row, {"num": "1", "fio": "Иванов Иван Иванович",
                               "group": "ИС-21", "gpa": "4.50"})

    def test_map_row_without_patronymic(self):
        row = sr.map_api_to_row({"last_name": "Петров", "first_name": "Пётр",
                                 "patronymic": "", "group": "ИС-21", "gpa": 3}, 2)
        self.assertEqual((row["fio"], row["gpa"]), ("Петров Пётр", "3.00"))

    def test_empty_report(self):
        self.assertEqual(sr.format_report([]), "Список студентов пуст")

    def test_table_has_header_and_total(self):
        rows = [sr.map_api_to_row({"last_name": "А", "first_name": "Б", "patronymic": "",
                                   "group": "В", "gpa": 4}, 1)]
        text = sr.format_report(rows)
        self.assertIn("Средний балл", text)
        self.assertTrue(text.endswith("Всего студентов: 1"))


class TestFullPipeline(unittest.TestCase):
    def setUp(self):
        self.server = api_server.create_server("127.0.0.1", 0, quiet=True)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def add(self, fio, group, gpa):
        return si.send_student(self.url, si.map_form_to_api(
            {"fio": fio, "group": group, "gpa": gpa}))

    def test_report_is_sorted_by_gpa_desc(self):
        self.add("Сидоров Пётр", "ИС-22", "3,6")
        self.add("Петрова Анна Сергеевна", "ИС-21", "4,9")
        self.add("Иванов Иван Иванович", "ИС-21", "4,2")
        lines = sr.build_report(self.url).splitlines()
        body = lines[2:-1]
        self.assertEqual([l.split()[1] for l in body], ["Петрова", "Иванов", "Сидоров"])
        self.assertEqual(lines[-1], "Всего студентов: 3")

    def test_equal_gpa_sorted_by_surname(self):
        self.add("Яковлев Яков", "ИС-21", "4")
        self.add("Абрамов Артём", "ИС-21", "4")
        body = sr.build_report(self.url).splitlines()[2:-1]
        self.assertEqual([l.split()[1] for l in body], ["Абрамов", "Яковлев"])

    def test_comma_and_dot_decimal_give_same_value(self):
        self.add("Иванов Иван", "ИС-21", "4,5")
        self.add("Петров Пётр", "ИС-21", "4.5")
        self.assertEqual([s["gpa"] for s in sr.fetch_sorted(self.url)], [4.5, 4.5])

    def test_boundary_gpa_accepted(self):
        self.add("Иванов Иван", "ИС-21", "2")
        self.add("Петров Пётр", "ИС-21", "5")
        self.assertEqual([s["gpa"] for s in sr.fetch_sorted(self.url)], [5.0, 2.0])

    def test_invalid_gpa_rejected_and_not_stored(self):
        with self.assertRaises(common.IntegrationError):
            self.add("Иванов Иван", "ИС-21", "5,5")
        self.assertEqual(sr.build_report(self.url), "Список студентов пуст")

    def test_empty_system_report(self):
        self.assertEqual(sr.build_report(self.url), "Список студентов пуст")

    def test_unicode_survives_round_trip(self):
        self.add("Ёлкина Юлия Ъ", "ИС-21", "4")
        self.assertIn("Ёлкина Юлия Ъ", sr.build_report(self.url))


class TestFailures(unittest.TestCase):
    def test_report_when_service_down(self):
        with self.assertRaises(common.IntegrationError) as ctx:
            sr.fetch_sorted("http://127.0.0.1:9", timeout=1)
        self.assertIn("недоступен", str(ctx.exception))

    def test_unknown_resource_gives_error(self):
        server = api_server.create_server("127.0.0.1", 0, quiet=True)
        thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/nothing"
            with self.assertRaises(common.IntegrationError):
                common.request_json("GET", url)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
