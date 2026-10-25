"""Модуль обработки: модель студента, проверка данных, сортировка по среднему баллу."""
import math
import threading
from dataclasses import asdict, dataclass

GPA_MIN = 2.0
GPA_MAX = 5.0
MAX_FIELD_LEN = 50


class ValidationError(ValueError):
    """Данные студента не прошли проверку."""


@dataclass
class Student:
    last_name: str
    first_name: str
    patronymic: str
    group: str
    gpa: float

    def to_dict(self):
        return asdict(self)


def _clean_text(data, key, required):
    value = data.get(key, "")
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValidationError(f"Поле {key} должно быть строкой")
    value = value.strip()
    if required and not value:
        raise ValidationError(f"Не указано поле: {key}")
    if len(value) > MAX_FIELD_LEN:
        raise ValidationError(f"Поле {key} длиннее {MAX_FIELD_LEN} символов")
    return value


def validate_student(data):
    """Проверяет словарь с данными и возвращает объект Student."""
    if not isinstance(data, dict):
        raise ValidationError("Ожидается объект с данными студента")
    last_name = _clean_text(data, "last_name", True)
    first_name = _clean_text(data, "first_name", True)
    patronymic = _clean_text(data, "patronymic", False)
    group = _clean_text(data, "group", True)
    gpa = data.get("gpa")
    if gpa is None:
        raise ValidationError("Не указано поле: gpa")
    if isinstance(gpa, bool) or not isinstance(gpa, (int, float)):
        raise ValidationError("Поле gpa должно быть числом")
    gpa = float(gpa)
    if not math.isfinite(gpa) or not GPA_MIN <= gpa <= GPA_MAX:
        raise ValidationError(
            f"Средний балл должен быть в диапазоне {GPA_MIN}–{GPA_MAX}")
    return Student(last_name, first_name, patronymic, group, gpa)


def sort_by_gpa(students):
    """Сортировка по среднему баллу (по убыванию), далее по ФИО."""
    return sorted(students, key=lambda s: (-s.gpa, s.last_name, s.first_name))


class StudentStore:
    """Хранилище студентов в памяти (потокобезопасное)."""

    def __init__(self):
        self._items = []
        self._lock = threading.Lock()

    def add(self, student):
        with self._lock:
            self._items.append(student)
            return len(self._items)

    def all(self):
        with self._lock:
            return list(self._items)

    def clear(self):
        with self._lock:
            count = len(self._items)
            self._items.clear()
            return count
