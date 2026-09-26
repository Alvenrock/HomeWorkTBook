import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox


def ask_new_phonebook_path(parent) -> str | None:
    """
    Спрашивает путь нового JSON-файла справочника.
    Возвращает путь или None, если пользователь отменил.
    """
    # Сначала спрашиваем папку и имя через стандартный диалог сохранения —
    # это удобнее, чем отдельное окно, и сразу даёт валидный путь.
    path = filedialog.asksaveasfilename(
        parent=parent,
        title="Создать новый справочник",
        defaultextension=".json",
        filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
        initialfile="ТелефонныйСправочник.json"
    )
    if not path:
        return None

    # Если файл существует — спросим подтверждение
    if os.path.exists(path):
        if not messagebox.askyesno(
            "Файл существует",
            f"Файл\n{path}\nуже существует. Перезаписать его пустым справочником?"
        ):
            return None

    # Создаём пустой файл
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"contacts": []}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось создать файл:\n{e}")
        return None

    return path