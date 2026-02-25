from __future__ import annotations

from typing import Iterable, Optional

from PySide6.QtCore import QRect, QSignalBlocker, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from producer_os.ui.animations import animate_reveal, pulse_opacity, stop_pulse


def repolish(widget: QWidget) -> None:
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def set_widget_role(button: QPushButton, role: str) -> None:
    button.setProperty("role", role)
    repolish(button)


class CardFrame(QFrame):
    """Reusable elevated card container."""

    def __init__(self, title: str | None = None, subtitle: str | None = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("CardFrame")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        self.layout_root = layout

        if title:
            title_label = QLabel(title)
            title_label.setObjectName("SectionTitle")
            layout.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("FieldHint")
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)

        self.body_layout = QVBoxLayout()
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(10)
        layout.addLayout(self.body_layout)


class HeaderBlock(QWidget):
    def __init__(self, title: str, subtitle: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("PageTitle")
        layout.addWidget(self.title_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setObjectName("PageSubtitle")
        self.subtitle_label.setWordWrap(True)
        layout.addWidget(self.subtitle_label)


class StatChip(QFrame):
    def __init__(self, label: str, value: str = "0", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatChip")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("StatValue")
        self.label_label = QLabel(label)
        self.label_label.setObjectName("StatLabel")
        layout.addWidget(self.value_label)
        layout.addWidget(self.label_label)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)


class StatusBadge(QLabel):
    def __init__(self, text: str = "Ready", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("StatusBadge")
        self.set_status(text, kind="neutral", pulsing=False)

    def set_status(self, text: str, kind: str = "neutral", pulsing: bool = False) -> None:
        self.setText(text)
        self.setProperty("badgeKind", kind)
        repolish(self)
        if pulsing:
            pulse_opacity(self)
        else:
            stop_pulse(self)


class SegmentedControl(QFrame):
    valueChanged = Signal(str)

    def __init__(self, values: Iterable[str], current: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("SegmentedGroup")
        self._buttons: dict[str, QPushButton] = {}
        self._value = current
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        for value in values:
            button = QPushButton(value.capitalize())
            button.setCheckable(True)
            button.setProperty("segmented", "true")
            button.clicked.connect(lambda checked=False, v=value: self.set_value(v, emit=True))
            self._buttons[value] = button
            layout.addWidget(button)
        self.set_value(current, emit=False)

    def value(self) -> str:
        return self._value

    def set_value(self, value: str, emit: bool = False) -> None:
        if value not in self._buttons:
            return
        self._value = value
        for key, button in self._buttons.items():
            with QSignalBlocker(button):
                button.setChecked(key == value)
            button.setProperty("checked", "true" if key == value else "false")
            repolish(button)
        if emit:
            self.valueChanged.emit(value)


class StepItem(QFrame):
    clicked = Signal()

    def __init__(self, index: int, title: str, description: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.index = index
        self.setObjectName("StepItem")
        self.setProperty("stepState", "idle")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(66)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        idx_label = QLabel(f"{index + 1:02d}")
        idx_label.setObjectName("StepIndex")
        idx_label.setFixedWidth(24)
        root.addWidget(idx_label)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("StepItemTitle")
        text_col.addWidget(self.title_label)

        self.desc_label = QLabel(description)
        self.desc_label.setObjectName("StepItemDesc")
        self.desc_label.setWordWrap(True)
        text_col.addWidget(self.desc_label)

        root.addLayout(text_col, 1)
        repolish(self)

    def set_step_state(self, state: str) -> None:
        self.setProperty("stepState", state)
        repolish(self)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.isEnabled() and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class StepSidebar(QFrame):
    stepSelected = Signal(int)

    def __init__(self, steps: list[tuple[str, str]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("SidebarCard")
        self._items: list[StepItem] = []
        self._current_index = 0
        self._max_clickable = 0
        self._invalid_indices: set[int] = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Workflow")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        hint = QLabel("Guided setup and run orchestration")
        hint.setObjectName("FieldHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._stack = QWidget()
        self._stack_layout = QVBoxLayout(self._stack)
        self._stack_layout.setContentsMargins(0, 6, 0, 6)
        self._stack_layout.setSpacing(8)
        layout.addWidget(self._stack, 1)

        self._highlight = QFrame(self._stack)
        self._highlight.setObjectName("StepHighlight")
        self._highlight.setFixedWidth(4)
        self._highlight.raise_()
        self._highlight.hide()

        for idx, (step_title, desc) in enumerate(steps):
            item = StepItem(idx, step_title, desc, self._stack)
            item.clicked.connect(lambda i=idx: self._on_item_clicked(i))
            self._items.append(item)
            self._stack_layout.addWidget(item)
        self._stack_layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        self.set_max_clickable(0)
        self.set_current_index(0, animate=False)

    def _on_item_clicked(self, index: int) -> None:
        if index <= self._max_clickable:
            self.stepSelected.emit(index)

    def set_max_clickable(self, index: int) -> None:
        self._max_clickable = max(0, index)
        for item in self._items:
            item.setEnabled(item.index <= self._max_clickable)
            cursor = Qt.CursorShape.PointingHandCursor if item.isEnabled() else Qt.CursorShape.ArrowCursor
            item.setCursor(cursor)

    def set_invalid_indices(self, indices: set[int]) -> None:
        self._invalid_indices = set(indices)
        self._apply_states()

    def set_current_index(self, index: int, animate: bool = True) -> None:
        if not self._items:
            return
        self._current_index = max(0, min(index, len(self._items) - 1))
        self._apply_states()
        self._move_highlight(animate=animate)

    def _apply_states(self) -> None:
        for item in self._items:
            if item.index == self._current_index:
                state = "current"
            elif item.index in self._invalid_indices:
                state = "invalid"
            elif item.index < self._current_index:
                state = "done"
            else:
                state = "idle"
            item.set_step_state(state)

    def _highlight_rect_for(self, item: StepItem) -> QRect:
        g = item.geometry()
        return QRect(0, g.y() + 10, 4, max(14, g.height() - 20))

    def _move_highlight(self, animate: bool = True) -> None:
        if not self._items:
            return
        item = self._items[self._current_index]
        target = self._highlight_rect_for(item)
        self._highlight.show()
        if not animate or not self._highlight.isVisible():
            self._highlight.setGeometry(target)
            return
        from PySide6.QtCore import QEasingCurve, QPropertyAnimation

        anim = QPropertyAnimation(self._highlight, b"geometry", self._highlight)
        anim.setDuration(220)
        anim.setStartValue(self._highlight.geometry())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        from producer_os.ui.animations import _keep_animation  # local import to avoid cycle

        _keep_animation(self._highlight, anim)
        anim.start()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._move_highlight(animate=False)


class AnimatedPanel(QWidget):
    def __init__(self, child: QWidget, expanded: bool = False, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.child = child
        layout.addWidget(child)
        if not expanded:
            self.setMaximumHeight(0)
            self.setVisible(False)

    def set_expanded(self, expanded: bool, animate: bool = True) -> None:
        if animate:
            animate_reveal(self, expanded)
        else:
            self.setVisible(expanded)
            self.setMaximumHeight(16777215 if expanded else 0)
