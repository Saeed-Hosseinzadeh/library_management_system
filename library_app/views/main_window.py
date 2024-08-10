"""
Main application window (Tkinter).

Provides the core layout structure with:
- A left navigation sidebar.
- A dynamic right-hand content area for loading sub-views.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from library_app.controllers.app_controller import AppController
from library_app.views.book_view import BookView
from library_app.views.member_view import MemberView
from library_app.views.loan_view import LoanView


class MainWindow:
    """Primary Tkinter window containing navigation and dynamic content area."""

    def __init__(self, app_controller: AppController) -> None:
        """Initialize and construct the main window layout.

        Args:
            app_controller: Central application controller coordinating domain services.
        """
        self._app_controller = app_controller

        self.root = tk.Tk()
        self.root.title("Library Management System")
        self.root.geometry("1150x700")
        self.root.minsize(1024, 600)

        # Main layout frames
        self.sidebar_frame = ttk.Frame(self.root, padding=10)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.content_frame = ttk.Frame(self.root, padding=10)
        self.content_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        self.active_view: Optional[tk.Frame] = None

        self._build_sidebar()
        # Default view upon login/start
        self.show_books_view()

    def _build_sidebar(self) -> None:
        """Construct the left-side navigation menu."""
        ttk.Label(
            self.sidebar_frame,
            text="Library Management",
            font=("Segoe UI", 13, "bold"),
        ).pack(pady=15)

        ttk.Button(
            self.sidebar_frame,
            text="Books Catalog",
            command=self.show_books_view,
            width=20
        ).pack(fill=tk.X, pady=5)

        ttk.Button(
            self.sidebar_frame,
            text="Patron Members",
            command=self.show_members_view,
            width=20
        ).pack(fill=tk.X, pady=5)

        ttk.Button(
            self.sidebar_frame,
            text="Loan Operations",
            command=self.show_loans_view,
            width=20
        ).pack(fill=tk.X, pady=5)

    def _clear_content(self) -> None:
        """Remove any currently visible sub-view from the content frame."""
        if self.active_view is not None:
            self.active_view.destroy()
            self.active_view = None

    def show_books_view(self) -> None:
        """Display the book management panel."""
        self._clear_content()
        self.active_view = BookView(
            parent=self.content_frame,
            controller=self._app_controller.books,
        )
        self.active_view.pack(expand=True, fill=tk.BOTH)

    def show_members_view(self) -> None:
        """Display the member management panel."""
        self._clear_content()
        self.active_view = MemberView(
            parent=self.content_frame,
            controller=self._app_controller.members,
        )
        self.active_view.pack(expand=True, fill=tk.BOTH)

    def show_loans_view(self) -> None:
        """Display the active checkout/return console."""
        self._clear_content()
        self.active_view = LoanView(
            parent=self.content_frame,
            loan_controller=self._app_controller.loans,
            book_controller=self._app_controller.books,
            member_controller=self._app_controller.members,
        )
        self.active_view.pack(expand=True, fill=tk.BOTH)

    def run(self) -> None:
        """Start the Tkinter main event loop."""
        self.root.mainloop()
