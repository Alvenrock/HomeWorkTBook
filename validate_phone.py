import re

# Строгая маска: +7 XXX XXX-XX-XX
PHONE_PATTERN = re.compile(r"^\+7 \d{3} \d{3}-\d{2}-\d{2}$")

# Всё, что не цифра
DIGITS_PATTERN = re.compile(r"\D")


def is_valid_phone(phone: str) -> bool:
    """Строгая проверка: соответствует ли строка маске +7 XXX XXX-XX-XX."""
    return bool(PHONE_PATTERN.match(phone.strip()))


def normalize_phone(phone: str) -> str:
    """
    Приводит произвольный ввод к виду +7 XXX XXX-XX-XX.
    Возвращает '' если цифр недостаточно/слишком много.
    """
    digits = DIGITS_PATTERN.sub("", phone)

    if len(digits) == 11 and digits[0] in ("7", "8"):
        digits = "7" + digits[1:]
    elif len(digits) == 10:
        digits = "7" + digits
    else:
        return ""

    return f"+{digits[0]} {digits[1:4]} {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"


def validate_and_normalize(phone: str):
    """
    Возвращает (ok: bool, normalized_or_error: str).
    """
    phone = phone.strip()

    if not phone:
        return False, "Телефон не может быть пустым"

    if is_valid_phone(phone):
        return True, phone

    normalized = normalize_phone(phone)
    if normalized:
        return True, normalized

    return False, "Неверный формат. Ожидается: +7 900 123-45-67"


def extract_digits(value: str) -> str:
    """
    Возвращает «полезные» цифры номера — максимум 10,
    без кода страны. Ведущие 7/8 отбрасываются, только если
    цифр изначально было 11 (то есть пользователь явно ввёл код).
    """
    digits = DIGITS_PATTERN.sub("", value)

    if len(digits) == 11 and digits[0] in ("7", "8"):
        digits = digits[1:]

    return digits[:10]


def format_as_you_type(value: str) -> str:
    """
    Форматирует строку по маске +7 XXX XXX-XX-XX по мере ввода.
    Гарантирует, что «полезная» часть — максимум 10 цифр.
    """
    digits = extract_digits(value)

    if not digits:
        return "+7 " if value.strip() else ""

    result = "+7 "

    if len(digits) >= 1:
        result += digits[0:3]
    if len(digits) > 3:
        result += " " + digits[3:6]
    if len(digits) > 6:
        result += "-" + digits[6:8]
    if len(digits) > 8:
        result += "-" + digits[8:10]

    return result