"""
Book management view.

Provides:
- Table grid (Treeview) listing all books.
- Search bar for filtering books.
- Input form for adding/updating books.
- Buttons that interact with BookController via ControllerResult.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Sequence, Optional

from library_app.controllers.book_controller import BookController
from library_app.db.models import Book


class BookView(ttk.Frame):
    """UI panel for book management operations."""

    def __init__(self, parent: tk.Widget, controller: BookController) -> None:
        """Initialize the book management view.

        Args:
            parent: Parent Tk widget or frame.
            controller: BookController instance injected from AppController.
        """
        super().__init__(parent)
        self.controller = controller

        # Tkinter variables for form inputs
        self.title_var = tk.StringVar()
        self.author_var = tk.StringVar()
        self.isbn_var = tk.StringVar()
        self.publisher_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.copies_var = tk.StringVar(value="1")

        self.search_var = tk.StringVar()

        self._build_layout()
        self._load_books()

    # ----------------------------------------------------------------------
    # Layout
    # ----------------------------------------------------------------------
    def _build_layout(self) -> None:
        """Build the visual layout (search bar, table, form, buttons)."""
        # ==================================================================
        # Search bar
        # ==================================================================
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Search Books:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="Search", command=self._search_books).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Reset", command=self._load_books).pack(side=tk.LEFT)

        # ==================================================================
        # Treeview table
        # ==================================================================
        self.tree = ttk.Treeview(
            self,
            columns=("id", "title", "author", "isbn", "publisher",
                     "category", "year", "copies"),
            show="headings",
            height=12,
        )

        for col in ("id", "title", "author", "isbn", "publisher", "category", "year", "copies"):
            self.tree.heading(col, text=col.capitalize())
            self.tree.column(col, width=120, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # ==================================================================
        # Input form
        # ==================================================================
        form_frame = ttk.LabelFrame(self, text="Book Details", padding=10)
        form_frame.pack(fill=tk.X, pady=10)

        # Row 1
        ttk.Label(form_frame, text="Title:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.title_var).grid(row=0, column=1, sticky=tk.EW, padx=5)

        ttk.Label(form_frame, text="Author:").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(form_frame, textvariable=self.author_var).grid(row=0, column=3, sticky=tk.EW, padx=5)

        # Row 2
        ttk.Label(form_frame, text="ISBN:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.isbn_var).grid(row=1, column=1, sticky=tk.EW, padx=5)

        ttk.Label(form_frame, text="Publisher:").grid(row=1, column=2, sticky=tk.W, padx=5)
        ttk.Entry(form_frame, textvariable=self.publisher_var).grid(row=1, column=3, sticky=tk.EW, padx=5)

        # Row 3
        ttk.Label(form_frame, text="Category:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.category_var).grid(row=2, column=1, sticky=tk.EW, padx=5)

        ttk.Label(form_frame, text="Year:").grid(row=2, column=2, sticky=tk.W, padx=5)
        ttk.Entry(form_frame, textvariable=self.year_var).grid(row=2, column=3, sticky=tk.EW, padx=5)

        # Row 4
        ttk.Label(form_frame, text="Copies:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.copies_var).grid(row=3, column=1, sticky=tk.EW, padx=5)

        for i in range(4):
            form_frame.columnconfigure(i, weight=1)

        # ==================================================================
        # Buttons
        # ==================================================================
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Add Book", command=self._add_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Update Selected", command=self._update_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self._delete_book).pack(side=tk.LEFT, padx=5)

    # ----------------------------------------------------------------------
    # Data Loading / Search
    # ----------------------------------------------------------------------
    def _load_books(self) -> None:
        """Load all books into the Treeview."""
        self.tree.delete(*self.tree.get_children())
        result = self.controller.get_all_books()

        if not result.success:
            messagebox.showerror("Error", result.message)
            return

        for book in result.data or []:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    book.id,
                    book.title,
                    book.author,
                    book.isbn,
                    book.publisher or "",
                    book.category or "",
                    book.publication_year or "",
                    book.copies_total,
                ),
            )

    def _search_books(self) -> None:
        """Search for books and reload the Treeview."""
        query = self.search_var.get().strip()
        result = self.controller.search_books(query)

        self.tree.delete(*self.tree.get_children())
        if not result.success:
            messagebox.showerror("Search Error", result.message)
            return

        for book in result.data or []:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    book.id,
                    book.title,
                    book.author,
                    book.isbn,
                    book.publisher or "",
                    book.category or "",
                    book.publication_year or "",
                    book.copies_total,
                ),
            )

    # ----------------------------------------------------------------------
    # Tree Selection -> load into form
    # ----------------------------------------------------------------------
    def _on_tree_select(self, event: tk.Event) -> None:
        """Load selected book data into input fields."""
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        (
            _id,
            title,
            author,
            isbn,
            publisher,
            category,
            year,
            copies,
        ) = values

        self.title_var.set(title)
        self.author_var.set(author)
        self.isbn_var.set(isbn)
        self.publisher_var.set(publisher)
        self.category_var.set(category)
        self.year_var.set(year)
        self.copies_var.set(copies)

    # ----------------------------------------------------------------------
    # Controller Actions
    # ----------------------------------------------------------------------
    def _get_selected_book_id(self) -> Optional[int]:
        """Return selected book ID from Treeview, or None."""
        selected = self.tree.selection()
        if not selected:
            return None

        values = self.tree.item(selected[0], "values")
        return int(values[0])

    def _add_book(self) -> None:
        """Call BookController.add_book using form input."""
        result = self.controller.add_book(
            title=self.title_var.get(),
            author=self.author_var.get(),
            isbn=self.isbn_var.get(),
            publisher=self.publisher_var.get(),
            category=self.category_var.get(),
            publication_year=self.year_var.get(),
            copies_total=int(self.copies_var.get()),
        )

        if result.success:
            messagebox.showinfo("Success", result.message)
            self._load_books()
        else:
            messagebox.showerror("Error Adding Book", result.message)

    def _update_book(self) -> None:
        """Update the selected book record."""
        book_id = self._get_selected_book_id()
        if book_id is None:
            messagebox.showwarning("No Selection", "Please select a book to update.")
            return

        result = self.controller.update_book(
            book_id=book_id,
            title=self.title_var.get(),
            author=self.author_var.get(),
            isbn=self.isbn_var.get(),
            publisher=self.publisher_var.get(),
            category=self.category_var.get(),
            publication_year=self.year_var.get(),
            copies_total=int(self.copies_var.get()),
        )

        if result.success:
            messagebox.showinfo("Success", result.message)
            self._load_books()
        else:
            messagebox.showerror("Update Error", result.message)

    def _delete_book(self) -> None:
        """Delete the selected book record."""
        book_id = self._get_selected_book_id()
        if book_id is None:
            messagebox.showwarning("No Selection", "Please select a book to delete.")
            return

        if not messagebox.askyesno("Confirm Delete", "Delete this book permanently?"):
            return

        result = self.controller.delete_book(book_id)
        if result.success:
            messagebox.showinfo("Success", result.message)
            self._load_books()
        else:
            messagebox.showerror("Delete Error", result.message)
