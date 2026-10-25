"""Модуль ввода: ввод данных о студенте и отправка в REST API модуля обработки."""
from integration_common import request_json


class InputError(ValueError):
    """Некорректный ввод пользователя."""


def map_form_to_api(form):
    """Маппинг данных формы ввода в JSON-структуру API.

    fio ("Иванов Иван Иванович") -> last_name, first_name, patronymic
    gpa ("4,5") -> gpa (4.5, запятая заменяется точкой)
    """
    parts = str(form.get("fio", "")).split()
    if len(parts) < 2:
        raise InputError("Введите минимум фамилию и имя")
    group = str(form.get("group", "")).strip()
    if not group:
        raise InputError("Введите номер группы")
    raw_gpa = str(form.get("gpa", "")).strip().replace(",", ".")
    try:
        gpa = float(raw_gpa)
    except ValueError:
        raise InputError("Средний балл должен быть числом") from None
    return {
        "last_name": parts[0],
        "first_name": parts[1],
        "patronymic": " ".join(parts[2:]),
        "group": group,
        "gpa": gpa,
    }


def send_student(base_url, payload, timeout=3):
    """Отправляет студента в API (POST /students), возвращает ответ сервиса."""
    return request_json("POST", base_url.rstrip("/") + "/students", payload, timeout)


def read_form(input_fn=input):
    """Читает данные студента из консоли."""
    return {
        "fio": input_fn("ФИО (Иванов Иван Иванович): "),
        "group": input_fn("Группа: "),
        "gpa": input_fn("Средний балл (2.0–5.0): "),
    }


def add_student_interactive(base_url, input_fn=input):
    """Ввод → маппинг → отправка. Возвращает ответ API."""
    payload = map_form_to_api(read_form(input_fn))
    return send_student(base_url, payload)
