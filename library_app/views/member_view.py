"""
Member management view.

Provides:
- Table grid (Treeview) listing all registered library members.
- Search interface filtering members by name or ID.
- Registration and profiling form for member details.
- Buttons interacting with MemberController using ControllerResult.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from library_app.controllers.member_controller import MemberController
from library_app.db.models import Member


class MemberView(ttk.Frame):
    """UI panel for library member management operations."""

    def __init__(self, parent: tk.Widget, controller: MemberController) -> None:
        """Initialize the member view.

        Args:
            parent: Parent Tk widget or frame.
            controller: MemberController instance injected from AppController.
        """
        super().__init__(parent)
        self.controller = controller

        # Form variables
        self.name_var = tk.StringVar()
        self.member_id_var = tk.StringVar()
        self.phone_var = tk.StringVar()
        self.address_var = tk.StringVar()

        self.search_var = tk.StringVar()

        self._build_layout()
        self._load_members()

    def _build_layout(self) -> None:
        """Build the member view layout hierarchy."""
        # ==================================================================
        # Search Component
        # ==================================================================
        search_frame = ttk.Frame(self)
        search_frame.pack(fill=tk.X, pady=5)

        ttk.Label(search_frame, text="Search Members:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(search_frame, text="Search", command=self._search_members).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Reset", command=self._load_members).pack(side=tk.LEFT)

        # ==================================================================
        # Members Grid
        # ==================================================================
        self.tree = ttk.Treeview(
            self,
            columns=("db_id", "member_id", "name", "phone", "address"),
            show="headings",
            height=12,
        )

        for col in ("db_id", "member_id", "name", "phone", "address"):
            self.tree.heading(col, text=col.replace("_", " ").upper())
            self.tree.column(col, width=150, anchor=tk.CENTER)

        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # ==================================================================
        # Data Entry Form
        # ==================================================================
        form_frame = ttk.LabelFrame(self, text="Member Details", padding=10)
        form_frame.pack(fill=tk.X, pady=10)

        # Form grid layout
        ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.name_var).grid(row=0, column=1, sticky=tk.EW, padx=5)

        ttk.Label(form_frame, text="Library Card ID:").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(form_frame, textvariable=self.member_id_var).grid(row=0, column=3, sticky=tk.EW, padx=5)

        ttk.Label(form_frame, text="Phone:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Entry(form_frame, textvariable=self.phone_var).grid(row=1, column=1, sticky=tk.EW, padx=5)

        ttk.Label(form_frame, text="Address:").grid(row=1, column=2, sticky=tk.W, padx=5)
        ttk.Entry(form_frame, textvariable=self.address_var).grid(row=1, column=3, sticky=tk.EW, padx=5)

        for i in range(4):
            form_frame.columnconfigure(i, weight=1)

        # ==================================================================
        # Operations Buttons
        # ==================================================================
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text="Register Member", command=self._register_member).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Update Selected", command=self._update_member).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Selected", command=self._delete_member).pack(side=tk.LEFT, padx=5)

    def _load_members(self) -> None:
        """Load all members from controller into the table."""
        self.tree.delete(*self.tree.get_children())
        result = self.controller.get_all_members()

        if not result.success:
            messagebox.showerror("Error Loading Members", result.message)
            return

        for member in result.data or []:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    member.id,
                    member.member_id,
                    member.name,
                    member.phone or "",
                    member.address or "",
                ),
            )

    def _search_members(self) -> None:
        """Query and filter list view."""
        query = self.search_var.get().strip()
        result = self.controller.search_members(query)

        self.tree.delete(*self.tree.get_children())
        if not result.success:
            messagebox.showerror("Search Error", result.message)
            return

        for member in result.data or []:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    member.id,
                    member.member_id,
                    member.name,
                    member.phone or "",
                    member.address or "",
                ),
            )

    def _on_tree_select(self, event: tk.Event) -> None:
        """Populate the details form when a table row is chosen."""
        selected = self.tree.selection()
        if not selected:
            return

        values = self.tree.item(selected[0], "values")
        _, member_id, name, phone, address = values

        self.name_var.set(name)
        self.member_id_var.set(member_id)
        self.phone_var.set(phone)
        self.address_var.set(address)

    def _get_selected_db_id(self) -> Optional[int]:
        """Return the database primary key for the selected member row."""
        selected = self.tree.selection()
        if not selected:
            return None
        values = self.tree.item(selected[0], "values")
        return int(values[0])

    def _register_member(self) -> None:
        """Submit enrollment input to the member service."""
        result = self.controller.register_member(
            name=self.name_var.get(),
            member_id=self.member_id_var.get(),
            phone=self.phone_var.get(),
            address=self.address_var.get(),
        )

        if result.success:
            messagebox.showinfo("Success", result.message)
            self._load_members()
        else:
            messagebox.showerror("Registration Error", result.message)

    def _update_member(self) -> None:
        """Modify profiling attributes of the chosen member."""
        db_id = self._get_selected_db_id()
        if db_id is None:
            messagebox.showwarning("No Selection", "Please select a member to update.")
            return

        result = self.controller.update_member(
            member_db_id=db_id,
            name=self.name_var.get(),
            phone=self.phone_var.get(),
            address=self.address_var.get(),
        )

        if result.success:
            messagebox.showinfo("Success", result.message)
            self._load_members()
        else:
            messagebox.showerror("Update Error", result.message)

    def _delete_member(self) -> None:
        """Delete member database entry."""
        db_id = self._get_selected_db_id()
        if db_id is None:
            messagebox.showwarning("No Selection", "Please select a member to deregister.")
            return

        if not messagebox.askyesno("Confirm Delete", "Remove this member catalog entry?"):
            return

        result = self.controller.delete_member(db_id)
        if result.success:
            messagebox.showinfo("Success", result.message)
            self._load_members()
        else:
            messagebox.showerror("Deletion Error", result.message)
