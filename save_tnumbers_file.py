import json


def save_file(file_path, contacts):
    """
    Сохраняет список контактов в JSON-файл.
    Возвращает True при успехе, False при ошибке.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump({"contacts": contacts}, file, ensure_ascii=False, indent=2)
        print(f"Сохранено {len(contacts)} контактов в {file_path}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")
        return False