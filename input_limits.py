import re
import tkinter as tk

# Буквы кириллица + латиница, пробел, дефис, апостроф.
NAME_ALLOWED = re.compile(r"^[A-Za-zА-Яа-яЁё\s\-']$", re.UNICODE)

MAX_LEN = 64

# Служебные клавиши, которые нужно пропускать без фильтрации
_SERVICE_KEYS = frozenset((
    "BackSpace", "Delete", "Left", "Right",
    "Home", "End", "Tab", "ISO_Left_Tab",
    "Shift_L", "Shift_R", "Control_L", "Control_R",
))


def _limit(entry: tk.Entry, max_len: int, char_filter=None):
    """
    Общая логика ограничения поля ввода.

    entry       — виджет Entry
    max_len     — максимальная длина
    char_filter — callable(char) -> bool, если задан, ввод фильтруется
    """

    def _on_key(event):
        # Служебные клавиши — пропускаем
        if event.keysym in _SERVICE_KEYS:
            return None
        # Ctrl+... — не мешаем (фильтрация после вставки)
        if event.state & 0x4:
            return None
        # Ограничение длины
        if len(entry.get()) >= max_len and not entry.selection_present():
            return "break"
        # Фильтр символов (если задан)
        ch = event.char
        if char_filter and ch and not char_filter(ch):
            return "break"
        return None

    def _on_paste(event):
        def _fix():
            text = entry.get()
            if char_filter:
                # Фильтруем запрещённые символы и обрезаем
                filtered = "".join(c for c in text if char_filter(c))
            else:
                filtered = text
            filtered = filtered[:max_len]
            if filtered != text:
                try:
                    pos = entry.index(tk.INSERT)
                except tk.TclError:
                    pos = len(filtered)
                entry.delete(0, tk.END)
                entry.insert(0, filtered)
                entry.icursor(min(pos, len(filtered)))
        entry.after_idle(_fix)
        return None

    entry.bind("<KeyPress>", _on_key, add="+")
    entry.bind("<<Paste>>", _on_paste, add="+")


# ---------- Публичный API ----------

def limit_length(entry: tk.Entry, max_len: int = MAX_LEN):
    """Ограничивает количество символов в поле до max_len."""
    _limit(entry, max_len, char_filter=None)


def limit_name(entry: tk.Entry, max_len: int = MAX_LEN):
    """Поле имени: только буквы, пробел, дефис, апостроф, максимум max_len."""
    _limit(entry, max_len, char_filter=NAME_ALLOWED.fullmatch)