import tkinter as tk
from tkinter import messagebox

from phone_entry import PhoneEntry
from input_limits import limit_name, limit_length


def add_contact(parent, contacts, refresh_callback, max_contacts=100):
    if len(contacts) >= max_contacts:
        messagebox.showwarning(
            "Внимание",
            f"Достигнут лимит: не более {max_contacts} записей в справочнике"
        )
        return

    win = tk.Toplevel(parent)
    win.title("Добавить контакт")
    win.geometry("400x320")
    win.transient(parent)
    win.grab_set()

    # --- Имя ---
    tk.Label(win, text="Имя:").pack(anchor="w", padx=10, pady=(10, 0))
    entry_name = tk.Entry(win, width=40)
    entry_name.pack(padx=10, fill="x")
    limit_name(entry_name, max_len=64)

    # --- Телефон ---
    tk.Label(win, text="Телефон:").pack(anchor="w", padx=10, pady=(10, 0))

    def form_is_valid() -> bool:
        return phone_entry.is_valid()

    def update_save_state():
        btn_save.config(state="normal" if form_is_valid() else "disabled")

    def on_save():
        if not form_is_valid():
            return
        if len(contacts) >= max_contacts:
            messagebox.showwarning(
                "Внимание",
                f"Достигнут лимит: не более {max_contacts} записей"
            )
            win.destroy()
            return
        contacts.append({
            "name": entry_name.get().strip(),
            "phone": phone_entry.get(),
            "comment": entry_comment.get().strip(),
        })
        refresh_callback()
        win.destroy()

    phone_entry = PhoneEntry(win, on_change=lambda _valid: update_save_state())
    phone_entry.pack(fill="x", padx=10)

    # --- Комментарий ---
    tk.Label(win, text="Комментарий:").pack(anchor="w", padx=10, pady=(10, 0))
    entry_comment = tk.Entry(win, width=40)
    entry_comment.pack(padx=10, fill="x")
    limit_length(entry_comment, max_len=64)

    # --- Кнопка ---
    btn_save = tk.Button(win, text="Сохранить",
                         command=lambda: on_save(),
                         state="disabled")
    btn_save.pack(pady=15)

    update_save_state()
    entry_name.focus_set()