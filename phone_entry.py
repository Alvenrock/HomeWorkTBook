import tkinter as tk

from validate_phone import is_valid_phone


class PhoneEntry(tk.Frame):
    """
    Поле ввода телефона с автоформатированием по маске +7 XXX XXX-XX-XX.
    Пользователь вводит только цифры, разделители подставляются сами.
    """

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
        # ВАЖНО: callback здесь НЕ вызывается — родитель сам вызовет
        # update_save_state() после создания виджета.

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
        # self._notify_change() тут НЕ вызываем

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