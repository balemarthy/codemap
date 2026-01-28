from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFontMetrics,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsPathItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True, slots=True)
class NodeStyle:
    fill: QColor
    border: QColor
    text: QColor


class ClickableNode(QGraphicsRectItem):
    def __init__(self, label: str, style: NodeStyle, max_text_px: int = 180) -> None:
        super().__init__()
        self.label = label
        self._style = style

        # Optional callbacks to keep hover tidy without monkey-patching methods
        self.on_hover_enter: Optional[Callable[[ClickableNode], None]] = None
        self.on_hover_leave: Optional[Callable[[ClickableNode], None]] = None

        self.setAcceptHoverEvents(True)
        self.setFlag(self.GraphicsItemFlag.ItemIsSelectable, True)

        # Elide long names to keep nodes compact
        self._text = QGraphicsTextItem(self)
        self._text.setDefaultTextColor(style.text)
        fm = QFontMetrics(self._text.font())
        shown = fm.elidedText(label, Qt.TextElideMode.ElideRight, max_text_px)
        self._text.setPlainText(shown)

        # Sizing
        padding_x = 14
        padding_y = 10
        text_rect = self._text.boundingRect()
        w = text_rect.width() + padding_x * 2
        h = text_rect.height() + padding_y * 2
        self.setRect(0, 0, w, h)
        self._text.setPos(padding_x, padding_y)

        self._normal_pen = QPen(style.border, 2)
        self._hover_pen = QPen(style.border.lighter(140), 3)

        self.setBrush(QBrush(style.fill))
        self.setPen(self._normal_pen)

    def hoverEnterEvent(self, event) -> None:  # type: ignore[override]
        self.setPen(self._hover_pen)
        if self.on_hover_enter is not None:
            self.on_hover_enter(self)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:  # type: ignore[override]
        self.setPen(self._normal_pen)
        if self.on_hover_leave is not None:
            self.on_hover_leave(self)
        super().hoverLeaveEvent(event)


class _ConstellationGraphicsView(QGraphicsView):
    node_clicked = Signal(str)
    fit_requested = Signal()

    def __init__(self, scene: QGraphicsScene) -> None:
        super().__init__(scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # Zoom behavior
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        self.fit_requested.emit()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            it = self.itemAt(event.position().toPoint())
            while it is not None and not isinstance(it, ClickableNode):
                it = it.parentItem()

            if isinstance(it, ClickableNode):
                self.node_clicked.emit(it.label)

        super().mousePressEvent(event)


class ConstellationView(QWidget):
    node_clicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._scene = QGraphicsScene(self)
        self._view = _ConstellationGraphicsView(self._scene)

        # Top bar
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        bar = QHBoxLayout()
        bar.setContentsMargins(6, 6, 6, 0)

        self._fit_btn = QPushButton("Fit")
        self._fit_btn.clicked.connect(self.fit_to_contents)

        self._counts_label = QLabel("")
        self._counts_label.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._zoom_label = QLabel("100%")

        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setRange(25, 200)
        self._zoom_slider.setValue(100)
        self._zoom_slider.setFixedWidth(160)
        self._zoom_slider.valueChanged.connect(self._on_zoom_slider)

        bar.addWidget(self._fit_btn)
        bar.addWidget(self._counts_label)
        bar.addStretch(1)
        bar.addWidget(self._zoom_label)
        bar.addWidget(self._zoom_slider)

        root.addLayout(bar)
        root.addWidget(self._view)

        # Styles
        self._style_center = NodeStyle(QColor("#FFE6D6"), QColor("#F07839"), QColor("#072846"))
        self._style_callers = NodeStyle(QColor("#E6F7FF"), QColor("#2B8BB5"), QColor("#072846"))
        self._style_callees = NodeStyle(QColor("#E8FFE6"), QColor("#2E9B4E"), QColor("#072846"))

        self._view.node_clicked.connect(self.node_clicked.emit)
        self._view.fit_requested.connect(self.fit_to_contents)

        # State for hover highlight
        self._all_nodes: list[ClickableNode] = []
        self._all_edges: list[QGraphicsPathItem] = []
        self._edges_by_node: dict[ClickableNode, list[QGraphicsPathItem]] = {}

        # Canvas cap
        self._max_side = 12

    def clear(self) -> None:
        self._scene.clear()
        self._counts_label.setText("")
        self._all_nodes = []
        self._all_edges = []
        self._edges_by_node = {}

    def _on_zoom_slider(self, value: int) -> None:
        # Preserve current view center while changing zoom
        center_scene = self._view.mapToScene(self._view.viewport().rect().center())
        scale = max(0.05, value / 100.0)

        self._view.resetTransform()
        self._view.scale(scale, scale)
        self._view.centerOn(center_scene)

        self._zoom_label.setText(f"{value}%")

    def _sync_zoom_slider_from_view(self) -> None:
        # After fitInView, update slider/label to reflect actual transform
        scale = self._view.transform().m11()
        pct = int(round(scale * 100))
        pct = max(25, min(200, pct))

        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(pct)
        self._zoom_slider.blockSignals(False)
        self._zoom_label.setText(f"{pct}%")

    def fit_to_contents(self) -> None:
        rect = self._scene.itemsBoundingRect().adjusted(-90, -90, 90, 90)
        self._scene.setSceneRect(rect)
        self._view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        self._sync_zoom_slider_from_view()

    def set_graph(self, center: str, callers: list[str], callees: list[str]) -> None:
        self.clear()

        callers_all = sorted(callers, key=lambda s: s.lower())
        callees_all = sorted(callees, key=lambda s: s.lower())

        callers_show = callers_all[: self._max_side]
        callees_show = callees_all[: self._max_side]

        self._counts_label.setText(
            f"Showing callers {len(callers_show)}/{len(callers_all)} . "
            f"Callees {len(callees_show)}/{len(callees_all)}"
        )

        center_node = self._make_node(center, self._style_center, role="center")

        caller_nodes = [self._make_node(s, self._style_callers, role="caller") for s in callers_show]
        callee_nodes = [self._make_node(s, self._style_callees, role="callee") for s in callees_show]

        self._all_nodes = [center_node] + caller_nodes + callee_nodes

        # ---- Layout: center at origin (true center), columns tidy ----
        cbr = center_node.boundingRect()
        center_node.setPos(-cbr.width() / 2, -cbr.height() / 2)

        # Column alignment: right-align callers, left-align callees
        margin_x = 160
        vgap = 16

        max_left_w = max((n.boundingRect().width() for n in caller_nodes), default=0.0)
        max_right_w = max((n.boundingRect().width() for n in callee_nodes), default=0.0)

        center_left_x = center_node.sceneBoundingRect().left()
        center_right_x = center_node.sceneBoundingRect().right()

        left_right_edge = center_left_x - margin_x
        right_left_edge = center_right_x + margin_x

        self._place_column_right_aligned(caller_nodes, right_edge_x=left_right_edge, vgap=vgap)
        self._place_column_left_aligned(callee_nodes, left_edge_x=right_left_edge, vgap=vgap)

        # ---- Edges: attach to real points on the center node (tidy) ----
        edge_pen = QPen(QColor("#9AA5B1"), 1.6)
        edge_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        center_scene = center_node.sceneBoundingRect()
        pad = 8.0

        caller_anchors = self._anchors_along_center_edge(
            top=center_scene.top() + pad,
            bottom=center_scene.bottom() - pad,
            n=len(caller_nodes),
        )
        callee_anchors = self._anchors_along_center_edge(
            top=center_scene.top() + pad,
            bottom=center_scene.bottom() - pad,
            n=len(callee_nodes),
        )

        def add_curve(a: ClickableNode, b: ClickableNode, x1: float, y1: float, x2: float, y2: float) -> None:
            dx = max(120.0, abs(x2 - x1) * 0.55)

            path = QPainterPath()
            path.moveTo(x1, y1)
            path.cubicTo(
                x1 + dx, y1,
                x2 - dx, y2,
                x2, y2,
            )

            item = QGraphicsPathItem(path)
            item.setPen(edge_pen)
            item.setZValue(-1)  # keep edges behind nodes
            self._scene.addItem(item)

            self._all_edges.append(item)
            self._edges_by_node.setdefault(a, []).append(item)
            self._edges_by_node.setdefault(b, []).append(item)

        # Callers -> center (endpoints distributed on center node)
        for i, n in enumerate(caller_nodes):
            r = n.sceneBoundingRect()
            y1 = r.center().y()
            y2 = caller_anchors[i]
            add_curve(n, center_node, r.right(), y1, center_scene.left(), y2)

        # Center -> callees
        for i, n in enumerate(callee_nodes):
            r = n.sceneBoundingRect()
            y1 = callee_anchors[i]
            y2 = r.center().y()
            add_curve(center_node, n, center_scene.right(), y1, r.left(), y2)

        # ---- Hover highlight: dim others, brighten connected edges ----
        for n in self._all_nodes:
            n.on_hover_enter = self._on_node_hover_enter
            n.on_hover_leave = self._on_node_hover_leave

        self.fit_to_contents()

    def _anchors_along_center_edge(self, top: float, bottom: float, n: int) -> list[float]:
        if n <= 0:
            return []
        if n == 1:
            return [(top + bottom) / 2.0]
        step = (bottom - top) / (n - 1)
        return [top + i * step for i in range(n)]

    def _place_column_right_aligned(self, nodes: list[ClickableNode], right_edge_x: float, vgap: float) -> None:
        if not nodes:
            return
        heights = [n.boundingRect().height() for n in nodes]
        total_h = sum(heights) + vgap * (len(nodes) - 1)

        y = -total_h / 2.0
        for n, h in zip(nodes, heights):
            w = n.boundingRect().width()
            n.setPos(right_edge_x - w, y)
            y += h + vgap

    def _place_column_left_aligned(self, nodes: list[ClickableNode], left_edge_x: float, vgap: float) -> None:
        if not nodes:
            return
        heights = [n.boundingRect().height() for n in nodes]
        total_h = sum(heights) + vgap * (len(nodes) - 1)

        y = -total_h / 2.0
        for n, h in zip(nodes, heights):
            n.setPos(left_edge_x, y)
            y += h + vgap

    def _on_node_hover_enter(self, node: ClickableNode) -> None:
        for n in self._all_nodes:
            n.setOpacity(0.55)
        for e in self._all_edges:
            e.setOpacity(0.18)

        node.setOpacity(1.0)
        for e in self._edges_by_node.get(node, []):
            e.setOpacity(0.95)

    def _on_node_hover_leave(self, node: ClickableNode) -> None:
        for n in self._all_nodes:
            n.setOpacity(1.0)
        for e in self._all_edges:
            e.setOpacity(1.0)

    def _make_node(self, label: str, style: NodeStyle, role: str) -> ClickableNode:
        node = ClickableNode(label, style)
        self._scene.addItem(node)
        node.setToolTip(f"{role}: {label}")
        return node
