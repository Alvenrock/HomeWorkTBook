import tkinter as tk

from phone_entry import PhoneEntry
from input_limits import limit_name, limit_length


def open_contact_dialog(parent, *, title, initial=None, on_submit=None):
    """
    Универсальное модальное окно редактирования контакта.

    parent      — родительское окно
    title       — заголовок окна
    initial     — dict с ключами name/phone/comment или None (для добавления)
    on_submit   — callback(dict) -> None, вызывается при сохранении
    """
    initial = initial or {"name": "", "phone": "", "comment": ""}

    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("400x320")
    win.transient(parent)
    win.grab_set()

    # --- Имя ---
    tk.Label(win, text="Имя:").pack(anchor="w", padx=10, pady=(10, 0))
    e_name = tk.Entry(win, width=40)
    e_name.insert(0, initial.get("name", ""))
    e_name.pack(padx=10, fill="x")
    limit_name(e_name, max_len=64)

    # --- Телефон ---
    tk.Label(win, text="Телефон:").pack(anchor="w", padx=10, pady=(10, 0))

    def form_is_valid() -> bool:
        return phone_entry.is_valid()

    def update_save_state():
        btn_save.config(state="normal" if form_is_valid() else "disabled")

    def on_save():
        if not form_is_valid():
            return
        data = {
            "name": e_name.get().strip(),
            "phone": phone_entry.get(),
            "comment": e_comment.get().strip(),
        }
        if on_submit:
            on_submit(data)
        win.destroy()

    phone_entry = PhoneEntry(win, initial=initial.get("phone", ""),
                             on_change=lambda _valid: update_save_state())
    phone_entry.pack(fill="x", padx=10)

    # --- Комментарий ---
    tk.Label(win, text="Комментарий:").pack(anchor="w", padx=10, pady=(10, 0))
    e_comment = tk.Entry(win, width=40)
    e_comment.insert(0, initial.get("comment", ""))
    e_comment.pack(padx=10, fill="x")
    limit_length(e_comment, max_len=64)

    # --- Кнопка ---
    btn_save = tk.Button(win, text="Сохранить",
                         command=on_save,
                         state="disabled")
    btn_save.pack(pady=15)

    update_save_state()
    e_name.focus_set()