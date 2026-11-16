"""Представление (UI) телефонного справочника: окна, диалоги, виджеты."""
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from model import is_valid_phone


# ==================== Ограничения ввода ====================

NAME_ALLOWED = re.compile(r"^[A-Za-zА-Яа-яЁё\s\-']$", re.UNICODE)
MAX_LEN = 64

_SERVICE_KEYS = frozenset((
    "BackSpace", "Delete", "Left", "Right",
    "Home", "End", "Tab", "ISO_Left_Tab",
    "Shift_L", "Shift_R", "Control_L", "Control_R",
))


def _limit(entry: tk.Entry, max_len: int, char_filter=None):
    """Общая логика ограничения поля ввода (длина + фильтр символов)."""

    def _on_key(event):
        if event.keysym in _SERVICE_KEYS:
            return None
        if event.state & 0x4:  # Ctrl+...
            return None
        if len(entry.get()) >= max_len and not entry.selection_present():
            return "break"
        ch = event.char
        if char_filter and ch and not char_filter(ch):
            return "break"
        return None

    def _on_paste(event):
        def _fix():
            text = entry.get()
            filtered = "".join(c for c in text if char_filter(c)) if char_filter else text
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


def limit_length(entry: tk.Entry, max_len: int = MAX_LEN):
    _limit(entry, max_len, char_filter=None)


def limit_name(entry: tk.Entry, max_len: int = MAX_LEN):
    _limit(entry, max_len, char_filter=NAME_ALLOWED.fullmatch)


# ==================== Виджет ввода телефона ====================

class PhoneEntry(tk.Frame):
    """Поле телефона с автоформатированием по маске +7 XXX XXX-XX-XX."""

    def __init__(self, master, initial: str = "", on_change=None, **kwargs):
        super().__init__(master, **kwargs)

        self.var = tk.StringVar()
        self.entry = tk.Entry(self, textvariable=self.var, width=40)
        self.entry.pack(fill="x")

        self.hint = tk.Label(self, text="", anchor="w", fg="gray")
        self.hint.pack(fill="x")

        self._suppress = False
        self._on_change_callback = on_change

        self.var.trace_add("write", self._on_change)
        self.entry.bind("<FocusIn>", lambda _e: self.entry.icursor(tk.END))

        if initial:
            self.set(initial)
        else:
            self._render("")

    # ---------- Рендер ----------
    @staticmethod
    def _format(digits: str) -> str:
        if not digits:
            return "+7 "
        result = "+7 " + digits[0:3]
        if len(digits) > 3:
            result += " " + digits[3:6]
        if len(digits) > 6:
            result += "-" + digits[6:8]
        if len(digits) > 8:
            result += "-" + digits[8:10]
        return result

    def _render(self, digits: str):
        self._suppress = True
        try:
            self.var.set(self._format(digits))
            self.entry.icursor(tk.END)
        finally:
            self._suppress = False
        self._update_hint()

    # ---------- Обработка изменений ----------
    def _on_change(self, *_):
        if self._suppress:
            return
        current = self.var.get()
        digits = "".join(ch for ch in current if ch.isdigit())
        if digits.startswith("7"):
            digits = digits[1:]
        digits = digits[:10]
        formatted = self._format(digits)

        if current != formatted:
            self.entry.after_idle(lambda: self._render(digits))
        else:
            self._update_hint()
            self._notify_change()

    # ---------- Подсказка ----------
    def _update_hint(self):
        value = self.var.get()
        digits = "".join(ch for ch in value if ch.isdigit())
        useful = digits[1:] if digits.startswith("7") else digits
        if not useful:
            self.hint.config(text="Формат: +7 900 123-45-67", fg="gray")
        elif is_valid_phone(value):
            self.hint.config(text="✓ формат верный", fg="green")
        else:
            self.hint.config(text="Продолжайте ввод цифр…", fg="gray")

    def _notify_change(self):
        if self._on_change_callback:
            self._on_change_callback(self.is_valid())

    # ---------- Публичный API ----------
    def get(self) -> str:
        return self.var.get().strip()

    def is_valid(self) -> bool:
        return is_valid_phone(self.var.get().strip())

    def set(self, value: str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) == 11 and digits[0] in ("7", "8"):
            digits = digits[1:]
        elif len(digits) > 10:
            digits = digits[:10]
        self._render(digits)

    def focus(self):
        self.entry.focus_set()


# ==================== Диалог редактирования контакта ====================

class ContactDialog(tk.Toplevel):
    """Модальное окно добавления/редактирования контакта."""

    def __init__(self, parent, *, title: str,
                 initial: dict | None = None, on_submit=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x320")
        self.transient(parent)
        self.grab_set()

        initial = initial or {"name": "", "phone": "", "comment": ""}

        # --- Имя ---
        tk.Label(self, text="Имя:").pack(anchor="w", padx=10, pady=(10, 0))
        self.e_name = tk.Entry(self, width=40)
        self.e_name.insert(0, initial.get("name", ""))
        self.e_name.pack(padx=10, fill="x")
        limit_name(self.e_name, max_len=64)

        # --- Телефон ---
        tk.Label(self, text="Телефон:").pack(anchor="w", padx=10, pady=(10, 0))
        self.phone_entry = PhoneEntry(
            self,
            initial=initial.get("phone", ""),
            on_change=lambda _valid: self._update_save_state(),
        )
        self.phone_entry.pack(fill="x", padx=10)

        # --- Комментарий ---
        tk.Label(self, text="Комментарий:").pack(anchor="w", padx=10, pady=(10, 0))
        self.e_comment = tk.Entry(self, width=40)
        self.e_comment.insert(0, initial.get("comment", ""))
        self.e_comment.pack(padx=10, fill="x")
        limit_length(self.e_comment, max_len=64)

        # --- Кнопка ---
        self.btn_save = tk.Button(self, text="Сохранить",
                                  command=self._on_save, state="disabled")
        self.btn_save.pack(pady=15)

        self._on_submit = on_submit
        self._update_save_state()
        self.e_name.focus_set()

    def _update_save_state(self):
        self.btn_save.config(
            state="normal" if self.phone_entry.is_valid() else "disabled"
        )

    def _on_save(self):
        if not self.phone_entry.is_valid():
            return
        data = {
            "name": self.e_name.get().strip(),
            "phone": self.phone_entry.get(),
            "comment": self.e_comment.get().strip(),
        }
        if self._on_submit:
            self._on_submit(data)
        self.destroy()


# ==================== Главное окно ====================

class PhoneBookView:
    """Основное окно справочника. Общается с контроллером через callbacks."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Телефонная книга")
        self.root.geometry("900x500")
        self.callbacks: dict = {}

        self._build_toolbar()
        self._build_search_bar()
        self._build_table()
        self._build_statusbar()

    def set_callbacks(self, **callbacks):
        self.callbacks.update(callbacks)

    def _emit(self, name: str, *args, **kwargs):
        cb = self.callbacks.get(name)
        if cb:
            cb(*args, **kwargs)

    # ---------- Построение UI ----------
    def _build_toolbar(self):
        bar = tk.Frame(self.root)
        bar.pack(fill="x", pady=5)
        self.btn_load = tk.Button(bar, text="📂 Загрузить",
                                  command=lambda: self._emit("load"))
        self.btn_load.pack(side="left", padx=5)
        self.btn_save = tk.Button(bar, text="💾 Сохранить",
                                  command=lambda: self._emit("save"))
        self.btn_save.pack(side="left", padx=5)
        self.btn_add = tk.Button(bar, text="➕ Добавить",
                                 command=lambda: self._emit("add"))
        self.btn_add.pack(side="left", padx=5)
        self.btn_remove = tk.Button(bar, text="🗑 Удалить",
                                    command=lambda: self._emit("remove"))
        self.btn_remove.pack(side="left", padx=5)
        self.btn_edit = tk.Button(bar, text="✏ Изменить",
                                  command=lambda: self._emit("edit"))
        self.btn_edit.pack(side="left", padx=5)

    def _build_search_bar(self):
        bar = tk.Frame(self.root)
        bar.pack(fill="x", pady=5)
        tk.Label(bar, text="Поиск:").pack(side="left", padx=(10, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._emit("search"))
        self.entry_search = tk.Entry(bar, textvariable=self.search_var, width=40)
        self.entry_search.pack(side="left")
        limit_length(self.entry_search, max_len=64)
        self.btn_reset = tk.Button(bar, text="Сбросить",
                                   command=lambda: self.search_var.set(""))
        self.btn_reset.pack(side="left", padx=5)

    def _build_table(self):
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=5)
        columns = ("name", "phone", "comment")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings",
                                 selectmode="browse")
        self.tree.heading("name", text="Имя",
                          command=lambda: self._emit("sort", "name"))
        self.tree.heading("phone", text="Телефон",
                          command=lambda: self._emit("sort", "phone"))
        self.tree.heading("comment", text="Комментарий",
                          command=lambda: self._emit("sort", "comment"))
        self.tree.column("name", width=200)
        self.tree.column("phone", width=180)
        self.tree.column("comment", width=380)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", lambda _e: self._emit("edit"))

    def _build_statusbar(self):
        self.status = tk.StringVar(value="Готово")
        tk.Label(self.root, textvariable=self.status, anchor="w",
                 relief="sunken").pack(fill="x", side="bottom")

    # ---------- Публичный API ----------
    def render(self, contacts, status_text: str):
        self.tree.delete(*self.tree.get_children())
        for c in contacts:
            self.tree.insert("", "end", values=(c.name, c.phone, c.comment))
        self.status.set(status_text)

    def get_search_query(self) -> str:
        return self.search_var.get()

    def get_selected_values(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0], "values")

    def set_title(self, title: str):
        self.root.title(title)

    def set_status(self, text: str):
        self.status.set(text)

    def set_actions_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in (self.btn_save, self.btn_remove, self.btn_edit, self.btn_reset):
            btn.config(state=state)
        self.entry_search.config(state=state)

    def set_add_enabled(self, enabled: bool):
        self.btn_add.config(state="normal" if enabled else "disabled")

    # ---------- Сообщения ----------
    def show_message(self, kind: str, title: str, message: str):
        if kind == "info":
            messagebox.showinfo(title, message)
        elif kind == "warning":
            messagebox.showwarning(title, message)
        else:
            messagebox.showerror(title, message)

    def ask_yes_no(self, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message)

    def ask_yes_no_cancel(self, title: str, message: str):
        return messagebox.askyesnocancel(title, message)

    # ---------- Файловые диалоги ----------
    def ask_open_filename(self):
        return filedialog.askopenfilename(
            title="Выберите файл справочника",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
        )

    def ask_save_filename(self):
        return filedialog.asksaveasfilename(
            title="Сохранить как",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json")],
        )

    def ask_new_phonebook_path(self):
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Создать новый справочник",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")],
            initialfile="ТелефонныйСправочник.json",
        )
        if not path:
            return None
        if os.path.exists(path):
            if not messagebox.askyesno(
                "Файл существует",
                f"Файл\n{path}\nуже существует. Перезаписать его пустым справочником?",
            ):
                return None
        return path

    def open_contact_dialog(self, *, title: str,
                            initial: dict | None = None, on_submit=None):
        ContactDialog(self.root, title=title, initial=initial, on_submit=on_submit)