"""Контроллер телефонного справочника: связывает модель и представление."""
import tkinter as tk

from model import (
    PhoneBook, Contact, FileReader, FileWriter,
    ContactLimitError, ContactNotFoundError,
    FileReadError, FileWriteError,
)
from view import PhoneBookView


class PhoneBookController:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.model = PhoneBook()
        self.view = PhoneBookView(root)

        self.sort_column: str | None = None
        self.sort_reverse: bool = False

        self.view.set_callbacks(
            load=self.on_load,
            save=self.on_save,
            add=self.on_add,
            remove=self.on_remove,
            edit=self.on_edit,
            search=self.on_search,
            sort=self.on_sort,
            close=self.on_close,
        )

        self.view.set_actions_enabled(False)
        self.view.set_add_enabled(True)
        self.view.set_status("Файл не загружен")

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ==================== Обновление ====================

    def refresh(self):
        query = self.view.get_search_query()
        filtered = self.model.search_contacts(query)
        if self.sort_column:
            filtered = self.model.sort_contacts(
                filtered, self.sort_column, self.sort_reverse
            )
        status = (
            f"Показано: {len(filtered)} из {len(self.model.contacts)} "
            f"(лимит: {self.model.MAX_CONTACTS})"
        )
        self.view.render(filtered, status)
        self.view.set_add_enabled(not self.model.is_full())

    def _update_title(self):
        title = "Телефонная книга"
        if self.model.current_file:
            title += f" — {self.model.current_file.split('/')[-1]}"
        if self.model.dirty:
            title += " *"
        self.view.set_title(title)

    # ==================== Обработчики событий ====================

    def on_load(self):
        path = self.view.ask_open_filename()
        if not path:
            return
        try:
            contacts = FileReader.read(path)
        except FileReadError as e:
            self.view.show_message("error", "Ошибка", str(e))
            return

        if not contacts:
            self.view.show_message("warning", "Внимание",
                                   "Файл пуст или содержит ошибки")
            self.view.set_actions_enabled(False)
            self.view.set_add_enabled(not self.model.is_full())
            self.view.set_status("Файл не загружен")
            return

        self.model.contacts = contacts
        self.model.current_file = path
        self.model.dirty = False
        self.refresh()
        self.view.set_actions_enabled(True)
        self._update_title()
        self.view.show_message("info", "Готово",
                               f"Загружено контактов: {len(contacts)}")

    def on_save(self):
        if not self.model.contacts:
            self.view.show_message("warning", "Внимание",
                                   "Нет данных для сохранения")
            return
        path = self.model.current_file or self.view.ask_save_filename()
        if not path:
            return
        try:
            FileWriter.write(path, self.model.contacts)
        except FileWriteError as e:
            self.view.show_message("error", "Ошибка", str(e))
            return
        self.model.current_file = path
        self.model.dirty = False
        self._update_title()
        self.view.show_message("info", "Готово", f"Сохранено в {path}")

    def on_add(self):
        # Нет файла — предлагаем создать новый справочник
        if self.model.current_file is None:
            path = self.view.ask_new_phonebook_path()
            if not path:
                return
            try:
                FileWriter.create_empty(path)
            except FileWriteError as e:
                self.view.show_message("error", "Ошибка", str(e))
                return
            self.model.contacts = []
            self.model.current_file = path
            self.model.dirty = False
            self.refresh()
            self.view.set_actions_enabled(True)
            self._update_title()

        if self.model.is_full():
            self.view.show_message(
                "warning", "Внимание",
                f"Достигнут лимит: не более {self.model.MAX_CONTACTS} записей",
            )
            return

        def on_submit(data: dict):
            try:
                self.model.add_contact(Contact(**data))
            except ContactLimitError as e:
                self.view.show_message("warning", "Внимание", str(e))
                return
            self.refresh()
            self._update_title()

        self.view.open_contact_dialog(
            title="Добавить контакт", on_submit=on_submit
        )

    def on_remove(self):
        values = self.view.get_selected_values()
        if not values:
            self.view.show_message("warning", "Внимание",
                                   "Выберите контакт для удаления")
            return
        idx = self.model.find_index(*values)
        if idx is None:
            self.view.show_message("warning", "Внимание", "Контакт не найден")
            return
        contact = self.model.contacts[idx]
        if not self.view.ask_yes_no(
            "Подтверждение", f"Удалить контакт «{contact.name}»?"
        ):
            return
        try:
            self.model.remove_contact(idx)
        except ContactNotFoundError as e:
            self.view.show_message("warning", "Внимание", str(e))
            return
        self.refresh()
        self._update_title()

    def on_edit(self):
        values = self.view.get_selected_values()
        if not values:
            self.view.show_message("warning", "Внимание",
                                   "Выберите контакт для изменения")
            return
        idx = self.model.find_index(*values)
        if idx is None:
            self.view.show_message("warning", "Внимание", "Контакт не найден")
            return
        contact = self.model.contacts[idx]

        def on_submit(data: dict):
            try:
                self.model.edit_contact(idx, Contact(**data))
            except ContactNotFoundError as e:
                self.view.show_message("warning", "Внимание", str(e))
                return
            self.refresh()
            self._update_title()

        self.view.open_contact_dialog(
            title="Изменить контакт",
            initial=contact.to_dict(),
            on_submit=on_submit,
        )

    def on_search(self):
        self.refresh()

    def on_sort(self, column: str):
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        self.refresh()

    def on_close(self):
        if self.model.current_file is None or not self.model.dirty:
            self.root.destroy()
            return

        answer = self.view.ask_yes_no_cancel(
            "Выход", "Сохранить изменения перед закрытием?"
        )
        if answer is None:
            return
        if answer:
            try:
                FileWriter.write(self.model.current_file, self.model.contacts)
            except FileWriteError as e:
                self.view.show_message(
                    "error", "Ошибка",
                    f"Не удалось сохранить файл: {e}\nОкно не будет закрыто.",
                )
                return
            self.model.dirty = False
        self.root.destroy()