"""
Application entry point.

Initializes database structures, constructs execution controllers,
configures logging parameters, and boots up the primary graphical UI interface.
"""

from __future__ import annotations

import logging
import sys
from library_app.config.settings import get_settings
from library_app.controllers.app_controller import AppController
from library_app.db.session import engine
from library_app.db.models import Base
from library_app.views.main_window import MainWindow

# Configure logging output format to stream to console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger("library_app")


def bootstrap_application() -> None:
    """Pre-initialize database storage parameters and launch the interface."""
    logger.info("Starting Library Management System database engine setup...")

    # Bind metadata models and verify local Sqlite structure migrations
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas validated and initialized.")
    except Exception as e:
        logger.critical(f"Critical error mapping database migrations: {e}")
        sys.exit(1)

    # Initialize Core Application layer controllers
    logger.info("Starting systems and loading application coordinator...")
    app_controller = AppController()

    # Launch GUI Event Loop
    logger.info("Booting client visual framework...")
    main_window = MainWindow(app_controller)
    main_window.run()


if __name__ == "__main__":
    bootstrap_application()
