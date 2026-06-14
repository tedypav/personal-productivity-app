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

/* Sidebar */
#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF8F5, stop:1 #FFF0F5);
}
#sidebarTree {
    background: #FFFFFF;
    border: 1px solid #F7D1DC;
    border-radius: 12px;
    font-size: 13px;
    color: #2E2B2B;
    outline: none;
    padding: 4px;
}
#sidebarTree::item {
    padding: 7px 6px;
    border-radius: 8px;
    margin: 1px 2px;
    color: #2E2B2B;
}
#sidebarTree::item:selected {
    background-color: #F3E8F6;
    color: #2E2B2B;
}
#sidebarTree::item:hover {
    background-color: #FFF0F3;
}
#sidebarBtn {
    padding: 6px 12px;
    border: 1px solid #F7D1DC;
    border-radius: 16px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFFFFF, stop:1 #FFF5F7);
    font-size: 11px;
    font-weight: 500;
    color: #2E2B2B;
}
#sidebarBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #FFF5F7, stop:1 #FFE4EC);
    border: 1px solid #F7AEC4;
}
#sidebarBtn:pressed {
    background: #F7D1DC;
    border: 1px solid #CFA6D6;
}
#sidebarExpandBtn, #sidebarCollapseBtn {
    padding: 4px 10px;
    font-size: 10px;
    border-radius: 14px;
}
#sidebarEmptyHint {
    color: #9CA3AF;
    font-size: 13px;
    padding: 20px;
}
#sidebarSpinBox {
    padding: 6px 12px;
    border: 1px solid #F7D1DC;
    border-radius: 10px;
    background: #FFFFFF;
    font-size: 13px;
    color: #2E2B2B;
    min-width: 120px;
    font-family: 'Inter', 'Poppins', sans-serif;
}
#sidebarSpinBox::up-button, #sidebarSpinBox::down-button {
    border: none;
    width: 22px;
    border-radius: 11px;
    background: #FFF0F3;
}
#sidebarSpinBox::up-button:hover, #sidebarSpinBox::down-button:hover {
    background: #FFE4EC;
}

/* PageEditor */
#pageEditor {
    background: #2a1a35;
}
#editorScroll {
    border: none;
    background: #2a1a35;
}
#welcome_label {
    font-family: 'Magnolia', cursive;
    font-size: 80px;
    color: #F0E4F5;
    background: transparent;
    padding: 40px;
}
#editorEmptyHint {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    color: #9CA3AF;
    font-style: italic;
    background: transparent;
}
#editorAddBtn {
    font-size: 24px;
    font-weight: 300;
    color: #FFFFFF;
    background: #CFA6D6;
    border: none;
    border-radius: 24px;
}
#editorAddBtn:hover {
    background: #B894C0;
}
#editorMenu {
    background: #FFFFFF;
    border: 1px solid #F7D1DC;
    border-radius: 8px;
    padding: 4px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
}
#editorMenu::item {
    padding: 8px 20px;
    border-radius: 6px;
}
#editorMenu::item:selected {
    background: #FFF0F3;
    color: #2E2B2B;
}
#editorToolbar {
    background: #FFF8F5;
    border-bottom: 1px solid #F0E6E8;
}
#editorPageTitle {
    font-size: 18px;
    font-weight: 600;
    padding: 4px 8px;
    color: #2E2B2B;
    font-family: 'Playfair Display', serif;
}
#editorBackBtn {
    font-size: 12px;
    color: #CFA6D6;
    background: transparent;
    border: 1px solid #F0E6E8;
    border-radius: 14px;
    padding: 4px 14px;
    font-family: 'Inter', sans-serif;
}
#editorBackBtn:hover {
    background: #FFF0F3;
    border-color: #CFA6D6;
    color: #9b59b6;
}
#editorChecklistBtn {
    font-size: 12px;
    color: #CFA6D6;
    background: transparent;
    border: 1px solid #F0E6E8;
    border-radius: 14px;
    padding: 4px 14px;
    font-family: 'Inter', sans-serif;
}
#editorChecklistBtn:hover {
    background: #FFF0F3;
    border-color: #CFA6D6;
    color: #9b59b6;
}
#editorTableBtn {
    font-size: 12px;
    color: #CFA6D6;
    background: transparent;
    border: 1px solid #F0E6E8;
    border-radius: 14px;
    padding: 4px 14px;
    font-family: 'Inter', sans-serif;
}
#editorTableBtn:hover {
    background: #FFF0F3;
    border-color: #CFA6D6;
    color: #9b59b6;
}
#editorTocContainer {
    background: transparent;
}
#editorTocLabel {
    font-family: 'Playfair Display', serif;
    font-size: 24px;
    font-weight: 600;
    color: #9b59b6;
    background: transparent;
    padding: 8px 0 16px 0;
}
#editorTocSeparator {
    background: #F0E6E8;
}
#editorTocItem {
    text-align: left;
    font-size: 15px;
    color: #CFA6D6;
    background: transparent;
    border: 1px solid transparent;
    padding: 10px 16px;
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
}
#editorTocItem:hover {
    background: #FFF0F3;
    border-color: #F7D1DC;
    color: #9b59b6;
}

/* Table Widget Buttons */
#tableAddBtn {
    font-size: 10px;
    color: #CFA6D6;
    background: transparent;
    border: 1px solid #F0E6E8;
    border-radius: 10px;
    padding: 2px 8px;
    font-family: 'Inter', sans-serif;
}
#tableAddBtn:hover {
    background: #FFF0F3;
    border-color: #CFA6D6;
    color: #9b59b6;
}
#tableRemoveBtn {
    font-size: 10px;
    color: #9CA3AF;
    background: transparent;
    border: 1px solid #F0E6E8;
    border-radius: 10px;
    padding: 2px 8px;
    font-family: 'Inter', sans-serif;
}
#tableRemoveBtn:hover {
    background: #FFF0F3;
    border-color: #EF4444;
    color: #EF4444;
}
#tableRowNumBtn {
    font-size: 10px;
    color: #9CA3AF;
    background: transparent;
    border: 1px solid #F0E6E8;
    border-radius: 10px;
    padding: 2px 8px;
    font-family: 'Inter', sans-serif;
}
#tableRowNumBtn:hover {
    background: #FFF0F3;
    border-color: #CFA6D6;
    color: #CFA6D6;
}
#tableRowNumBtn:checked {
    background: #F3E8F6;
    border-color: #CFA6D6;
    color: #CFA6D6;
}

/* Fun Imports Dialog */
#funImportsTabs::pane {
    border: none;
}
#funImportsTabBar::tab {
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 500;
    color: #9ca3af;
    border-bottom: 2px solid transparent;
}
#funImportsTabBar::tab:selected {
    color: #CFA6D6;
    border-bottom: 2px solid #CFA6D6;
}
#funImportsTabBar::tab:hover {
    color: #7c3aed;
}
#funImportsCatBtn {
    border: none;
    border-radius: 6px;
}
#funImportsCatBtn:hover {
    background: #F3E8F6;
}
#funImportsCatLabel {
    font-size: 12px;
    font-weight: 600;
    color: #6b7280;
    padding: 4px 0px;
}
#funImportsEmojiBtn {
    border: none;
    border-radius: 8px;
}
#funImportsEmojiBtn:hover {
    background: #F3E8F6;
}
#funImportsGifBtn {
    border: 1px solid #F0E6E8;
    border-radius: 8px;
}
#funImportsGifBtn:hover {
    border-color: #CFA6D6;
    background: #F3E8F6;
}

/* Checklist Widget */
#checklist {
    background-color: #FFFFFF;
    border: 1px solid #F7D1DC;
    border-radius: 12px;
}
#checklistHeader {
    background-color: #FFF0F3;
    border-top-left-radius: 12px;
    border-bottom: 1px solid #F7D1DC;
}
#checklistTitle {
    border: none;
    background: transparent;
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    color: #8B6B7B;
    font-weight: 600;
    padding: 0;
}
#checklistDeleteBtn {
    border: none;
    font-size: 16px;
    color: #9CA3AF;
    background: transparent;
}
#checklistDeleteBtn:hover {
    color: #EF4444;
}
#checklistAddBtn {
    border: none;
    font-size: 11px;
    color: #8B6B7B;
    background: transparent;
}
#checklistAddBtn:hover {
    color: #2E2B2B;
}

/* Table Widget */
#tableCard {
    background-color: #FFFFFF;
    border: 1px solid #F7D1DC;
    border-radius: 12px;
}
#tableHeader {
    background-color: #FFF0F3;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid #F7D1DC;
}
#tableTitle {
    border: none;
    background: transparent;
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    color: #8B6B7B;
    font-weight: 600;
    padding: 0;
}
#tableDeleteBtn {
    border: none;
    font-size: 16px;
    color: #9CA3AF;
    background: transparent;
}
#tableDeleteBtn:hover {
    color: #EF4444;
}
#tableGrid {
    border: none;
    gridline-color: #F7D1DC;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: #2E2B2B;
    background: #FFFFFF;
    selection-background-color: #F3E8F6;
    selection-color: #2E2B2B;
}
#tableGrid::item {
    padding: 4px 8px;
    border: none;
    border-radius: 6px;
}
#tableGrid::item:selected {
    background: #F3E8F6;
    color: #2E2B2B;
}
#tableGrid QHeaderView::section {
    background: #FFF0F3;
    border: none;
    border-bottom: 1px solid #F7D1DC;
    border-right: 1px solid #F7D1DC;
    padding: 4px 8px;
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: #8B6B7B;
}
#tableGrid QTableCornerButton::section {
    background: #FFF0F3;
    border: none;
    border-bottom: 1px solid #F7D1DC;
    border-right: 1px solid #F7D1DC;
}
#tableGrid QLineEdit {
    border: 1px solid #CFA6D6;
    border-radius: 6px;
    padding: 4px 8px;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    color: #2E2B2B;
    background: #FFFFFF;
}
#tableGrid QLineEdit:focus {
    border-color: #9b59b6;
}
#tableGrid QScrollBar:vertical {
    background: #FFFFFF;
    width: 8px;
    margin: 0;
}
#tableGrid QScrollBar::handle:vertical {
    background: #E8DDE0;
    border-radius: 4px;
    min-height: 20px;
}
#tableGrid QScrollBar::handle:vertical:hover {
    background: #CFA6D6;
}
#tableGrid QScrollBar::add-line:vertical,
#tableGrid QScrollBar::sub-line:vertical {
    height: 0;
}
#tableGrid QScrollBar:horizontal {
    background: #FFFFFF;
    height: 8px;
    margin: 0;
}
#tableGrid QScrollBar::handle:horizontal {
    background: #E8DDE0;
    border-radius: 4px;
    min-width: 20px;
}
#tableGrid QScrollBar::handle:horizontal:hover {
    background: #CFA6D6;
}
#tableGrid QScrollBar::add-line:horizontal,
#tableGrid QScrollBar::sub-line:horizontal {
    width: 0;
}

/* Checkbox Widget */
#checkboxWidget {
    background-color: #FFFFFF;
}
#checkboxText {
    border: none;
    background: transparent;
    font-size: 13px;
    color: #2E2B2B;
    font-family: 'Inter', sans-serif;
    padding: 2px 0;
}
#checkboxText:checked {
    color: #9CA3AF;
    text-decoration: line-through;
}
#checkboxDeleteBtn {
    border: none;
    font-size: 16px;
    color: #9CA3AF;
    background: transparent;
}
#checkboxDeleteBtn:hover {
    color: #EF4444;
}

/* Bulk Create Dialog */
#bulkDateEdit {
    padding: 6px 12px;
    border: 1px solid #F0E6E8;
    border-radius: 10px;
    background: #FFFFFF;
    font-size: 13px;
    color: #2E2B2B;
    min-width: 120px;
    font-family: 'Inter', 'Poppins', sans-serif;
}
#bulkDateEdit::drop-down {
    border: none;
    width: 26px;
    subcontrol-origin: padding;
    subcontrol-position: top right;
    border-radius: 13px;
    background: #FFF0F3;
}
#bulkDateEdit::drop-down:hover {
    background: #FFE4EC;
}
#bulkDateEdit::down-arrow {
    image: url(assets/icons/chevron_down.svg);
    width: 12px;
    height: 12px;
}
#bulkCalendar {
    background: #FFFFFF;
    border: 1px solid #F0E6E8;
    border-radius: 12px;
    font-family: 'Inter', 'Poppins', sans-serif;
    font-size: 10px;
}
#bulkCalendar QToolButton {
    color: #2E2B2B;
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 3px 6px;
    font-size: 11px;
    font-family: 'Inter', 'Poppins', sans-serif;
}
#bulkCalendar QToolButton:hover {
    background: #FFF0F3;
}
#bulkCalendar QToolButton:pressed {
    background: #F7D1DC;
}
#bulkCalendar QToolButton#qt_calendar_prevmonth,
#bulkCalendar QToolButton#qt_calendar_nextmonth {
    qproperty-icon: none;
    min-width: 20px;
    font-size: 11px;
    color: #CFA6D6;
}
#bulkCalendar QToolButton#qt_calendar_prevmonth {
    qproperty-text: "<";
}
#bulkCalendar QToolButton#qt_calendar_nextmonth {
    qproperty-text: ">";
}
#bulkCalendar QToolButton#qt_calendar_prevmonth:hover,
#bulkCalendar QToolButton#qt_calendar_nextmonth:hover {
    color: #2E2B2B;
    background: #FFF0F3;
}
#bulkCalendar QToolButton#qt_calendar_monthbutton,
#bulkCalendar QToolButton#qt_calendar_yearbutton {
    font-size: 11px;
    font-weight: 600;
    min-width: 60px;
    color: #2E2B2B;
}
#bulkCalendar QToolButton#qt_calendar_monthbutton:hover,
#bulkCalendar QToolButton#qt_calendar_yearbutton:hover {
    background: #FFF0F3;
}
#bulkCalendar QToolButton#qt_calendar_monthbutton:pressed,
#bulkCalendar QToolButton#qt_calendar_yearbutton:pressed {
    background: #F7D1DC;
}
#bulkCalendar QWidget#qt_calendar_calendarview {
    background: #FFFFFF;
    border: none;
}
#bulkCalendar QAbstractItemView:enabled {
    color: #2E2B2B;
    background: #FFFFFF;
    selection-background-color: #CFA6D6;
    selection-color: #FFFFFF;
    font-family: 'Inter', 'Poppins', sans-serif;
    font-size: 10px;
    gridline-color: transparent;
}
#bulkCalendar QAbstractItemView:disabled {
    color: #D1D5DB;
}
#bulkCalendar QAbstractItemView:focus {
    outline: none;
}
#bulkCalendar QTableView {
    selection-background-color: #CFA6D6;
    selection-color: #FFFFFF;
}
#bulkCalendar QTableView QHeaderView::section {
    background: #FFF8F5;
    color: #6B6770;
    border: none;
    border-bottom: 1px solid #F0E6E8;
    padding: 3px;
    font-size: 10px;
    font-weight: 600;
    font-family: 'Inter', 'Poppins', sans-serif;
}
#bulkCalendar QWidget#qt_calendar_navigationbar {
    background: #FFF8F5;
    border-top: 1px solid #F0E6E8;
    border-radius: 0 0 12px 12px;
    padding: 3px;
}
#bulkCalendar QCalendarDayWidget {
    padding: 1px;
}
#bulkCalendar QToolButton#qt_calendar_calendarbutton {
    qproperty-icon: none;
    min-width: 20px;
    font-size: 11px;
    color: #CFA6D6;
}
#bulkCalendar QToolButton#qt_calendar_calendarbutton:hover {
    background: #FFF0F3;
    color: #2E2B2B;
}
"""
