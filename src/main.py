import sys
import os
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QProxyStyle, QStyle, QStyleOption
from PyQt6.QtGui import QFont, QFontDatabase, QIcon, QPalette, QColor
from PyQt6.QtCore import Qt
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
    magnolia_path = os.path.join(base_path, "assets", "fonts", "magnolia", "magnolia.ttf")
    fonts['magnolia'] = load_font('Magnolia', magnolia_path)
    
    # Load Playfair Display
    playfair_path = os.path.join(base_path, "assets", "fonts", "playfair-display", "PlayfairDisplay.ttf")
    fonts['playfair'] = load_font('Playfair Display', playfair_path)
    
    # Load Inter
    inter_path = os.path.join(base_path, "assets", "fonts", "inter", "Inter.ttf")
    fonts['inter'] = load_font('Inter', inter_path)
    
    return fonts


APP_STYLESHEET = """
QMainWindow {
    background-color: #FFF8F5;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QMenuBar {
    background-color: #FFFFFF;
    border-bottom: 1px solid #F0E6E8;
    padding: 4px 8px;
    font-size: 13px;
    color: #2E2B2B;
    font-family: 'Playfair Display', serif;
}
QMenuBar::item {
    padding: 6px 12px;
    border-radius: 8px;
    margin: 2px 1px;
}
QMenuBar::item:selected {
    background-color: #F7D1DC;
    color: #2E2B2B;
}
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #F0E6E8;
    border-radius: 12px;
    padding: 6px;
    font-family: 'Playfair Display', serif;
}
QMenu::item {
    padding: 8px 28px;
    border-radius: 8px;
    color: #2E2B2B;
    font-size: 13px;
}
QMenu::item:selected {
    background-color: #FFF0F3;
    color: #2E2B2B;
}
QMenu::separator {
    height: 1px;
    background: #F0E6E8;
    margin: 4px 12px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QFrame {
    border-radius: 8px;
}
QTextEdit, QLineEdit, QTextBrowser {
    border: 1px solid #F0E6E8;
    border-radius: 10px;
    padding: 8px;
    background: #FFFFFF;
    font-size: 14px;
    color: #2E2B2B;
    selection-background-color: #F7D1DC;
    selection-color: #2E2B2B;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QTextEdit:focus, QLineEdit:focus {
    border-color: #CFA6D6;
}
QLineEdit {
    padding: 8px 12px;
}
QPushButton {
    padding: 8px 16px;
    border: none;
    border-radius: 20px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #FFF8F5);
    font-size: 12px;
    font-weight: 500;
    color: #2E2B2B;
    min-height: 20px;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF0F3, stop:1 #F7D1DC);
    border: 1px solid #F7D1DC;
}
QPushButton:pressed {
    background: #F7D1DC;
    border: 1px solid #CFA6D6;
}
QToolButton {
    border: none;
    border-radius: 10px;
    padding: 4px 8px;
    font-size: 13px;
    color: #6B6770;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QToolButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF0F3, stop:1 #F7D1DC);
    color: #2E2B2B;
}
QToolButton:checked {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F3E8F6, stop:1 #E8DDE0);
    border: 1px solid #CFA6D6;
    color: #2E2B2B;
}
QSplitter::handle {
    background: #E8DDE0;
    width: 4px;
    margin: 20px 0px;
    border-radius: 2px;
}
QSplitter::handle:hover {
    background: #CFA6D6;
}
QSplitter::handle:pressed {
    background: #B894C0;
}
QTreeWidget {
    background: #FFFFFF;
    border: none;
    font-size: 13px;
    color: #2E2B2B;
    outline: none;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QTreeWidget::item {
    padding: 6px 4px;
    border-radius: 8px;
    margin: 1px 4px;
}
QTreeWidget::item:selected {
    background-color: #F3E8F6;
    color: #2E2B2B;
}
QTreeWidget::item:hover {
    background-color: #FFF0F3;
}
QCheckBox {
    spacing: 8px;
    font-size: 13px;
    color: #2E2B2B;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 2px solid #E0D6D8;
    background: #FFFFFF;
}
QCheckBox::indicator:checked {
    background: #7DC68E;
    border-color: #7DC68E;
}
QCheckBox::indicator:hover {
    border-color: #CFA6D6;
}
QComboBox {
    padding: 6px 12px;
    border: 1px solid #F0E6E8;
    border-radius: 10px;
    background: #FFFFFF;
    font-size: 12px;
    color: #2E2B2B;
    min-height: 20px;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QComboBox:hover {
    border-color: #CFA6D6;
}
QComboBox:focus {
    border-color: #CFA6D6;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background: #FFFFFF;
    border: 1px solid #F0E6E8;
    border-radius: 10px;
    selection-background-color: #FFF0F3;
    selection-color: #2E2B2B;
    outline: none;
    padding: 4px;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QCalendarWidget {
    background: #FFFFFF;
    border: 1px solid #F0E6E8;
    border-radius: 12px;
    font-family: 'Inter', 'Poppins', sans-serif;
    font-size: 11px;
}
QCalendarWidget QToolButton {
    color: #2E2B2B;
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 12px;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QCalendarWidget QToolButton:hover {
    background: #FFF0F3;
}
QCalendarWidget QToolButton:pressed {
    background: #F7D1DC;
}
QCalendarWidget QToolButton#qt_calendar_prevmonth,
QCalendarWidget QToolButton#qt_calendar_nextmonth {
    qproperty-icon: none;
    min-width: 24px;
    font-size: 12px;
    color: #CFA6D6;
}
QCalendarWidget QToolButton#qt_calendar_prevmonth {
    qproperty-text: "<";
}
QCalendarWidget QToolButton#qt_calendar_nextmonth {
    qproperty-text: ">";
}
QCalendarWidget QToolButton#qt_calendar_prevmonth:hover,
QCalendarWidget QToolButton#qt_calendar_nextmonth:hover {
    color: #2E2B2B;
    background: #FFF0F3;
}
QCalendarWidget QToolButton#qt_calendar_monthbutton,
QCalendarWidget QToolButton#qt_calendar_yearbutton {
    font-size: 12px;
    font-weight: 600;
    min-width: 70px;
    color: #2E2B2B;
}
QCalendarWidget QToolButton#qt_calendar_monthbutton:hover,
QCalendarWidget QToolButton#qt_calendar_yearbutton:hover {
    background: #FFF0F3;
}
QCalendarWidget QToolButton#qt_calendar_monthbutton:pressed,
QCalendarWidget QToolButton#qt_calendar_yearbutton:pressed {
    background: #F7D1DC;
}
QCalendarWidget QWidget#qt_calendar_calendarview {
    background: #FFFFFF;
    border: none;
}
QCalendarWidget QAbstractItemView:enabled {
    color: #2E2B2B;
    background: #FFFFFF;
    selection-background-color: #CFA6D6;
    selection-color: #FFFFFF;
    font-family: 'Inter', 'Poppins', sans-serif;
    font-size: 11px;
    gridline-color: transparent;
}
QCalendarWidget QAbstractItemView:disabled {
    color: #D1D5DB;
}
QCalendarWidget QAbstractItemView:focus {
    outline: none;
}
QCalendarWidget QTableView {
    selection-background-color: #CFA6D6;
    selection-color: #FFFFFF;
}
QCalendarWidget QTableView QHeaderView::section {
    background: #FFF8F5;
    color: #6B6770;
    border: none;
    border-bottom: 1px solid #F0E6E8;
    padding: 3px;
    font-size: 10px;
    font-weight: 600;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background: #FFF8F5;
    border-top: 1px solid #F0E6E8;
    border-radius: 0 0 12px 12px;
    padding: 3px;
}
QCalendarWidget QCalendarDayWidget {
    padding: 1px;
}
QCalendarWidget QToolButton#qt_calendar_calendarbutton {
    qproperty-icon: none;
    min-width: 20px;
    font-size: 11px;
    color: #CFA6D6;
}
QCalendarWidget QToolButton#qt_calendar_calendarbutton:hover {
    background: #FFF0F3;
    color: #2E2B2B;
}
QScrollBar:vertical {
    width: 8px;
    background: transparent;
    margin: 8px 0px;
}
QScrollBar::handle:vertical {
    background: #E8DDE0;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #CFA6D6;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
QScrollBar:horizontal {
    height: 8px;
    background: transparent;
}
QScrollBar::handle:horizontal {
    background: #E8DDE0;
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #CFA6D6;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
}
QSpinBox {
    padding: 6px 12px;
    border: 1px solid #F0E6E8;
    border-radius: 10px;
    background: #FFFFFF;
    font-size: 13px;
    color: #2E2B2B;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QSpinBox:focus {
    border-color: #CFA6D6;
}
QDateEdit {
    padding: 6px 12px;
    border: 1px solid #F0E6E8;
    border-radius: 10px;
    background: #FFFFFF;
    font-size: 13px;
    color: #2E2B2B;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QDateEdit:focus {
    border-color: #CFA6D6;
}
QDateEdit::drop-down {
    border: none;
    width: 28px;
}
QLabel {
    color: #2E2B2B;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QLabel#page_title {
    font-family: 'Playfair Display', serif;
    font-size: 18px;
    font-weight: 600;
}
QLabel#welcome_title {
    font-family: 'Magnolia', cursive;
    font-size: 32px;
}
QToolTip {
    background-color: #FFFFFF;
    border: 1px solid #F0E6E8;
    border-radius: 8px;
    color: #2E2B2B;
    padding: 6px 10px;
    font-size: 12px;
    font-family: 'Inter', 'Poppins', sans-serif;
    font-weight: 400;
}
QToolTip QLabel {
    background-color: #FFFFFF;
    color: #2E2B2B;
    font-family: 'Inter', 'Poppins', sans-serif;
    font-size: 12px;
}
QDialog {
    background: #FFF8F5;
    font-family: 'Inter', 'Poppins', sans-serif;
}
QDialogButtonBox QPushButton {
    min-width: 80px;
}
QMessageBox {
    background: #FFF8F5;
    font-family: 'Inter', 'Poppins', sans-serif;
}
"""


def _excepthook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    try:
        app = QApplication.instance()
        if app:
            msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton
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
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("com.productivity.app")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Personal Productivity App")
    app.setStyle(TooltipStyle(app.style()))

    # Set app icon for taskbar
    logo_ico = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "logo_icon.ico")
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
