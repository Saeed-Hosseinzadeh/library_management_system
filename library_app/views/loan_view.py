"""
Loan circulation management view.

Provides interfaces to:
- Issue new loans (with search dropdowns/selectors for books & members).
- View lists of currently active/outstanding loans.
- Settle and return borrowed items.
"""

from __future__ import annotations

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk
from typing import Dict, Optional

from library_app.controllers.loan_controller import LoanController
from library_app.controllers.book_controller import BookController
from library_app.controllers.member_controller import MemberController


class LoanView(ttk.Frame):
    """UI Panel coordinating borrowing rules and returns transactions."""

    def __init__(
        self,
        parent: tk.Widget,
        loan_controller: LoanController,
        book_controller: BookController,
        member_controller: MemberController,
    ) -> None:
        """Initialize circulation components.

        Args:
            parent: Parent frame component.
            loan_controller: Loan operations coordinator.
            book_controller: Source for book lookup lists.
            member_controller: Source for member lookup lists.
        """
        super().__init__(parent)
        self.loan_controller = loan_controller
        self.book_controller = book_controller
        self.member_controller = member_controller

        # Storage mapping display strings to primary key IDs
        self._book_map: Dict[str, int] = {}
        self._member_map: Dict[str, int] = {}

        self.loan_period_var = tk.StringVar(value="14")

        self._build_layout()
        self._refresh_combobox_data()
        self._load_active_loans()

    def _build_layout(self) -> None:
        """Construct the circulation view layout."""
        # Top Checkout Section
        checkout_frame = ttk.LabelFrame(self, text="New Loan Checkout Desk", padding=10)
        checkout_frame.pack(fill=tk.X, pady=5)

        ttk.Label(checkout_frame, text="Select Book:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.book_combo = ttk.Combobox(checkout_frame, state="readonly", width=40)
        self.book_combo.grid(row=0, column=1, sticky=tk.EW, padx=5)

        ttk.Label(checkout_frame, text="Select Member:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.member_combo = ttk.Combobox(checkout_frame, state="readonly", width=40)
        self.member_combo.grid(row=0, column=3, sticky=tk.EW, padx=5)

        ttk.Label(checkout_frame, text="Period (Days):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(checkout_frame, textvariable=self.loan_period_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5)

        checkout_btn = ttk.Button(checkout_frame, text="Issue Loan Checkout", command=self._issue_loan)
        checkout_btn.grid(row=1, column=3, sticky=tk.E, padx=5)

        for col in (1, 3):
            checkout_frame.columnconfigure(col, weight=1)

        # Bottom Grid (Active Loans)
        table_frame = ttk.LabelFrame(self, text="Active Outstanding Loans", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("loan_id", "book_title", "member_name", "loan_date", "due_date"),
            show="headings",
        )

        for col in ("loan_id", "book_title", "member_name", "loan_date", "due_date"):
            self.tree.heading(col, text=col.replace("_", " ").upper())
            self.tree.column(col, width=150, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Scrollbar for table
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)

        # Action Buttons
        actions_frame = ttk.Frame(self)
        actions_frame.pack(fill=tk.X, pady=5)

        ttk.Button(actions_frame, text="Process Book Return", command=self._return_loan).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Refresh Database Records", command=self._refresh_all).pack(side=tk.LEFT)

    def _refresh_combobox_data(self) -> None:
        """Re-read active records from books/members controllers to populate select fields."""
        # Book list
        book_res = self.book_controller.get_all_books()
        if book_res.success and book_res.data:
            # Only list books that have copies available to borrow
            books = [b for b in book_res.data if (b.copies_total - len([l for l in b.loans if l.return_date is None])) > 0]
            self._book_map = {f"{b.title} (ISBN: {b.isbn})": b.id for b in books}
            self.book_combo["values"] = list(self._book_map.keys())
        else:
            self.book_combo["values"] = []

        # Member list
        member_res = self.member_controller.get_all_members()
        if member_res.success and member_res.data:
            self._member_map = {f"{m.name} [ID: {m.member_id}]": m.id for m in member_res.data}
            self.member_combo["values"] = list(self._member_map.keys())
        else:
            self.member_combo["values"] = []

    def _load_active_loans(self) -> None:
        """Load outstanding transactions list."""
        self.tree.delete(*self.tree.get_children())
        result = self.loan_controller.get_active_loans()

        if not result.success:
            messagebox.showerror("Transactions Error", result.message)
            return

        for loan in result.data or []:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    loan.id,
                    loan.book.title,
                    loan.member.name,
                    loan.loan_date.strftime("%Y-%m-%d") if loan.loan_date else "",
                    loan.due_date.strftime("%Y-%m-%d") if loan.due_date else "",
                ),
            )

    def _issue_loan(self) -> None:
        """Coordinate loan validation and processing."""
        selected_book_str = self.book_combo.get()
        selected_member_str = self.member_combo.get()

        if not selected_book_str or not selected_member_str:
            messagebox.showwarning("Incomplete Fields", "Please select both a book and a member.")
            return

        book_id = self._book_map[selected_book_str]
        member_id = self._member_map[selected_member_str]

        try:
            days = int(self.loan_period_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Loan period must be an integer duration.")
            return

        result = self.loan_controller.borrow_book(
            book_id=book_id,
            member_id=member_id,
            loan_period_days=days,
        )

        if result.success:
            messagebox.showinfo("Checkout Complete", result.message)
            self._refresh_all()
        else:
            messagebox.showerror("Checkout Refused", result.message)

    def _return_loan(self) -> None:
        """Settle returning parameters."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Transaction", "Please select a loan record to return.")
            return

        values = self.tree.item(selected[0], "values")
        loan_id = int(values[0])

        result = self.loan_controller.return_book(loan_id=loan_id, return_date=date.today())

        if result.success:
            messagebox.showinfo("Return Succeeded", result.message)
            self._refresh_all()
        else:
            messagebox.showerror("Return Rejected", result.message)

    def _refresh_all(self) -> None:
        """Helper sequence refreshing lists and combo catalogs."""
        self._refresh_combobox_data()
        self._load_active_loans()
        # Reset current selection dropdown display values
        self.book_combo.set("")
        self.member_combo.set("")
