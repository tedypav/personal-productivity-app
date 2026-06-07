import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QFont
from src.ui.main_window import MainWindow


APP_STYLESHEET = """
QMainWindow {
    background-color: #fafafa;
}
QMenuBar {
    background-color: #f8f9fa;
    border-bottom: 1px solid #dee2e6;
    padding: 2px;
    font-size: 13px;
}
QMenuBar::item:selected {
    background-color: #e0e7ff;
    border-radius: 4px;
}
QMenu {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #e0e7ff;
    color: #1e40af;
}
QScrollArea {
    border: none;
}
QFrame {
    border-radius: 4px;
}
QTextEdit, QLineEdit, QTextBrowser {
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 4px;
    background: #ffffff;
    font-size: 13px;
}
QTextEdit:focus, QLineEdit:focus {
    border-color: #6366f1;
}
QPushButton {
    padding: 4px 10px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    background: #ffffff;
    font-size: 12px;
}
QPushButton:hover {
    background: #f0f0ff;
    border-color: #6366f1;
}
QPushButton:pressed {
    background: #e0e0ff;
}
QToolButton {
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 2px;
    font-size: 13px;
}
QToolButton:hover {
    background: #f0f0ff;
    border-color: #d1d5db;
}
QToolButton:checked {
    background: #e0e7ff;
    border-color: #6366f1;
}
QSplitter::handle {
    background: #dee2e6;
    width: 2px;
}
QTreeWidget {
    background: #ffffff;
    border: none;
    font-size: 13px;
}
QTreeWidget::item {
    padding: 4px 2px;
    border-radius: 4px;
}
QTreeWidget::item:selected {
    background-color: #e0e7ff;
    color: #1e40af;
}
QTreeWidget::item:hover {
    background-color: #f3f4f6;
}
QCheckBox {
    spacing: 6px;
    font-size: 13px;
}
QComboBox {
    padding: 2px 8px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    background: #ffffff;
    font-size: 12px;
}
QComboBox:hover {
    border-color: #6366f1;
}
QScrollBar:vertical {
    width: 8px;
    background: transparent;
}
QScrollBar::handle:vertical {
    background: #d1d5db;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #9ca3af;
}
"""


def _excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    try:
        app = QApplication.instance()
        if app:
            msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            QMessageBox.critical(None, "Unhandled Error", msg)
    except Exception:
        pass

sys.excepthook = _excepthook


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Personal Productivity App")
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
