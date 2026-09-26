from tkinter import messagebox

from contact_dialog import open_contact_dialog


def add_contact(parent, contacts, refresh_callback, max_contacts=100):
    if len(contacts) >= max_contacts:
        messagebox.showwarning(
            "Внимание",
            f"Достигнут лимит: не более {max_contacts} записей в справочнике"
        )
        return

    def on_submit(data):
        if len(contacts) >= max_contacts:
            messagebox.showwarning(
                "Внимание",
                f"Достигнут лимит: не более {max_contacts} записей"
            )
            return
        contacts.append(data)
        refresh_callback()

    open_contact_dialog(parent, title="Добавить контакт", on_submit=on_submit)