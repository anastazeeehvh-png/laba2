"""Система учёта студентов — точка входа."""

students = []


def add_student(name, group):
    students.append({"name": name, "group": group})


def find_by_group(group):
    return [s for s in students if s["group"] == group]


def main():
    add_student("Иванов Иван", "ИС-21")
    print("Студентов в базе:", len(students))


if __name__ == "__main__":
    main()
