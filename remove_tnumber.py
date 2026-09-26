from tkinter import messagebox


def remove_contact(parent, contacts, index, refresh_callback):
    """
    Удаляет контакт по индексу после подтверждения.
    """
    if index is None or index < 0 or index >= len(contacts):
        messagebox.showwarning("Внимание", "Выберите контакт для удаления")
        return

    contact = contacts[index]
    if messagebox.askyesno("Подтверждение",
                           f"Удалить контакт «{contact['name']}»?"):
        contacts.pop(index)
        refresh_callback()