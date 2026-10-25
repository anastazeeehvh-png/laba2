"""Система учёта студентов: единая точка входа интегрированной системы.

Команды:
  python src/main.py serve [--port 8000]   запустить REST API (модуль обработки)
  python src/main.py add [--url URL]       ввести студента (модуль ввода)
  python src/main.py report [--url URL]    вывести ведомость (модуль отчёта)
  python src/main.py demo                  полный сценарий в одном процессе
"""
import argparse
import sys
import threading

import api_server
import student_input
import student_report
from integration_common import IntegrationError

DEFAULT_URL = f"http://{api_server.DEFAULT_HOST}:{api_server.DEFAULT_PORT}"

DEMO_STUDENTS = (
    {"fio": "Иванов Иван Иванович", "group": "ИС-21", "gpa": "4,2"},
    {"fio": "Петрова Анна Сергеевна", "group": "ИС-21", "gpa": "4,9"},
    {"fio": "Сидоров Пётр", "group": "ИС-22", "gpa": "3,6"},
    {"fio": "Кузнецова Мария Олеговна", "group": "ИС-22", "gpa": "4,9"},
)


def run_demo():
    server = api_server.create_server(api_server.DEFAULT_HOST, 0, quiet=True)
    url = f"http://{api_server.DEFAULT_HOST}:{server.server_address[1]}"
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    try:
        print(f"[1/3] Модуль обработки запущен: {url}")
        print("[2/3] Модуль ввода отправляет студентов в API:")
        for form in DEMO_STUDENTS:
            answer = student_input.send_student(url, student_input.map_form_to_api(form))
            print(f"      id={answer['id']}: {form['fio']} (средний балл {form['gpa']})")
        print("[3/3] Модуль отчёта запрашивает отсортированный список:\n")
        print(student_report.build_report(url))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Система учёта студентов")
    sub = parser.add_subparsers(dest="command", required=True)
    p_serve = sub.add_parser("serve", help="запустить REST API")
    p_serve.add_argument("--port", type=int, default=api_server.DEFAULT_PORT)
    for name in ("add", "report"):
        sub.add_parser(name).add_argument("--url", default=DEFAULT_URL)
    sub.add_parser("demo", help="полный сценарий без отдельного сервера")
    args = parser.parse_args(argv)
    try:
        if args.command == "serve":
            api_server.serve(api_server.DEFAULT_HOST, args.port)
        elif args.command == "add":
            answer = student_input.add_student_interactive(args.url)
            print(f"Студент добавлен (id={answer['id']})")
        elif args.command == "report":
            print(student_report.build_report(args.url))
        else:
            run_demo()
    except student_input.InputError as exc:
        print(f"Ошибка ввода: {exc}")
        return 2
    except IntegrationError as exc:
        print(f"Ошибка интеграции: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
