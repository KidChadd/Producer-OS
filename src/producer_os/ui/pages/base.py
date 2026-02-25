from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from producer_os.ui.widgets import CardFrame, HeaderBlock


class BaseWizardPage(QWidget):
    def __init__(self, title: str, subtitle: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)

        self.header = HeaderBlock(title, subtitle)
        root.addWidget(self.header)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        root.addWidget(self.scroll_area, 1)

        self._content_host = QWidget()
        self.scroll_area.setWidget(self._content_host)
        self.content_layout = QVBoxLayout(self._content_host)
        self.content_layout.setContentsMargins(0, 0, 4, 0)
        self.content_layout.setSpacing(12)
        self.content_layout.addStretch()

    def add_card(self, title: str | None = None, subtitle: str | None = None) -> CardFrame:
        card = CardFrame(title=title, subtitle=subtitle)
        self.content_layout.insertWidget(self.content_layout.count() - 1, card)
        return card

    def add_content_widget(self, widget: QWidget) -> None:
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.content_layout.insertWidget(self.content_layout.count() - 1, widget)
