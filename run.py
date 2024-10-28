import logging
import sys
from pathlib import Path

# Add project root to sys.path for absolute imports
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from library_app.controllers.app_controller import AppController
from library_app.db.base import Base, engine
from library_app.views.main_window import MainWindow


def setup_logging():
    """Initialize system logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def main():
    """Application entry point."""
    setup_logging()

    try:
        # Initialize database tables
        Base.metadata.create_all(bind=engine)

        # Initialize controller and view
        app_controller = AppController()
        app = MainWindow(app_controller)
        app.run()
    except Exception as e:
        logging.critical(f"System failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
