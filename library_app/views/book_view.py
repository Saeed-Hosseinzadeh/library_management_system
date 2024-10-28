import tkinter as tk
from tkinter import messagebox, ttk

from library_app.controllers.book_controller import BookController


class BookView(ttk.Frame):
    """Book management frame."""

    def __init__(self, master, controller: BookController):
        super().__init__(master, padding=12)
        self.controller = controller
        self.selected_book_id = None

        self.title_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.isbn_var = tk.StringVar()
        self.publisher_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.copies_var = tk.StringVar()
        self.quantity_var = tk.StringVar()
        self.search_var = tk.StringVar()

        self._build_layout()
        self.refresh_books()

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        search_frame = ttk.Frame(self)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Search").grid(row=0, column=0, padx=(0, 8))
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(search_frame, text="Find", command=self.search_books).grid(row=0, column=2, padx=6)
        ttk.Button(search_frame, text="Refresh", command=self.refresh_books).grid(row=0, column=3)

        body = ttk.Frame(self)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            body,
            columns=(
                "id",
                "title",
                "author",
                "isbn",
                "publisher",
                "category",
                "year",
                "copies_total",
                "quantity",
            ),
            show="headings",
            height=18,
        )
        headings = {
            "id": "ID",
            "title": "Title",
            "author": "Author",
            "isbn": "ISBN",
            "publisher": "Publisher",
            "category": "Category",
            "year": "Year",
            "copies_total": "Copies",
            "quantity": "Available",
        }
        widths = {
            "id": 60,
            "title": 180,
            "author": 150,
            "isbn": 120,
            "publisher": 130,
            "category": 110,
            "year": 80,
            "copies_total": 80,
            "quantity": 80,
        }
        for key, text in headings.items():
            self.tree.heading(key, text=text)
            self.tree.column(key, width=widths[key], anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        y_scroll = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=y_scroll.set)

        form = ttk.LabelFrame(body, text="Book Details", padding=12)
        form.grid(row=0, column=2, sticky="nsew", padx=(12, 0))
        form.columnconfigure(1, weight=1)

        fields = [
            ("Title", self.title_var),
            ("Author", self.author_var),
            ("ISBN", self.isbn_var),
            ("Publisher", self.publisher_var),
            ("Category", self.category_var),
            ("Publication Year", self.year_var),
            ("Copies Total", self.copies_var),
            ("Available Quantity", self.quantity_var),
        ]

        for row_index, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row_index, column=0, sticky="w", pady=4, padx=(0, 8))
            ttk.Entry(form, textvariable=variable).grid(row=row_index, column=1, sticky="ew", pady=4)

        actions = ttk.Frame(form)
        actions.grid(row=len(fields), column=0, columnspan=2, sticky="ew", pady=(12, 0))
        actions.columnconfigure((0, 1), weight=1)

        ttk.Button(actions, text="Add", command=self.add_book).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(actions, text="Update", command=self.update_book).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(actions, text="Remove", command=self.remove_book).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(8, 0))
        ttk.Button(actions, text="Clear", command=self.clear_form).grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(8, 0))

    def _to_int_or_none(self, value: str):
        value = value.strip()
        return int(value) if value else None

    def _collect_payload(self) -> dict:
        return {
            "title": self.title_var.get(),
            "author": self.author_var.get(),
            "isbn": self.isbn_var.get(),
            "publisher": self.publisher_var.get().strip() or None,
            "category": self.category_var.get().strip() or None,
            "publication_year": self._to_int_or_none(self.year_var.get()),
            "copies_total": int(self.copies_var.get().strip()),
            "quantity": int(self.quantity_var.get().strip()),
        }

    def _show_error(self, result):
        messagebox.showerror("Error", result.message or "Operation failed.")

    def refresh_books(self):
        result = self.controller.list_books()
        if not result.success:
            self._show_error(result)
            return
        self._load_books(result.data or [])

    def search_books(self):
        query = self.search_var.get().strip()
        if not query:
            self.refresh_books()
            return
        result = self.controller.search_books(query)
        if not result.success:
            self._show_error(result)
            return
        self._load_books(result.data or [])

    def _load_books(self, books):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for book in books:
            self.tree.insert(
                "",
                "end",
                iid=str(book.id),
                values=(
                    book.id,
                    book.title,
                    book.author,
                    book.isbn,
                    book.publisher or "",
                    book.category or "",
                    book.publication_year or "",
                    book.copies_total,
                    book.quantity,
                ),
            )

    def on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return

        item_id = selection[0]
        values = self.tree.item(item_id, "values")
        self.selected_book_id = int(values[0])

        self.title_var.set(values[1])
        self.author_var.set(values[2])
        self.isbn_var.set(values[3])
        self.publisher_var.set(values[4])
        self.category_var.set(values[5])
        self.year_var.set(values[6])
        self.copies_var.set(values[7])
        self.quantity_var.set(values[8])

    def add_book(self):
        try:
            payload = self._collect_payload()
            result = self.controller.add_book(**payload)
            if not result.success:
                self._show_error(result)
                return
            self.clear_form()
            self.refresh_books()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def update_book(self):
        if self.selected_book_id is None:
            messagebox.showerror("Error", "Select a book first.")
            return

        try:
            payload = self._collect_payload()
            result = self.controller.update_book(self.selected_book_id, **payload)
            if not result.success:
                self._show_error(result)
                return
            self.clear_form()
            self.refresh_books()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def remove_book(self):
        if self.selected_book_id is None:
            messagebox.showerror("Error", "Select a book first.")
            return

        if not messagebox.askyesno("Confirm", "Remove selected book?"):
            return

        result = self.controller.remove_book(self.selected_book_id)
        if not result.success:
            self._show_error(result)
            return

        self.clear_form()
        self.refresh_books()

    def clear_form(self):
        self.selected_book_id = None
        self.title_var.set("")
        self.author_var.set("")
        self.isbn_var.set("")
        self.publisher_var.set("")
        self.category_var.set("")
        self.year_var.set("")
        self.copies_var.set("")
        self.quantity_var.set("")
        self.tree.selection_remove(self.tree.selection())
