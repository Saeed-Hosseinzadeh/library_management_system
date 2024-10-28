import tkinter as tk
from tkinter import messagebox, ttk

from library_app.controllers.member_controller import MemberController


class MemberView(ttk.Frame):
    """Member management frame."""

    def __init__(self, master, controller: MemberController):
        super().__init__(master, padding=12)
        self.controller = controller
        self.selected_member_id = None

        self.member_id_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.national_id_var = tk.StringVar()
        self.address_var = tk.StringVar()
        self.search_var = tk.StringVar()

        self._build_layout()
        self.refresh_members()

    def _build_layout(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        search_frame = ttk.Frame(self)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Search").grid(row=0, column=0, padx=(0, 8))
        ttk.Entry(search_frame, textvariable=self.search_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(search_frame, text="Find", command=self.search_members).grid(row=0, column=2, padx=6)
        ttk.Button(search_frame, text="Refresh", command=self.refresh_members).grid(row=0, column=3)

        body = ttk.Frame(self)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=3)
        body.columnconfigure(2, weight=2)
        body.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            body,
            columns=("id", "member_id", "name", "phone", "national_id", "address"),
            show="headings",
            height=18,
        )
        headings = {
            "id": "ID",
            "member_id": "Member ID",
            "name": "Name",
            "phone": "Phone",
            "national_id": "National ID",
            "address": "Address",
        }
        widths = {
            "id": 60,
            "member_id": 110,
            "name": 170,
            "phone": 120,
            "national_id": 120,
            "address": 220,
        }
        for key, text in headings.items():
            self.tree.heading(key, text=text)
            self.tree.column(key, width=widths[key], anchor="center")

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        y_scroll = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=y_scroll.set)

        form = ttk.LabelFrame(body, text="Member Details", padding=12)
        form.grid(row=0, column=2, sticky="nsew", padx=(12, 0))
        form.columnconfigure(1, weight=1)

        fields = [
            ("Member ID", self.member_id_var),
            ("Name", self.name_var),
            ("Phone", self.phone_var),
            ("National ID", self.national_id_var),
            ("Address", self.address_var),
        ]

        for row_index, (label, variable) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=row_index, column=0, sticky="w", pady=4, padx=(0, 8))
            ttk.Entry(form, textvariable=variable).grid(row=row_index, column=1, sticky="ew", pady=4)

        actions = ttk.Frame(form)
        actions.grid(row=len(fields), column=0, columnspan=2, sticky="ew", pady=(12, 0))
        actions.columnconfigure((0, 1), weight=1)

        ttk.Button(actions, text="Add", command=self.add_member).grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(actions, text="Update", command=self.update_member).grid(row=0, column=1, sticky="ew", padx=(4, 0))
        ttk.Button(actions, text="Remove", command=self.remove_member).grid(row=1, column=0, sticky="ew", padx=(0, 4), pady=(8, 0))
        ttk.Button(actions, text="Clear", command=self.clear_form).grid(row=1, column=1, sticky="ew", padx=(4, 0), pady=(8, 0))

    def _collect_payload(self) -> dict:
        return {
            "member_id": self.member_id_var.get(),
            "name": self.name_var.get(),
            "phone": self.phone_var.get().strip() or None,
            "national_id": self.national_id_var.get().strip() or None,
            "address": self.address_var.get().strip() or None,
        }

    def _show_error(self, result):
        messagebox.showerror("Error", result.message or "Operation failed.")

    def refresh_members(self):
        result = self.controller.list_members()
        if not result.success:
            self._show_error(result)
            return
        self._load_members(result.data or [])

    def search_members(self):
        query = self.search_var.get().strip()
        if not query:
            self.refresh_members()
            return
        result = self.controller.search_members(query)
        if not result.success:
            self._show_error(result)
            return
        self._load_members(result.data or [])

    def _load_members(self, members):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for member in members:
            self.tree.insert(
                "",
                "end",
                iid=str(member.id),
                values=(
                    member.id,
                    member.member_id,
                    member.name,
                    member.phone or "",
                    member.national_id or "",
                    member.address or "",
                ),
            )

    def on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return

        item_id = selection[0]
        values = self.tree.item(item_id, "values")
        self.selected_member_id = int(values[0])

        self.member_id_var.set(values[1])
        self.name_var.set(values[2])
        self.phone_var.set(values[3])
        self.national_id_var.set(values[4])
        self.address_var.set(values[5])

    def add_member(self):
        try:
            payload = self._collect_payload()
            result = self.controller.add_member(**payload)
            if not result.success:
                self._show_error(result)
                return
            self.clear_form()
            self.refresh_members()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def update_member(self):
        if self.selected_member_id is None:
            messagebox.showerror("Error", "Select a member first.")
            return

        try:
            payload = self._collect_payload()
            result = self.controller.update_member(self.selected_member_id, **payload)
            if not result.success:
                self._show_error(result)
                return
            self.clear_form()
            self.refresh_members()
        except Exception as exc:
            messagebox.showerror("Error", str(exc))

    def remove_member(self):
        if self.selected_member_id is None:
            messagebox.showerror("Error", "Select a member first.")
            return

        if not messagebox.askyesno("Confirm", "Remove selected member?"):
            return

        result = self.controller.remove_member(self.selected_member_id)
        if not result.success:
            self._show_error(result)
            return

        self.clear_form()
        self.refresh_members()

    def clear_form(self):
        self.selected_member_id = None
        self.member_id_var.set("")
        self.name_var.set("")
        self.phone_var.set("")
        self.national_id_var.set("")
        self.address_var.set("")
        self.tree.selection_remove(self.tree.selection())
