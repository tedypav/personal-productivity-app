import os

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QLabel


def _get_icon_path(name: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "assets",
        "icons",
        f"{name}.svg",
    )


def create_dialog_header(title: str) -> QHBoxLayout:
    layout = QHBoxLayout()
    logo_path = _get_icon_path("logo_icon")
    if os.path.exists(logo_path):
        logo_label = QLabel()
        logo_label.setPixmap(QIcon(logo_path).pixmap(28, 28))
        layout.addWidget(logo_label)
    title_label = QLabel(title)
    title_label.setStyleSheet(
        "font-size: 16px; font-weight: 600; color: #2E2B2B;"
        " font-family: 'Playfair Display', serif;"
    )
    layout.addWidget(title_label)
    layout.addStretch()
    return layout
