"""Модуль отчёта: получение отсортированного списка из API и вывод ведомости."""
from integration_common import request_json


def fetch_sorted(base_url, timeout=3):
    """Запрашивает у API список студентов, отсортированный по среднему баллу."""
    data = request_json("GET", base_url.rstrip("/") + "/students/sorted", timeout=timeout)
    if not isinstance(data, list):
        raise ValueError("Ожидался список студентов")
    return data


def map_api_to_row(item, number):
    """Маппинг JSON-записи API в строку отчёта.

    last_name + first_name + patronymic -> ФИО одной строкой
    gpa (4.5) -> "4.50" (два знака после запятой)
    """
    parts = (item.get("last_name", ""), item.get("first_name", ""), item.get("patronymic", ""))
    return {
        "num": str(number),
        "fio": " ".join(p for p in parts if p),
        "group": str(item.get("group", "")),
        "gpa": f"{float(item.get('gpa', 0)):.2f}",
    }


def format_report(rows):
    """Формирует текстовую таблицу."""
    if not rows:
        return "Список студентов пуст"
    heads = {"num": "№", "fio": "ФИО", "group": "Группа", "gpa": "Средний балл"}
    widths = {k: max(len(heads[k]), *(len(r[k]) for r in rows)) for k in heads}

    def line(r):
        return "  ".join(r[k].ljust(widths[k]) for k in heads).rstrip()

    out = [line(heads), "-" * len(line(heads))]
    out.extend(line(r) for r in rows)
    out.append(f"Всего студентов: {len(rows)}")
    return "\n".join(out)


def build_report(base_url):
    items = fetch_sorted(base_url)
    rows = [map_api_to_row(item, i) for i, item in enumerate(items, start=1)]
    return format_report(rows)
