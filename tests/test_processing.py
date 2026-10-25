import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import student_processing as sp  # noqa: E402


def ok(**kw):
    data = {"last_name": "Иванов", "first_name": "Иван", "patronymic": "Иванович",
            "group": "ИС-21", "gpa": 4.5}
    data.update(kw)
    return data


class TestValidation(unittest.TestCase):
    def test_valid_student(self):
        s = sp.validate_student(ok())
        self.assertEqual((s.last_name, s.gpa), ("Иванов", 4.5))

    def test_patronymic_optional(self):
        s = sp.validate_student(ok(patronymic=""))
        self.assertEqual(s.patronymic, "")

    def test_boundary_gpa(self):
        self.assertEqual(sp.validate_student(ok(gpa=2)).gpa, 2.0)
        self.assertEqual(sp.validate_student(ok(gpa=5)).gpa, 5.0)

    def test_gpa_out_of_range(self):
        for bad in (1.99, 5.01, -1, 100):
            with self.assertRaises(sp.ValidationError):
                sp.validate_student(ok(gpa=bad))

    def test_gpa_wrong_type(self):
        for bad in ("4.5", True, None, [4]):
            with self.assertRaises(sp.ValidationError):
                sp.validate_student(ok(gpa=bad))

    def test_gpa_not_finite(self):
        with self.assertRaises(sp.ValidationError):
            sp.validate_student(ok(gpa=float("nan")))

    def test_missing_or_empty_required(self):
        for key in ("last_name", "first_name", "group"):
            with self.assertRaises(sp.ValidationError):
                sp.validate_student(ok(**{key: "  "}))
        data = ok()
        del data["group"]
        with self.assertRaises(sp.ValidationError):
            sp.validate_student(data)

    def test_not_a_dict(self):
        with self.assertRaises(sp.ValidationError):
            sp.validate_student([1, 2])

    def test_too_long_field(self):
        with self.assertRaises(sp.ValidationError):
            sp.validate_student(ok(last_name="я" * 51))


class TestSorting(unittest.TestCase):
    def test_sorted_by_gpa_desc(self):
        items = [sp.validate_student(ok(last_name=n, gpa=g))
                 for n, g in (("А", 3.5), ("Б", 4.9), ("В", 4.1))]
        self.assertEqual([s.last_name for s in sp.sort_by_gpa(items)], ["Б", "В", "А"])

    def test_ties_sorted_by_name(self):
        items = [sp.validate_student(ok(last_name=n, gpa=4.0)) for n in ("Яковлев", "Абрамов")]
        self.assertEqual([s.last_name for s in sp.sort_by_gpa(items)], ["Абрамов", "Яковлев"])

    def test_empty_list(self):
        self.assertEqual(sp.sort_by_gpa([]), [])


class TestStore(unittest.TestCase):
    def test_add_all_clear(self):
        store = sp.StudentStore()
        self.assertEqual(store.add(sp.validate_student(ok())), 1)
        self.assertEqual(len(store.all()), 1)
        self.assertEqual(store.clear(), 1)
        self.assertEqual(store.all(), [])


if __name__ == "__main__":
    unittest.main()
