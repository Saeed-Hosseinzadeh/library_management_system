import tkinter as tk
from tkinter import messagebox, ttk

from library_app.controllers.loan_controller import LoanController


class LoanView(ttk.Frame):
    """Loan management frame."""

    def __init__(self, master, controller: LoanController):
        super().__init__(master, padding=12)
        self.controller = controller
        self.selected_loan_id = None

        self.member_identifier_var = tk.StringVar()
        self.isbn_var = tk.StringVar()

        self._build_layout()
        self.refresh_loans()

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        form = ttk.LabelFrame(self, text="Issue Loan", padding=12)
        form.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        ttk.Label(form, text="Member ID").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(form, textvariable=self.member_identifier_var).grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="ISBN").grid(row=0, column=2, sticky="w", padx=(12, 8), pady=4)
        ttk.Entry(form, textvariable=self.isbn_var).grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Button(form, text="Issue Loan", command=self.issue_loan).grid(row=0, column=4, padx=(12, 0))
        ttk.Button(form, text="Refresh", command=self.refresh_loans).grid(row=0, column=5, padx=(6, 0))

        table_frame = ttk.Frame(self)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            table_frame,
            columns=("id", "member", "book", "isbn", "loan_date"),
            show="headings",
            height=18,
        )
        headings = {
            "id": "Loan ID",
            "member": "Member",
            "book": "Book",
            "isbn": "ISBN",
            "loan_date": "Loan Date",
        }
        widths = {
            "id": 80,
            "member": 180,
            "book": 220,
            "isbn": 130,
            "loan_date": 120,
        }
        for key, text in headings.items():
            self.tree.heading(key, text=text)
            self.tree.column(key, width=widths[key], anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=y_scroll.set)

        action_frame = ttk.Frame(self)
        action_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        ttk.Button(action_frame, text="Terminate Selected Loan", command=self.terminate_loan).pack(side="left")

    def _show_error(self, result):
        messagebox.showerror("Error", result.message or "Operation failed.")

    def refresh_loans(self):
        result = self.controller.get_active_loans()
        if not result.success:
            self._show_error(result)
            return
        self._load_loans(result.data or [])

    def _load_loans(self, loans):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for loan in loans:
            member_label = getattr(loan.member, "name", "") if getattr(loan, "member", None) else ""
            if getattr(loan, "member", None) and getattr(loan.member, "member_id", None):
                member_label = f"{loan.member.name} ({loan.member.member_id})"

            book_label = getattr(loan.book, "title", "") if getattr(loan, "book", None) else ""
            isbn = getattr(loan.book, "isbn", "") if getattr(loan, "book", None) else ""

            self.tree.insert(
                "",
                "end",
                iid=str(loan.id),
                values=(
                    loan.id,
                    member_label,
                    book_label,
                    isbn,
                    str(loan.loan_date),
                ),
            )

    def on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        self.selected_loan_id = int(selection[0])

    def issue_loan(self):
        member_identifier = self.member_identifier_var.get().strip()
        isbn = self.isbn_var.get().strip()

        result = self.controller.issue_loan(member_identifier, isbn)
        if not result.success:
            self._show_error(result)
            return

        self.member_identifier_var.set("")
        self.isbn_var.set("")
        self.refresh_loans()

    def terminate_loan(self):
        if self.selected_loan_id is None:
            messagebox.showerror("Error", "Select a loan first.")
            return

        if not messagebox.askyesno("Confirm", "Terminate selected loan?"):
            return

        result = self.controller.terminate_loan(self.selected_loan_id)
        if not result.success:
            self._show_error(result)
            return

        self.selected_loan_id = None
        self.refresh_loans()
