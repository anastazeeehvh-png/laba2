"""REST API модуля обработки: приём студентов и выдача списков в формате JSON."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from student_processing import (StudentStore, ValidationError, sort_by_gpa,
                                validate_student)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MAX_BODY = 64 * 1024


class StudentApiHandler(BaseHTTPRequestHandler):
    server_version = "StudentApi/1.0"

    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length <= 0 or length > MAX_BODY:
            self._send_json(400, {"error": "Некорректная длина тела запроса"})
            return None
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(400, {"error": "Тело запроса не является корректным JSON"})
            return None
        return data

    def do_GET(self):
        store = self.server.store
        if self.path == "/students":
            self._send_json(200, [s.to_dict() for s in store.all()])
        elif self.path == "/students/sorted":
            ordered = sort_by_gpa(store.all())
            self._send_json(200, [s.to_dict() for s in ordered])
        else:
            self._send_json(404, {"error": "Ресурс не найден"})

    def do_POST(self):
        if self.path != "/students":
            self._send_json(404, {"error": "Ресурс не найден"})
            return
        data = self._read_json_body()
        if data is None:
            return
        try:
            student = validate_student(data)
        except ValidationError as exc:
            self._send_json(400, {"error": str(exc)})
            return
        new_id = self.server.store.add(student)
        self._send_json(201, {"id": new_id, **student.to_dict()})

    def do_DELETE(self):
        if self.path != "/students":
            self._send_json(404, {"error": "Ресурс не найден"})
            return
        self._send_json(200, {"deleted": self.server.store.clear()})

    def log_message(self, fmt, *args):
        if not getattr(self.server, "quiet", False):
            super().log_message(fmt, *args)


def create_server(host=DEFAULT_HOST, port=DEFAULT_PORT, store=None, quiet=False):
    """Создаёт HTTP-сервер (port=0 — свободный порт, удобно для тестов)."""
    server = ThreadingHTTPServer((host, port), StudentApiHandler)
    server.store = store if store is not None else StudentStore()
    server.quiet = quiet
    return server


def serve(host=DEFAULT_HOST, port=DEFAULT_PORT):
    server = create_server(host, port)
    print(f"REST API запущен: http://{host}:{server.server_address[1]}  (Ctrl+C — остановка)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
    finally:
        server.server_close()
