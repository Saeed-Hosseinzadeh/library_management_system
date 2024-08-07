"""
Main application window (Tkinter).

Provides the core layout structure with:
- A left navigation sidebar.
- A dynamic right-hand content area for loading sub-views.

The window binds application controllers to UI panels without exposing
any backend or database internals to the UI layer.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional

from library_app.controllers.app_controller import AppController
from library_app.views.book_view import BookView


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
        self.root.geometry("1100x650")
        self.root.minsize(1024, 600)

        # Main layout frames
        self.sidebar_frame = ttk.Frame(self.root, padding=10)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.content_frame = ttk.Frame(self.root, padding=10)
        self.content_frame.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Currently active view
        self.active_view: Optional[tk.Frame] = None

        self._build_sidebar()

    def _build_sidebar(self) -> None:
        """Construct the left-side navigation menu."""
        ttk.Label(
            self.sidebar_frame,
            text="Library Dashboard",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=10)

        # Buttons
        ttk.Button(
            self.sidebar_frame,
            text="Books",
            command=self.show_books_view
        ).pack(fill=tk.X, pady=5)

        ttk.Button(
            self.sidebar_frame,
            text="Members",
            command=self._placeholder_members_view
        ).pack(fill=tk.X, pady=5)

        ttk.Button(
            self.sidebar_frame,
            text="Loans",
            command=self._placeholder_loans_view
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

    def _placeholder_members_view(self) -> None:
        """Temporary placeholder until MemberView is implemented."""
        self._clear_content()
        placeholder = ttk.Label(self.content_frame, text="Members panel under construction...")
        placeholder.pack(expand=True)
        self.active_view = placeholder

    def _placeholder_loans_view(self) -> None:
        """Temporary placeholder until LoanView is implemented."""
        self._clear_content()
        placeholder = ttk.Label(self.content_frame, text="Loans panel under construction...")
        placeholder.pack(expand=True)
        self.active_view = placeholder

    def run(self) -> None:
        """Start the Tkinter main event loop."""
        self.root.mainloop()
