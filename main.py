import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import contact_dialog
import add_tnumber
import remove_tnumber
import sort_n_search_tnumber as sns
import download_tnumbers_file
import save_tnumbers_file
import new_phonebook
from phone_entry import PhoneEntry
from input_limits import limit_name, limit_length


MAX_CONTACTS = 100   # максимальное количество записей в справочнике


class PhoneBook:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Телефонная книга")
        self.root.geometry("900x500")

        self.contacts = []
        self.filtered = []
        self.current_file = None
        self.sort_column = None
        self.sort_reverse = False
        self.dirty = False

        self._build_toolbar()
        self._build_search_bar()
        self._build_table()
        self._build_statusbar()

        # Изначально файл не загружен — блокируем всё, кроме «Загрузить» и «Добавить»
        self._set_actions_enabled(False)
        self.status.set("Файл не загружен")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------ UI ------------------
    def _build_toolbar(self):
        bar = tk.Frame(self.root)
        bar.pack(fill="x", pady=5)

        self.btn_load = tk.Button(bar, text="📂 Загрузить", command=self.download)
        self.btn_load.pack(side="left", padx=5)

        self.btn_save = tk.Button(bar, text="💾 Сохранить", command=self.save)
        self.btn_save.pack(side="left", padx=5)

        self.btn_add = tk.Button(bar, text="➕ Добавить", command=self.add)
        self.btn_add.pack(side="left", padx=5)

        self.btn_remove = tk.Button(bar, text="🗑 Удалить", command=self.remove)
        self.btn_remove.pack(side="left", padx=5)

        self.btn_edit = tk.Button(bar, text="✏ Изменить", command=self.edit)
        self.btn_edit.pack(side="left", padx=5)

    def _build_search_bar(self):
        bar = tk.Frame(self.root)
        bar.pack(fill="x", pady=5)

        tk.Label(bar, text="Поиск:").pack(side="left", padx=(10, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace_add(
            "write",
            lambda _name, _index, _mode: self.refresh()
        )
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
        self.tree.heading("name", text="Имя", command=lambda: self.sort_by("name"))
        self.tree.heading("phone", text="Телефон", command=lambda: self.sort_by("phone"))
        self.tree.heading("comment", text="Комментарий", command=lambda: self.sort_by("comment"))

        self.tree.column("name", width=200)
        self.tree.column("phone", width=180)
        self.tree.column("comment", width=380)

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda _e: self.edit())

    def _build_statusbar(self):
        self.status = tk.StringVar(value="Готово")
        tk.Label(self.root, textvariable=self.status, anchor="w",
                 relief="sunken").pack(fill="x", side="bottom")

    # ------------------ Состояние ------------------
    def _set_actions_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for btn in (self.btn_save, self.btn_remove, self.btn_edit, self.btn_reset):
            btn.config(state=state)
        self.entry_search.config(state=state)
        self._update_add_button()

    def _update_add_button(self):
        """Кнопка «Добавить» активна всегда, кроме случая, когда достигнут лимит."""
        if len(self.contacts) >= MAX_CONTACTS:
            self.btn_add.config(state="disabled")
        else:
            self.btn_add.config(state="normal")

    def _update_title(self):
        title = "Телефонная книга"
        if self.current_file:
            title += f" — {self.current_file.split('/')[-1]}"
        if self.dirty:
            title += " *"
        self.root.title(title)

    # ------------------ Логика ------------------
    def refresh(self):
        self.filtered = sns.search_contacts(self.contacts, self.search_var.get())

        if self.sort_column:
            self.filtered = sns.sort_contacts(self.filtered,
                                              self.sort_column,
                                              self.sort_reverse)

        self.tree.delete(*self.tree.get_children())
        for c in self.filtered:
            self.tree.insert("", "end",
                             values=(c["name"], c["phone"], c["comment"]))

        self.status.set(
            f"Показано: {len(self.filtered)} из {len(self.contacts)} "
            f"(лимит: {MAX_CONTACTS})"
        )

        self._update_add_button()

    def _selected_index(self):
        sel = self.tree.selection()
        if not sel:
            return None
        values = self.tree.item(sel[0], "values")
        for i, c in enumerate(self.contacts):
            if (c["name"], c["phone"], c["comment"]) == tuple(values):
                return i
        return None

    # ---------- Команды кнопок ----------
    def download(self):
        path = filedialog.askopenfilename(
            title="Выберите файл справочника",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        if not path:
            return
        data = download_tnumbers_file.load_file(path)
        if data:
            self.contacts = data
            self.current_file = path
            self.dirty = False
            self.refresh()
            self._set_actions_enabled(True)
            self._update_title()
            messagebox.showinfo("Готово", f"Загружено контактов: {len(self.contacts)}")
        else:
            messagebox.showwarning("Внимание", "Файл пуст или содержит ошибки")
            self._set_actions_enabled(False)
            self.status.set("Файл не загружен")

    def save(self):
        if not self.contacts:
            messagebox.showwarning("Внимание", "Нет данных для сохранения")
            return
        path = self.current_file or filedialog.asksaveasfilename(
            title="Сохранить как",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json")]
        )
        if not path:
            return
        if save_tnumbers_file.save_file(path, self.contacts):
            self.current_file = path
            self.dirty = False
            self._update_title()
            messagebox.showinfo("Готово", f"Сохранено в {path}")

    def add(self):
        # Если файл ещё не создан/не загружен — предложить создать новый справочник
        if self.current_file is None:
            path = new_phonebook.ask_new_phonebook_path(self.root)
            if not path:
                return

            self.contacts = []
            self.current_file = path
            self.dirty = False
            self.refresh()
            self._set_actions_enabled(True)
            self._update_title()

        # Проверка лимита
        if len(self.contacts) >= MAX_CONTACTS:
            messagebox.showwarning(
                "Внимание",
                f"Достигнут лимит: не более {MAX_CONTACTS} записей в справочнике"
            )
            return

        before = len(self.contacts)
        add_tnumber.add_contact(self.root, self.contacts, self.refresh,
                                max_contacts=MAX_CONTACTS)
        if len(self.contacts) != before:
            self.dirty = True
            self._update_title()

    def remove(self):
        idx = self._selected_index()
        before = len(self.contacts)
        remove_tnumber.remove_contact(self.root, self.contacts, idx, self.refresh)
        if len(self.contacts) != before:
            self.dirty = True
            self._update_title()
            self._update_add_button()

    def edit(self):
        idx = self._selected_index()
        if idx is None:
            messagebox.showwarning("Внимание", "Выберите контакт для изменения")
            return

        contact = self.contacts[idx]

        def on_submit(data):
            self.contacts[idx] = data
            self.dirty = True
            self._update_title()
            self.refresh()

        contact_dialog.open_contact_dialog(
            self.root,
            title="Изменить контакт",
            initial=contact,
            on_submit=on_submit,
        )

        def form_is_valid() -> bool:
            return phone_entry.is_valid()

        def update_save_state():
            btn_save.config(state="normal" if form_is_valid() else "disabled")

        def on_save():
            if not form_is_valid():
                return
            self.contacts[idx] = {
                "name": e_name.get().strip(),
                "phone": phone_entry.get(),
                "comment": e_comment.get().strip(),
            }
            self.dirty = True
            self._update_title()
            self.refresh()
            win.destroy()

        phone_entry = PhoneEntry(win, initial=contact["phone"],
                                 on_change=lambda _valid: update_save_state())
        phone_entry.pack(fill="x", padx=10)

        # --- Комментарий ---
        tk.Label(win, text="Комментарий:").pack(anchor="w", padx=10, pady=(10, 0))
        e_comment = tk.Entry(win, width=40)
        e_comment.insert(0, contact["comment"])
        e_comment.pack(padx=10, fill="x")
        limit_length(e_comment, max_len=64)

        # --- Кнопка ---
        btn_save = tk.Button(win, text="Сохранить",
                             command=lambda: on_save(),
                             state="disabled")
        btn_save.pack(pady=15)

        update_save_state()

    def sort_by(self, column):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh()

    # ---------- Закрытие окна ----------
    def on_close(self):
        if self.current_file is None:
            self.root.destroy()
            return

        if not self.dirty:
            self.root.destroy()
            return

        answer = messagebox.askyesnocancel(
            "Выход",
            "Сохранить изменения перед закрытием?"
        )

        if answer is None:
            return

        if answer:
            if not save_tnumbers_file.save_file(self.current_file, self.contacts):
                messagebox.showerror("Ошибка",
                                     "Не удалось сохранить файл. "
                                     "Окно не будет закрыто.")
                return
            self.dirty = False

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PhoneBook(root)
    root.mainloop()