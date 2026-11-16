import tkinter as tk

from controller import PhoneBookController


if __name__ == "__main__":
    root = tk.Tk()
    app = PhoneBookController(root)
    root.mainloop()