"""Общий транспортный слой для клиентских модулей: HTTP + JSON."""
import json
import urllib.error
import urllib.request


class IntegrationError(RuntimeError):
    """Ошибка взаимодействия модулей (сервис недоступен, отказ, неверный ответ)."""


def request_json(method, url, payload=None, timeout=3):
    """Выполняет HTTP-запрос и возвращает разобранный JSON-ответ."""
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            message = json.loads(exc.read().decode("utf-8")).get("error", f"HTTP {exc.code}")
        except (ValueError, AttributeError):
            message = f"HTTP {exc.code}"
        raise IntegrationError(f"Сервис отклонил запрос: {message}") from exc
    except (urllib.error.URLError, OSError) as exc:
        raise IntegrationError("Сервис обработки недоступен") from exc
    except ValueError as exc:
        raise IntegrationError("Сервис вернул некорректный ответ") from exc
