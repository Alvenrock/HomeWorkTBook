import json


def load_file(file_path):
    """
    Загружает контакты из JSON-файла.
    Возвращает список словарей [{"name": ..., "phone": ..., "comment": ...}, ...]
    или [] при ошибке.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            contacts = data.get("contacts", [])
            print(f"Загружено {len(contacts)} контактов из {file_path}")
            return contacts
    except FileNotFoundError:
        print(f"Файл {file_path} не найден")
        return []
    except json.JSONDecodeError as e:
        print(f"Ошибка парсинга JSON: {e}")
        return []
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return []