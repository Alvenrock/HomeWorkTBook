"""
Полный набор тестов для модуля model.py.

Запуск:
    pytest test_directory.py -v

Покрытие:
    - Contact: создание, сериализация, равенство
    - PhoneBook: add / remove / edit / find_index / is_full
    - PhoneBook: поиск (имя, телефон, комментарий, общий запрос)
    - PhoneBook: сортировка (прямая / обратная, разные столбцы)
    - FileReader: чтение, все ошибочные сценарии
    - FileWriter: запись, create_empty, roundtrip, ошибки записи
    - Валидация телефона: is_valid_phone / normalize_phone / extract_digits
    - Кастомные исключения: иерархия, ловля, сообщения
    - Интеграционные сценарии
"""
import json

import pytest

from model import (
    Contact,
    PhoneBook,
    FileReader,
    FileWriter,
    is_valid_phone,
    normalize_phone,
    extract_digits,
    PhoneBookError,
    ContactLimitError,
    ContactNotFoundError,
    FileReadError,
    FileWriteError,
)


# =====================================================================
# Contact
# =====================================================================

class TestContact:
    def test_create_empty(self):
        c = Contact()
        assert c.name == ""
        assert c.phone == ""
        assert c.comment == ""

    def test_create_with_data(self):
        c = Contact("Иван", "+7 900 123-45-67", "друг")
        assert c.name == "Иван"
        assert c.phone == "+7 900 123-45-67"
        assert c.comment == "друг"

    def test_to_dict(self):
        c = Contact("Иван", "+7 900 123-45-67", "друг")
        assert c.to_dict() == {
            "name": "Иван",
            "phone": "+7 900 123-45-67",
            "comment": "друг",
        }

    @pytest.mark.parametrize("data, expected", [
        ({"name": "A", "phone": "P", "comment": "C"}, ("A", "P", "C")),
        ({"name": "A"}, ("A", "", "")),
        ({"phone": "P"}, ("", "P", "")),
        ({"comment": "C"}, ("", "", "C")),
        ({}, ("", "", "")),
    ])
    def test_from_dict(self, data, expected):
        c = Contact.from_dict(data)
        assert (c.name, c.phone, c.comment) == expected

    def test_equality(self):
        assert Contact("A", "P", "C") == Contact("A", "P", "C")

    def test_inequality(self):
        assert Contact("A", "P", "C") != Contact("B", "P", "C")

    def test_not_equal_to_other_type(self):
        assert Contact("A", "P", "C") != "not a contact"

    def test_repr(self):
        c = Contact("Иван", "+7 900 123-45-67", "друг")
        r = repr(c)
        assert "Contact" in r
        assert "Иван" in r


# =====================================================================
# PhoneBook — базовые операции
# =====================================================================

class TestPhoneBook:
    def setup_method(self):
        self.book = PhoneBook()

    def test_initial_state(self):
        assert self.book.contacts == []
        assert self.book.current_file is None
        assert self.book.dirty is False
        assert self.book.is_full() is False

    # ---------- add ----------
    def test_add_contact(self):
        c = Contact("Иван", "+7 900 123-45-67", "друг")
        self.book.add_contact(c)
        assert len(self.book.contacts) == 1
        assert self.book.contacts[0] is c
        assert self.book.dirty is True

    def test_add_empty_contact_allowed(self):
        """Граничный случай: пустой контакт модель принимает
        (валидация — на уровне view)."""
        self.book.add_contact(Contact())
        assert len(self.book.contacts) == 1

    @pytest.mark.parametrize("name", [
        "Иван",
        "John",
        "Иван-Петр",
        "О'Брайен",
        "Иван Петрович",
        "IVAN",
    ])
    def test_add_various_names(self, name):
        self.book.add_contact(Contact(name, "+7 900 123-45-67", ""))
        assert self.book.contacts[-1].name == name

    def test_add_limit(self):
        for i in range(PhoneBook.MAX_CONTACTS):
            self.book.add_contact(Contact(f"Имя{i}", "+7 900 000-00-00"))
        assert self.book.is_full() is True
        with pytest.raises(ContactLimitError):
            self.book.add_contact(Contact("Overflow"))

    # ---------- remove ----------
    def test_remove_contact(self):
        c = Contact("Иван", "+7 900 123-45-67", "друг")
        self.book.add_contact(c)
        self.book.dirty = False
        removed = self.book.remove_contact(0)
        assert removed is c
        assert self.book.contacts == []
        assert self.book.dirty is True

    @pytest.mark.parametrize("index", [-1, 5, 100, -10])
    def test_remove_wrong_index(self, index):
        self.book.add_contact(Contact("A"))
        with pytest.raises(ContactNotFoundError):
            self.book.remove_contact(index)

    def test_remove_none_index(self):
        with pytest.raises(ContactNotFoundError):
            self.book.remove_contact(None)

    # ---------- edit ----------
    def test_edit_contact(self):
        self.book.add_contact(Contact("Иван", "+7 900 123-45-67", "друг"))
        self.book.dirty = False
        new = Contact("Петр", "+7 900 765-43-21", "коллега")
        self.book.edit_contact(0, new)
        assert self.book.contacts[0] is new
        assert self.book.dirty is True

    @pytest.mark.parametrize("index", [-1, 5, 100])
    def test_edit_wrong_index(self, index):
        with pytest.raises(ContactNotFoundError):
            self.book.edit_contact(index, Contact("A"))

    # ---------- find_index ----------
    def test_find_index(self):
        self.book.add_contact(Contact("Иван", "+7 900 123-45-67", "друг"))
        self.book.add_contact(Contact("Петр", "+7 900 765-43-21", "коллега"))
        assert self.book.find_index("Иван", "+7 900 123-45-67", "друг") == 0
        assert self.book.find_index("Петр", "+7 900 765-43-21", "коллега") == 1

    def test_find_index_not_found(self):
        self.book.add_contact(Contact("Иван", "+7 900 123-45-67", "друг"))
        assert self.book.find_index("Нет", "нет", "нет") is None

    # ---------- is_full ----------
    def test_is_full(self):
        assert self.book.is_full() is False
        for i in range(PhoneBook.MAX_CONTACTS):
            self.book.add_contact(Contact(f"C{i}"))
        assert self.book.is_full() is True


# =====================================================================
# PhoneBook — поиск
# =====================================================================

class TestPhoneBookSearch:
    def setup_method(self):
        self.book = PhoneBook()
        self.book.add_contact(Contact("Иван Иванов", "+7 900 123-45-67", "друг"))
        self.book.add_contact(Contact("Петр Петров", "+7 900 765-43-21", "коллега"))
        self.book.add_contact(Contact("Юрий Юрьев", "+7 900 111-22-33", "сосед"))

    def test_search_by_name(self):
        result = self.book.search_contacts("Иван")
        assert len(result) == 1
        assert result[0].name == "Иван Иванов"

    def test_search_by_phone(self):
        result = self.book.search_contacts("765")
        assert len(result) == 1
        assert result[0].name == "Петр Петров"

    def test_search_by_comment(self):
        result = self.book.search_contacts("сосед")
        assert len(result) == 1
        assert result[0].name == "Юрий Юрьев"

    @pytest.mark.parametrize("query", ["иван", "ИВАН", "Иван", "иВаН"])
    def test_search_case_insensitive(self, query):
        assert len(self.book.search_contacts(query)) == 1

    def test_search_general_query(self):
        result = self.book.search_contacts("петр")
        assert len(result) == 1
        assert result[0].name == "Петр Петров"

    def test_search_empty_query(self):
        result = self.book.search_contacts("")
        assert len(result) == 3
        # должна возвращаться копия
        assert result is not self.book.contacts

    def test_search_nonexistent(self):
        result = self.book.search_contacts("несуществующий")
        assert result == []

    def test_search_matches_multiple(self):
        """Поиск по «7» найдёт всех — у всех телефонов есть цифра 7."""
        result = self.book.search_contacts("7")
        assert len(result) == 3


# =====================================================================
# PhoneBook — сортировка
# =====================================================================

class TestPhoneBookSort:
    def setup_method(self):
        self.book = PhoneBook()
        self.book.add_contact(Contact("Борис", "+7 900 333-33-33", "b"))
        self.book.add_contact(Contact("Анна", "+7 900 111-11-11", "a"))
        self.book.add_contact(Contact("Виктор", "+7 900 222-22-22", "c"))

    def test_sort_by_name(self):
        result = PhoneBook.sort_contacts(self.book.contacts, "name")
        assert [c.name for c in result] == ["Анна", "Борис", "Виктор"]

    def test_sort_by_name_reverse(self):
        result = PhoneBook.sort_contacts(self.book.contacts, "name", reverse=True)
        assert [c.name for c in result] == ["Виктор", "Борис", "Анна"]

    def test_sort_by_phone(self):
        result = PhoneBook.sort_contacts(self.book.contacts, "phone")
        assert [c.name for c in result] == ["Анна", "Виктор", "Борис"]

    def test_sort_by_comment(self):
        result = PhoneBook.sort_contacts(self.book.contacts, "comment")
        assert [c.comment for c in result] == ["a", "b", "c"]

    def test_sort_empty(self):
        assert PhoneBook.sort_contacts([], "name") == []

    def test_sort_case_insensitive(self):
        book = PhoneBook()
        book.add_contact(Contact("banana"))
        book.add_contact(Contact("Apple"))
        book.add_contact(Contact("cherry"))
        result = PhoneBook.sort_contacts(book.contacts, "name")
        assert [c.name for c in result] == ["Apple", "banana", "cherry"]

    def test_sort_single(self):
        book = PhoneBook()
        book.add_contact(Contact("Only"))
        assert len(PhoneBook.sort_contacts(book.contacts, "name")) == 1


# =====================================================================
# FileReader
# =====================================================================

class TestFileReader:
    def test_read_valid_file(self, tmp_path):
        path = tmp_path / "book.json"
        path.write_text(json.dumps({
            "contacts": [
                {"name": "Иван", "phone": "+7 900 123-45-67", "comment": "друг"},
                {"name": "Петр", "phone": "+7 900 765-43-21", "comment": ""},
            ]
        }, ensure_ascii=False), encoding="utf-8")
        contacts = FileReader.read(str(path))
        assert len(contacts) == 2
        assert contacts[0].name == "Иван"
        assert contacts[1].phone == "+7 900 765-43-21"

    def test_read_missing_file(self, tmp_path):
        with pytest.raises(FileReadError):
            FileReader.read(str(tmp_path / "nonexistent.json"))

    def test_read_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        with pytest.raises(FileReadError):
            FileReader.read(str(path))

    def test_read_non_dict_root(self, tmp_path):
        path = tmp_path / "list.json"
        path.write_text("[1, 2, 3]", encoding="utf-8")
        with pytest.raises(FileReadError):
            FileReader.read(str(path))

    def test_read_contacts_not_list(self, tmp_path):
        path = tmp_path / "bad2.json"
        path.write_text(json.dumps({"contacts": "oops"}), encoding="utf-8")
        with pytest.raises(FileReadError):
            FileReader.read(str(path))

    def test_read_contacts_none(self, tmp_path):
        path = tmp_path / "none.json"
        path.write_text(json.dumps({"contacts": None}), encoding="utf-8")
        with pytest.raises(FileReadError):
            FileReader.read(str(path))

    def test_read_contact_not_dict(self, tmp_path):
        path = tmp_path / "bad3.json"
        path.write_text(json.dumps({"contacts": [1, 2]}), encoding="utf-8")
        with pytest.raises(FileReadError):
            FileReader.read(str(path))

    def test_read_empty_contacts(self, tmp_path):
        path = tmp_path / "empty.json"
        path.write_text(json.dumps({"contacts": []}), encoding="utf-8")
        assert FileReader.read(str(path)) == []

    def test_read_missing_contacts_key(self, tmp_path):
        path = tmp_path / "nokey.json"
        path.write_text(json.dumps({"other": 1}), encoding="utf-8")
        assert FileReader.read(str(path)) == []


# =====================================================================
# FileWriter
# =====================================================================

class TestFileWriter:
    def test_write_and_read_roundtrip(self, tmp_path):
        path = tmp_path / "out.json"
        contacts = [
            Contact("Иван", "+7 900 123-45-67", "друг"),
            Contact("Петр", "+7 900 765-43-21", "коллега"),
        ]
        FileWriter.write(str(path), contacts)
        loaded = FileReader.read(str(path))
        assert len(loaded) == 2
        assert loaded[0].name == "Иван"
        assert loaded[1].comment == "коллега"

    def test_write_empty(self, tmp_path):
        path = tmp_path / "empty.json"
        FileWriter.write(str(path), [])
        assert FileReader.read(str(path)) == []

    def test_write_preserves_unicode(self, tmp_path):
        path = tmp_path / "u.json"
        FileWriter.write(str(path), [Contact("Юрий", "+7 900 111-22-33", "сосед")])
        text = path.read_text(encoding="utf-8")
        assert "Юрий" in text  # не escape-последовательности

    def test_write_invalid_path(self, tmp_path):
        invalid = tmp_path / "no_such_dir" / "file.json"
        with pytest.raises(FileWriteError):
            FileWriter.write(str(invalid), [])

    def test_create_empty(self, tmp_path):
        path = tmp_path / "new.json"
        FileWriter.create_empty(str(path))
        assert path.exists()
        assert FileReader.read(str(path)) == []

    def test_create_empty_invalid_path(self, tmp_path):
        invalid = tmp_path / "no_such_dir" / "file.json"
        with pytest.raises(FileWriteError):
            FileWriter.create_empty(str(invalid))


# =====================================================================
# Валидация телефона (параметризованные тесты)
# =====================================================================

class TestPhoneValidation:
    @pytest.mark.parametrize("phone", [
        "+7 900 123-45-67",
        "+7 000 000-00-00",
        "+7 999 999-99-99",
        "+7 123 456-78-90",
    ])
    def test_valid_phones(self, phone):
        assert is_valid_phone(phone) is True

    @pytest.mark.parametrize("phone", [
        "",
        "   ",
        "+7 900 123-45-6",
        "+7 900 123-45-678",
        "8 900 123-45-67",
        "+79001234567",
        "+7 (900) 123-45-67",
        "+7 900 1234567",
        "abc",
        "+8 900 123-45-67",
        "+7 900 123 45 67",
    ])
    def test_invalid_phones(self, phone):
        assert is_valid_phone(phone) is False

    @pytest.mark.parametrize("raw, expected", [
        ("+7 900 123-45-67", "+7 900 123-45-67"),
        ("89001234567",      "+7 900 123-45-67"),
        ("79001234567",      "+7 900 123-45-67"),
        ("9001234567",       "+7 900 123-45-67"),
        ("+7 (900) 123 45 67", "+7 900 123-45-67"),
        ("",                 ""),
        ("123",              ""),
        ("12345678901234",   ""),
    ])
    def test_normalize_phone(self, raw, expected):
        assert normalize_phone(raw) == expected

    @pytest.mark.parametrize("raw, expected", [
        ("+7 900 123-45-67", "9001234567"),
        ("89001234567",      "9001234567"),
        ("79001234567",      "9001234567"),
        ("9001234567",       "9001234567"),
        ("",                 ""),
        ("123",              "123"),
        ("12345678901234",   "1234567890"),
    ])
    def test_extract_digits(self, raw, expected):
        assert extract_digits(raw) == expected


# =====================================================================
# Кастомные исключения
# =====================================================================

class TestExceptions:
    @pytest.mark.parametrize("exc", [
        FileReadError,
        FileWriteError,
        ContactLimitError,
        ContactNotFoundError,
    ])
    def test_inherit_from_base(self, exc):
        assert issubclass(exc, PhoneBookError)

    @pytest.mark.parametrize("exc", [
        FileReadError,
        FileWriteError,
        ContactLimitError,
        ContactNotFoundError,
    ])
    def test_catch_as_base(self, exc):
        with pytest.raises(PhoneBookError):
            raise exc("test")

    def test_limit_error_message(self):
        with pytest.raises(ContactLimitError, match="лимит"):
            raise ContactLimitError("Достигнут лимит")

    def test_file_read_error_wraps_original(self, tmp_path):
        """FileReadError должен содержать внятное сообщение."""
        with pytest.raises(FileReadError, match="не найден"):
            FileReader.read(str(tmp_path / "absent.json"))

    def test_file_write_error_message(self, tmp_path):
        invalid = tmp_path / "no_dir" / "f.json"
        with pytest.raises(FileWriteError, match="Ошибка"):
            FileWriter.write(str(invalid), [])


# =====================================================================
# Интеграционные сценарии
# =====================================================================

class TestIntegration:
    def test_full_workflow(self, tmp_path):
        path = tmp_path / "book.json"
        book = PhoneBook()

        # Добавление
        book.add_contact(Contact("Иван", "+7 900 123-45-67", "друг"))
        book.add_contact(Contact("Петр", "+7 900 765-43-21", "коллега"))
        assert len(book.contacts) == 2

        # Поиск
        assert len(book.search_contacts("Иван")) == 1

        # Редактирование
        book.edit_contact(0, Contact("Иван П.", "+7 900 123-45-67", "друг"))
        assert book.contacts[0].name == "Иван П."

        # Сохранение
        FileWriter.write(str(path), book.contacts)
        assert path.exists()

        # Загрузка в новый справочник
        book2 = PhoneBook()
        book2.contacts = FileReader.read(str(path))
        assert len(book2.contacts) == 2
        assert book2.contacts[0].name == "Иван П."

        # Удаление
        book2.remove_contact(0)
        assert len(book2.contacts) == 1

    def test_limit_boundary_full_cycle(self):
        """Граничный сценарий: достижение и снятие лимита."""
        book = PhoneBook()
        for i in range(PhoneBook.MAX_CONTACTS):
            book.add_contact(Contact(f"C{i}"))
        assert book.is_full()
        with pytest.raises(ContactLimitError):
            book.add_contact(Contact("overflow"))
        book.remove_contact(0)
        assert not book.is_full()
        book.add_contact(Contact("new"))  # снова можно
        assert book.is_full()