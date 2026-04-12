from __future__ import annotations

from typing import Sequence

from PySide6.QtWidgets import QApplication

from src.gui.main_window_clean import MainWindow


def start_gui(argv: Sequence[str] | None = None) -> int:
    qt_argv = ["docx-gui"]
    if argv:
        qt_argv.extend(list(argv))
    app = QApplication(qt_argv)
    window = MainWindow()
    window.show()
    return app.exec()
