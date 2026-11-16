"""Модель телефонного справочника: данные, файловый ввод-вывод, валидация."""
import json
import re


# ==================== Кастомные исключения ====================

class PhoneBookError(Exception):
    """Базовое исключение для ошибок справочника."""


class FileReadError(PhoneBookError):
    """Ошибка при чтении файла справочника."""


class FileWriteError(PhoneBookError):
    """Ошибка при записи файла справочника."""


class ContactLimitError(PhoneBookError):
    """Превышен лимит записей в справочнике."""


class ContactNotFoundError(PhoneBookError):
    """Запрашиваемый контакт не найден."""


class InvalidPhoneError(PhoneBookError):
    """Неверный формат телефонного номера."""


# ==================== Валидация телефона ====================

PHONE_PATTERN = re.compile(r"^\+7 \d{3} \d{3}-\d{2}-\d{2}$")
DIGITS_PATTERN = re.compile(r"\D")


def is_valid_phone(phone: str) -> bool:
    """Строгая проверка: соответствует ли строка маске +7 XXX XXX-XX-XX."""
    return bool(PHONE_PATTERN.match(phone.strip()))


def normalize_phone(phone: str) -> str:
    """Приводит произвольный ввод к виду +7 XXX XXX-XX-XX."""
    digits = DIGITS_PATTERN.sub("", phone)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    else:
        return ""
    return f"+{digits[0]} {digits[1:4]} {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"


def extract_digits(value: str) -> str:
    """Возвращает «полезные» цифры номера (максимум 10, без кода страны)."""
    digits = DIGITS_PATTERN.sub("", value)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        digits = digits[1:]
    return digits[:10]


# ==================== Контакт ====================

class Contact:
    """Запись телефонного справочника."""

    def __init__(self, name: str = "", phone: str = "", comment: str = ""):
        self.name = name
        self.phone = phone
        self.comment = comment

    def to_dict(self) -> dict:
        return {"name": self.name, "phone": self.phone, "comment": self.comment}

    @classmethod
    def from_dict(cls, data: dict) -> "Contact":
        return cls(
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            comment=data.get("comment", ""),
        )

    def __eq__(self, other):
        if not isinstance(other, Contact):
            return NotImplemented
        return (self.name, self.phone, self.comment) == (
            other.name, other.phone, other.comment
        )

    def __repr__(self):
        return (f"Contact(name={self.name!r}, "
                f"phone={self.phone!r}, comment={self.comment!r})")


# ==================== Справочник ====================

class PhoneBook:
    """Контейнер контактов с бизнес-операциями."""

    MAX_CONTACTS = 3

    def __init__(self):
        self.contacts: list[Contact] = []
        self.current_file: str | None = None
        self.dirty: bool = False

    # --- Операции над контактами ---

    def add_contact(self, contact: Contact) -> None:
        if len(self.contacts) >= self.MAX_CONTACTS:
            raise ContactLimitError(
                f"Достигнут лимит: не более {self.MAX_CONTACTS} записей"
            )
        self.contacts.append(contact)
        self.dirty = True

    def remove_contact(self, index: int) -> Contact:
        if index is None or index < 0 or index >= len(self.contacts):
            raise ContactNotFoundError("Контакт не найден")
        contact = self.contacts.pop(index)
        self.dirty = True
        return contact

    def edit_contact(self, index: int, contact: Contact) -> None:
        if index < 0 or index >= len(self.contacts):
            raise ContactNotFoundError("Контакт не найден")
        self.contacts[index] = contact
        self.dirty = True

    def find_index(self, name: str, phone: str, comment: str) -> int | None:
        for i, c in enumerate(self.contacts):
            if (c.name, c.phone, c.comment) == (name, phone, comment):
                return i
        return None

    def is_full(self) -> bool:
        return len(self.contacts) >= self.MAX_CONTACTS

    # --- Сортировка и поиск ---

    @staticmethod
    def sort_contacts(contacts: list[Contact], column: str,
                      reverse: bool = False) -> list[Contact]:
        return sorted(
            contacts,
            key=lambda c: getattr(c, column, "").lower(),
            reverse=reverse,
        )

    def search_contacts(self, query: str) -> list[Contact]:
        if not query:
            return self.contacts[:]
        q = query.lower()
        return [
            c for c in self.contacts
            if q in c.name.lower()
            or q in c.phone.lower()
            or q in c.comment.lower()
        ]


# ==================== Чтение файла ====================

class FileReader:
    """Загрузка контактов из JSON-файла."""

    @staticmethod
    def read(file_path: str) -> list[Contact]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as e:
            raise FileReadError(f"Файл {file_path} не найден") from e
        except json.JSONDecodeError as e:
            raise FileReadError(f"Ошибка парсинга JSON: {e}") from e
        except Exception as e:
            raise FileReadError(f"Ошибка при чтении файла: {e}") from e

        if not isinstance(data, dict):
            raise FileReadError("Неверная структура JSON-файла")

        raw_contacts = data.get("contacts", [])
        if not isinstance(raw_contacts, list):
            raise FileReadError("Поле 'contacts' должно быть списком")

        result: list[Contact] = []
        for item in raw_contacts:
            if not isinstance(item, dict):
                raise FileReadError("Неверный формат записи контакта")
            result.append(Contact.from_dict(item))
        return result


# ==================== Запись файла ====================

class FileWriter:
    """Сохранение контактов в JSON-файл."""

    @staticmethod
    def write(file_path: str, contacts: list[Contact]) -> None:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"contacts": [c.to_dict() for c in contacts]},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
        except Exception as e:
            raise FileWriteError(f"Ошибка при сохранении файла: {e}") from e

    @staticmethod
    def create_empty(file_path: str) -> None:
        FileWriter.write(file_path, [])