import os
import sys
import traceback

from PyQt6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPalette
from PyQt6.QtWidgets import QApplication, QProxyStyle, QStyle

from src.styles import APP_STYLESHEET
from src.ui.main_window import MainWindow


class TooltipStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QStyle.PrimitiveElement.PE_PanelTipLabel:
            painter.save()
            painter.setRenderHint(painter.RenderHint.Antialiasing)
            painter.setBrush(QColor("#FFFFFF"))
            painter.setPen(QColor("#F0E6E8"))
            painter.drawRoundedRect(option.rect, 8, 8)
            painter.restore()
            return
        super().drawPrimitive(element, option, painter, widget)


def load_font(font_name, font_path):
    """Load a font from the assets folder."""
    if os.path.exists(font_path):
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id >= 0:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                return font_families[0]
    return None


def load_all_fonts():
    """Load all custom fonts from assets folder."""
    base_path = os.path.dirname(os.path.dirname(__file__))
    fonts = {}

    # Load Magnolia
    magnolia_path = os.path.join(
        base_path, "assets", "fonts", "magnolia", "magnolia.ttf"
    )
    fonts["magnolia"] = load_font("Magnolia", magnolia_path)

    # Load Playfair Display
    playfair_path = os.path.join(
        base_path, "assets", "fonts", "playfair-display", "PlayfairDisplay.ttf"
    )
    fonts["playfair"] = load_font("Playfair Display", playfair_path)

    # Load Inter
    inter_path = os.path.join(base_path, "assets", "fonts", "inter", "Inter.ttf")
    fonts["inter"] = load_font("Inter", inter_path)

    return fonts


def _excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    try:
        app = QApplication.instance()
        if app:
            msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            from PyQt6.QtWidgets import (
                QDialog,
                QHBoxLayout,
                QPushButton,
                QTextEdit,
                QVBoxLayout,
            )

            dialog = QDialog()
            dialog.setWindowTitle("Unhandled Error")
            dialog.setMinimumSize(600, 400)
            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setPlainText(msg)
            text_edit.setReadOnly(True)
            layout.addWidget(text_edit)
            copy_btn = QPushButton("Copy to Clipboard")

            def copy_to_clipboard():
                text_edit.selectAll()
                text_edit.copy()

            copy_btn.clicked.connect(copy_to_clipboard)
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            btn_layout = QHBoxLayout()
            btn_layout.addWidget(copy_btn)
            btn_layout.addWidget(close_btn)
            layout.addLayout(btn_layout)
            dialog.exec()
    except Exception:
        pass


sys.excepthook = _excepthook


def main():
    # Set AppUserModelID for Windows taskbar icon
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "com.productivity.app"
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Personal Productivity App")
    app.setStyle(TooltipStyle(app.style()))

    # Set app icon for taskbar
    logo_ico = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "logo_icon.ico"
    )
    if os.path.exists(logo_ico):
        app.setWindowIcon(QIcon(logo_ico))

    # Load all custom fonts
    fonts = load_all_fonts()
    for font_name, font_family in fonts.items():
        if font_family:
            print(f"Loaded {font_name} font: {font_family}")

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#2E2B2B"))
    app.setPalette(palette)

    from PyQt6.QtWidgets import QToolTip as _QToolTip

    _QToolTip.setFont(QFont("Inter", 12))
    _QToolTip.setPalette(palette)

    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
