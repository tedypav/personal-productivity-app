from PyQt6.QtCore import Qt

__all__ = ["ResizableMixin"]


class ResizableMixin:
    """Shared drag, resize, and edge-detection logic for floating widgets.

    Subclasses must define: self._header, self._title_edit, self._user_width,
    self._MIN_W, self._BORDER, and implement _min_height() and _save_meta().
    """

    def _init_resizable_state(self):
        self._dragging = False
        self._drag_start = None
        self._resizing = False
        self._resize_edge = None
        self._resize_start = None
        self._resize_origin = None
        self._user_width = None
        self._user_height = None
        self._loaded_pos = None
        self._MIN_W = 200
        self._BORDER = 8

    def _min_height(self):
        return 100

    def _on_resize_complete(self):
        pass

    def _detect_edge(self, pos):
        b = self._BORDER
        w, h = self.width(), self.height()
        header_h = self._header.height()
        below_header = pos.y() > header_h
        left = below_header and pos.x() < b
        right = below_header and pos.x() > w - b
        top = below_header and pos.y() < header_h + b
        bottom = pos.y() > h - b
        if left and top:
            return "top-left"
        if right and top:
            return "top-right"
        if left and bottom:
            return "bottom-left"
        if right and bottom:
            return "bottom-right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _edge_cursor(self, edge):
        cursors = {
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "top-left": Qt.CursorShape.SizeFDiagCursor,
            "bottom-right": Qt.CursorShape.SizeFDiagCursor,
            "top-right": Qt.CursorShape.SizeBDiagCursor,
            "bottom-left": Qt.CursorShape.SizeBDiagCursor,
        }
        return cursors.get(edge, Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if pos.y() <= self._header.height():
                child = self._header.childAt(pos)
                if child is self._title_edit:
                    return
                self.setFocus()
                self._dragging = True
                self._drag_start = event.globalPosition().toPoint() - self.pos()
                self._header.setCursor(Qt.CursorShape.ClosedHandCursor)
                event.accept()
                return
            edge = self._detect_edge(pos)
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._resize_start = event.globalPosition().toPoint()
                self._resize_origin = (
                    self.x(),
                    self.y(),
                    self.width(),
                    self.height(),
                )
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_start is not None:
            new_pos = event.globalPosition().toPoint() - self._drag_start
            parent = self.parent()
            if parent:
                new_x = max(0, min(new_pos.x(), parent.width() - self.width()))
                new_y = max(0, min(new_pos.y(), parent.height() - self.height()))
                self.move(new_x, new_y)
            event.accept()
            return
        if self._resizing and self._resize_start is not None:
            curr = event.globalPosition().toPoint()
            dx = curr.x() - self._resize_start.x()
            dy = curr.y() - self._resize_start.y()
            ox, oy, ow, oh = self._resize_origin
            edge = self._resize_edge
            new_x, new_y, new_w, new_h = ox, oy, ow, oh
            if "right" in edge:
                new_w = max(self._MIN_W, ow + dx)
            if "bottom" in edge:
                new_h = max(self._min_height(), oh + dy)
            if "left" in edge:
                new_w = max(self._MIN_W, ow - dx)
                new_x = ox + ow - new_w
            if "top" in edge:
                new_h = max(self._min_height(), oh - dy)
                new_y = oy + oh - new_h
            parent = self.parent()
            if parent:
                new_x = max(0, min(new_x, parent.width() - new_w))
                new_y = max(0, min(new_y, parent.height() - new_h))
            self._user_width = new_w
            self.setMinimumWidth(0)
            self.setMaximumWidth(16777215)
            self.setGeometry(new_x, new_y, new_w, new_h)
            event.accept()
            return
        pos = event.position().toPoint()
        edge = self._detect_edge(pos)
        if edge:
            self.setCursor(self._edge_cursor(edge))
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging:
            self._dragging = False
            self._drag_start = None
            self._header.setCursor(Qt.CursorShape.OpenHandCursor)
            self._save_meta()
            event.accept()
            return
        if self._resizing:
            self._resizing = False
            self._resize_edge = None
            self._resize_start = None
            self._resize_origin = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self._on_resize_complete()
            self._save_meta()
            event.accept()
            return
        super().mouseReleaseEvent(event)
