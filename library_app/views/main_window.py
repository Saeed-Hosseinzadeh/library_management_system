import tkinter as tk
from tkinter import ttk

from library_app.controllers.app_controller import AppController
from library_app.views.book_view import BookView
from library_app.views.loan_view import LoanView
from library_app.views.member_view import MemberView


class MainWindow:
    """Main Tk application window."""

    def __init__(self, app_controller: AppController):
        self._app_controller = app_controller
        self.root = tk.Tk()
        self.root.title("Library Management System")
        self.root.geometry("1300x720")
        self.root.minsize(1100, 650)

        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(self.root, padding=12)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.content = ttk.Frame(self.root, padding=12)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        self._build_sidebar()
        self.show_books_view()

    def _build_sidebar(self):
        ttk.Label(self.sidebar, text="Library System", font=("Segoe UI", 14, "bold")).pack(
            fill="x",
            pady=(0, 16),
        )

        ttk.Button(self.sidebar, text="Books", command=self.show_books_view).pack(fill="x", pady=4)
        ttk.Button(self.sidebar, text="Members", command=self.show_members_view).pack(fill="x", pady=4)
        ttk.Button(self.sidebar, text="Loans", command=self.show_loans_view).pack(fill="x", pady=4)

    def _clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def show_books_view(self):
        self._clear_content()
        view = BookView(self.content, self._app_controller.books)
        view.grid(row=0, column=0, sticky="nsew")

    def show_members_view(self):
        self._clear_content()
        view = MemberView(self.content, self._app_controller.members)
        view.grid(row=0, column=0, sticky="nsew")

    def show_loans_view(self):
        self._clear_content()
        view = LoanView(self.content, self._app_controller.loans)
        view.grid(row=0, column=0, sticky="nsew")

    def run(self):
        self.root.mainloop()
