# shape_editor_v3.py
# unified composite/shape hierarchy + grid + delete buttons + export
import sys
import copy
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QFileDialog, QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem,
    QInputDialog, QMenu, QAction
)
from PyQt5.QtGui import QPainter, QPen, QColor, QKeySequence
from PyQt5.QtCore import Qt, QPoint, QRectF, pyqtSignal
import math

# Measurement units: treat 1 pixel == 1 mm as requested
PX_PER_MM = 50.0
# Make lines slightly thicker so they are easier to click
LINE_PIXEL_WIDTH = 4  # pen width in device pixels
VERTEX_RADIUS_PX = 4  # vertex marker radius in device pixels
BTN_SIZE = 18
UNDO_LIMIT = 100

class LineSeg:
    def __init__(self, a: QPoint, b: QPoint):
        self.a = a
        self.b = b
        self.id = id(self)

class ShapeObj:
    def __init__(self, name, color: QColor):
        self.name = name
        self.color = color
        self.lines: list[LineSeg] = []

class GlueTab:
    def __init__(self, a: QPoint=None, b: QPoint=None):
        self.a = a
        self.b = b
        self.id = id(self)

class GridWidget(QWidget):
    shapes_changed = pyqtSignal()
    history_changed = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.shapes: dict[str, ShapeObj] = {}
        self.glue_tabs: dict[int, GlueTab] = {}
        self.current_mode = 'shape'
        self.selected_shape: str | None = None
        self.selected_segment_id: int | None = None
        self.selected_glue_id: int | None = None
        self.dragging = False
        self.drag_start: QPoint | None = None
        # (no inline widgets) segments will be clickable and show a popup menu
        # track selected vertex for starting/ending lines
        self.selected_vertex = None  # tuple (shape_name, seg, 'a'|'b') or None
        # Zoom / view scale (1.0 = 100%) and pan offset (world coords)
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.zoom_mode = False
        # panning state
        self.panning = False
        self.pan_start_dev = None
        self.pan_start_off = (0.0, 0.0)
        # drag mode state
        self.drag_mode = False
        self.dragging_segment = None
        self.drag_start_pos = None
        self._auto_fitted = False
        self.hover_target = None  # tuple (owner_type, owner, seg) when mouse hovers near a segment
        self.setMouseTracking(True)
        # Undo/Redo stacks
        self.undo_stack = []
        self.redo_stack = []

    def save_state(self):
        """Saves a deep copy of the current shapes and glue tabs to the undo stack."""
        state = (copy.deepcopy(self.shapes), copy.deepcopy(self.glue_tabs))
        self.undo_stack.append(state)
        if len(self.undo_stack) > UNDO_LIMIT:
            self.undo_stack.pop(0)
        # A new action clears the redo stack
        self.redo_stack.clear()
        self.history_changed.emit()

    def undo(self):
        """Restores the previous state from the undo stack."""
        if not self.undo_stack:
            return
        # Save current state to redo stack
        current_state = (copy.deepcopy(self.shapes), copy.deepcopy(self.glue_tabs))
        self.redo_stack.append(current_state)
        # Restore previous state
        last_state = self.undo_stack.pop()
        self.shapes, self.glue_tabs = last_state
        self.shapes_changed.emit()
        self.history_changed.emit()
        self.update()

    def redo(self):
        """Restores a future state from the redo stack."""
        if not self.redo_stack:
            return
        # Save current state to undo stack
        current_state = (copy.deepcopy(self.shapes), copy.deepcopy(self.glue_tabs))
        self.undo_stack.append(current_state)
        # Restore next state
        next_state = self.redo_stack.pop()
        self.shapes, self.glue_tabs = next_state
        self.shapes_changed.emit()
        self.history_changed.emit()
        self.update()

    def to_world(self, p: QPoint) -> QPoint:
        """Convert device/widget coordinates to world coordinates (unscaled).

        The drawing data is stored in world coordinates. When zoomed, we scale the painter
        when drawing; mouse events provide device coordinates which must be mapped back.
        """
        if self.scale == 0:
            return QPoint(p.x(), p.y())
        total_scale = self.scale * PX_PER_MM
        # world = offset + device/total_scale
        wx = self.offset_x + (p.x() / total_scale)
        wy = self.offset_y + (p.y() / total_scale)
        return QPoint(int(round(wx)), int(round(wy)))

    def to_device(self, p: QPoint) -> QPoint:
        """Convert world coordinates to device/widget coordinates (apply scale).
        """
        total_scale = self.scale * PX_PER_MM
        dx = (p.x() - self.offset_x) * total_scale
        dy = (p.y() - self.offset_y) * total_scale
        return QPoint(int(round(dx)), int(round(dy)))

    # kept for compatibility with earlier calls; behaves like to_world (no grid snapping)
    def snap(self, p: QPoint) -> QPoint:
        return self.to_world(p)

    def paintEvent(self, e):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(QRectF(0,0,w,h), QColor(255,255,255))

        total_scale = self.scale * PX_PER_MM

        # Draw shapes and glue using device coordinates computed from world (mm) coords
        for shp in self.shapes.values():
            pen = QPen(shp.color, LINE_PIXEL_WIDTH)
            p.setPen(pen)
            for seg in shp.lines:
                a_dev = self.to_device(seg.a)
                b_dev = self.to_device(seg.b)
                # draw hover outline underneath if this segment is hovered
                if self.hover_target and self.hover_target[0] == 'shape' and self.hover_target[2].id == seg.id:
                    hpen = QPen(QColor(255, 120, 0, 180), max(1, LINE_PIXEL_WIDTH + 4))
                    hpen.setCapStyle(Qt.RoundCap)
                    p.setPen(hpen)
                    p.drawLine(a_dev, b_dev)
                    p.setPen(pen)
                p.drawLine(a_dev, b_dev)
                # draw small vertex markers (fixed size in device pixels)
                vpen = QPen(QColor(0,0,0), 1)
                p.setPen(vpen)
                p.setBrush(QColor(200,200,255))
                r = VERTEX_RADIUS_PX
                p.drawEllipse(QRectF(a_dev.x()-r, a_dev.y()-r, r*2, r*2))
                p.drawEllipse(QRectF(b_dev.x()-r, b_dev.y()-r, r*2, r*2))
                # restore pen for line text after drawing markers
                p.setPen(pen)
                # draw length label near midpoint (length in mm)
                mx = (seg.a.x() + seg.b.x())/2.0
                my = (seg.a.y() + seg.b.y())/2.0
                length = math.hypot(seg.b.x()-seg.a.x(), seg.b.y()-seg.a.y())
                text = f"{length:.1f} mm"
                # small offset perpendicular to the line for better visibility (in mm -> convert to dev)
                dx = seg.b.x() - seg.a.x(); dy = seg.b.y() - seg.a.y()
                if dx == 0 and dy == 0:
                    ox_mm, oy_mm = 6, -18
                else:
                    norm = math.hypot(dx, dy)
                    ox_mm = -dy / norm * 18
                    oy_mm = dx / norm * 18
                # convert label pos to device coords
                label_dev = self.to_device(QPoint(int(round(mx+ox_mm)), int(round(my+oy_mm))))
                p.drawText(label_dev.x(), label_dev.y(), text)

        pen = QPen(QColor(0,120,0), LINE_PIXEL_WIDTH, Qt.DashLine)
        p.setPen(pen)
        for glue in self.glue_tabs.values():
            if glue.a and glue.b:
                a_dev = self.to_device(glue.a)
                b_dev = self.to_device(glue.b)
                # highlight glue if hovered
                if self.hover_target and self.hover_target[0] == 'glue' and self.hover_target[2].id == glue.id:
                    hpen = QPen(QColor(255, 120, 0, 180), max(1, LINE_PIXEL_WIDTH + 4))
                    hpen.setCapStyle(Qt.RoundCap)
                    p.setPen(hpen)
                    p.drawLine(a_dev, b_dev)
                    p.setPen(pen)
                p.drawLine(a_dev, b_dev)

        if self.dragging and self.drag_start:
            # show preview line from drag_start to current cursor position (in world coords)
            pos_dev = self.mapFromGlobal(self.cursor().pos())
            pos_world = self.to_world(pos_dev)
            # constrain to horizontal or vertical for preview
            dx = pos_world.x() - self.drag_start.x(); dy = pos_world.y() - self.drag_start.y()
            if abs(dx) >= abs(dy):
                preview_end = QPoint(pos_world.x(), self.drag_start.y())
            else:
                preview_end = QPoint(self.drag_start.x(), pos_world.y())
            pen = QPen(QColor(0,0,0), LINE_PIXEL_WIDTH, Qt.DotLine)
            p.setPen(pen)
            p.drawLine(self.to_device(self.drag_start), self.to_device(preview_end))

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            pt_dev = ev.pos()
            pt = self.to_world(pt_dev)

            # --- Mode-specific handlers ---
            if self.drag_mode:
                stype, owner, sobj = self.find_nearest_segment_dev(ev.pos())
                if stype:
                    self.save_state()  # Save state before starting a drag
                    self.dragging_segment = sobj
                    self.drag_start_pos = self.to_world(ev.pos())
                return
            if getattr(self, 'pan_mode', False):
                self.panning = True
                self.pan_start_dev = ev.pos()
                self.pan_start_off = (self.offset_x, self.offset_y)
                return

            if ev.modifiers() & Qt.ShiftModifier:
                self.delete_nearest_segment(ev.pos()); return
            
            # --- Default drawing/interaction handlers ---
            # If clicked near an existing vertex, start dragging from that vertex
            v = self.find_nearest_vertex(pt, thresh=6)
            if v:
                shape_name, seg, which, vpt = v
                self.selected_vertex = (shape_name, seg, which)
                self.dragging = True; self.drag_start = QPoint(vpt.x(), vpt.y())
                return
            # If hovered over a segment, prefer that as the click target and show popup menu
            if self.hover_target:
                stype, owner, sobj = self.hover_target
                menu = QMenu(self)
                if stype == 'shape':
                    a = menu.addAction("Delete Segment")
                    a.triggered.connect(lambda _, sid=sobj.id: self.delete_segment_by_id(sid))
                    b = menu.addAction("Edit Segment Length")
                    b.triggered.connect(lambda _, sid=sobj.id: self.edit_segment_by_id(sid))
                else:
                    a = menu.addAction("Delete Glue")
                    a.triggered.connect(lambda _, gid=owner: self.delete_glue_by_id(gid))
                    b = menu.addAction("Edit Glue Length")
                    b.triggered.connect(lambda _, gid=owner: self.edit_glue_by_id(gid))
                menu.exec_(ev.globalPos())
                return
            # otherwise fall back to device-space nearest-segment detection
            stype, owner, sobj = self.find_nearest_segment_dev(ev.pos(), thresh_px=10)
            if stype:
                menu = QMenu(self)
                if stype == 'shape':
                    a = menu.addAction("Delete Segment")
                    a.triggered.connect(lambda _, sid=sobj.id: self.delete_segment_by_id(sid))
                    b = menu.addAction("Edit Segment Length")
                    b.triggered.connect(lambda _, sid=sobj.id: self.edit_segment_by_id(sid))
                else:
                    a = menu.addAction("Delete Glue")
                    a.triggered.connect(lambda _, gid=owner: self.delete_glue_by_id(gid))
                    b = menu.addAction("Edit Glue Length")
                    b.triggered.connect(lambda _, gid=owner: self.edit_glue_by_id(gid))
                menu.exec_(ev.globalPos())
                return
            if self.current_mode == 'shape' and self.selected_shape:
                self.dragging = True; self.drag_start = pt
            elif self.current_mode == 'glue' and self.selected_glue_id is not None:
                self.dragging = True; self.drag_start = pt
        elif ev.button() == Qt.MiddleButton:
            # start panning
            self.panning = True
            self.pan_start_dev = ev.pos()
            self.pan_start_off = (self.offset_x, self.offset_y)

    def mouseMoveEvent(self, ev):
        if self.dragging_segment and self.drag_start_pos:
            current_pos = self.to_world(ev.pos())
            delta = current_pos - self.drag_start_pos
            self.dragging_segment.a += delta
            self.dragging_segment.b += delta
            self.drag_start_pos = current_pos
            self.update()
            return

        if self.panning and self.pan_start_dev is not None:
            # compute device delta and update offset (world units)
            dx = ev.pos().x() - self.pan_start_dev.x()
            dy = ev.pos().y() - self.pan_start_dev.y()
            total_scale = self.scale * PX_PER_MM
            self.offset_x = self.pan_start_off[0] - (dx / total_scale)
            self.offset_y = self.pan_start_off[1] - (dy / total_scale)
            self.update()
            return
        if self.dragging:
            self.update()
            return

        # update hover target when not panning or dragging
        pos_dev = ev.pos()
        stype, owner, sobj = self.find_nearest_segment_dev(pos_dev, thresh_px=None)
        new_hover = (stype, owner, sobj) if stype else None
        if (self.hover_target is None and new_hover is not None) or (self.hover_target is not None and new_hover is None) or (self.hover_target is not None and new_hover is not None and self.hover_target[2].id != new_hover[2].id):
            self.hover_target = new_hover
            self.update()

    def mouseReleaseEvent(self, ev):
        if self.dragging_segment:
            self.dragging_segment = None
            self.drag_start_pos = None
            self.shapes_changed.emit() # Update sidebar with new segment info if needed
            self.update()
            return

        # If left button released while panning (Pan Mode), stop panning
        if ev.button() == Qt.LeftButton and self.panning:
            self.panning = False
            self.pan_start_dev = None
            self.pan_start_off = (self.offset_x, self.offset_y)
            self.update()
            return

        if ev.button() == Qt.LeftButton and self.dragging and self.drag_start:
            end = self.to_world(ev.pos())
            # Constrain to horizontal or vertical relative to drag_start
            dx = end.x() - self.drag_start.x(); dy = end.y() - self.drag_start.y()
            if abs(dx) >= abs(dy):
                end = QPoint(end.x(), self.drag_start.y())
            else:
                end = QPoint(self.drag_start.x(), end.y())
            # If released near an existing vertex, snap to it
            v = self.find_nearest_vertex(end, thresh=6)
            if v:
                _, _, _, vpt = v
                end = QPoint(vpt.x(), vpt.y())
            if end != self.drag_start:
                self.save_state()  # Save state before making a change
                if self.current_mode == 'shape' and self.selected_shape:
                    shp = self.shapes.get(self.selected_shape)
                    if shp:
                        shp.lines.append(LineSeg(self.drag_start, end))
                        # notify listeners (sidebar) that shapes changed
                        self.shapes_changed.emit()
                elif self.current_mode == 'glue' and self.selected_glue_id is not None:
                    glue = self.glue_tabs.get(self.selected_glue_id)
                    if glue:
                        glue.a, glue.b = self.drag_start, end
                        self.shapes_changed.emit()
            self.dragging = False; self.drag_start = None; self.update()
        elif ev.button() == Qt.MiddleButton and self.panning:
            self.panning = False
            self.pan_start_dev = None
            self.pan_start_off = (self.offset_x, self.offset_y)
            self.update()

    def delete_nearest_segment(self, pos):
        # pos is device coords; convert to world coords for comparison
        pos_w = self.to_world(pos)
        best, best_d, owner, owner_type = None, 9999, None, None
        for name, shp in self.shapes.items():
            for seg in shp.lines:
                d = self._point_seg_dist(pos_w, seg.a, seg.b)
                if d < best_d: best_d, best, owner, owner_type = d, seg, name, 'shape'
        for gid, glue in self.glue_tabs.items():
            if glue.a and glue.b:
                d = self._point_seg_dist(pos_w, glue.a, glue.b)
                if d < best_d: best_d, best, owner, owner_type = d, glue, gid, 'glue'
        # threshold in world pixels (approx)
        if best and best_d < 12:
            self.save_state()  # Save state before making a change
            if owner_type == 'shape':
                self.shapes[owner].lines = [s for s in self.shapes[owner].lines if s.id != best.id]
                self.shapes_changed.emit()
            else:
                del self.glue_tabs[owner]
                self.shapes_changed.emit()
            self.update()

    def find_nearest_segment(self, p: QPoint, thresh: float = 6.0):
        """Find nearest segment (shape or glue) to world point p.

        Returns tuple (owner_type, owner_id_or_name, seg_obj) or (None, None, None).
        """
        best_d = float('inf'); best_item = (None, None, None)
        for name, shp in self.shapes.items():
            for seg in shp.lines:
                d = self._point_seg_dist(p, seg.a, seg.b)
                if d < best_d:
                    best_d = d; best_item = ('shape', name, seg)
        for gid, glue in self.glue_tabs.items():
            if glue.a and glue.b:
                d = self._point_seg_dist(p, glue.a, glue.b)
                if d < best_d:
                    best_d = d; best_item = ('glue', gid, glue)
        if best_item[0] and best_d <= thresh:
            return best_item
        return (None, None, None)

    def _point_seg_dist_dev(self, p_dev: QPoint, a_dev: QPoint, b_dev: QPoint):
        """Distance from device point p_dev to device segment a_dev-b_dev (pixels)."""
        px, py = p_dev.x(), p_dev.y()
        x1, y1 = a_dev.x(), a_dev.y(); x2, y2 = b_dev.x(), b_dev.y()
        dx, dy = x2-x1, y2-y1
        if dx == 0 and dy == 0:
            return math.hypot(px-x1, py-y1)
        t = ((px-x1)*dx + (py-y1)*dy) / (dx*dx + dy*dy)
        t = max(0.0, min(1.0, t))
        projx, projy = x1 + t*dx, y1 + t*dy
        return math.hypot(px-projx, py-projy)

    def find_nearest_segment_dev(self, pos_dev: QPoint, thresh_px: float | None = None):
        """Find nearest segment using device coordinates so clicks work regardless of zoom/pan.

        Returns tuple (owner_type, owner_id_or_name, seg_obj) or (None, None, None).
        """
        best_d = float('inf'); best_item = (None, None, None)
        for name, shp in self.shapes.items():
            for seg in shp.lines:
                a_dev = self.to_device(seg.a)
                b_dev = self.to_device(seg.b)
                d = self._point_seg_dist_dev(pos_dev, a_dev, b_dev)
                if d < best_d:
                    best_d = d; best_item = ('shape', name, seg)
        for gid, glue in self.glue_tabs.items():
            if glue.a and glue.b:
                a_dev = self.to_device(glue.a)
                b_dev = self.to_device(glue.b)
                d = self._point_seg_dist_dev(pos_dev, a_dev, b_dev)
                if d < best_d:
                    best_d = d; best_item = ('glue', gid, glue)
        # determine pixel threshold (if not provided, base on line visual width)
        if thresh_px is None:
            thr = max(10, int(round(LINE_PIXEL_WIDTH * 1.5)))
        else:
            thr = thresh_px
        if best_item[0] and best_d <= thr:
            return best_item
        return (None, None, None)

    def _point_seg_dist(self, p, a, b):
        px, py, x1, y1, x2, y2 = p.x(), p.y(), a.x(), a.y(), b.x(), b.y()
        dx, dy = x2-x1, y2-y1
        if dx==0 and dy==0: return ((px-x1)**2+(py-y1)**2)**0.5
        t = ((px-x1)*dx+(py-y1)*dy)/(dx*dx+dy*dy)
        t = max(0, min(1, t))
        projx, projy = x1+t*dx, y1+t*dy
        return ((px-projx)**2+(py-projy)**2)**0.5

    def _point_point_dist(self, p, a):
        return ((p.x()-a.x())**2 + (p.y()-a.y())**2)**0.5

    def find_nearest_vertex(self, p: QPoint, thresh: float = 6.0):
        """Find nearest vertex (endpoint of any segment) within thresh (world units).

        Returns tuple (shape_name, seg, 'a'|'b', QPoint) or None.
        """
        best_d = float('inf'); best_item = None
        for name, shp in self.shapes.items():
            for seg in shp.lines:
                da = self._point_point_dist(p, seg.a)
                if da < best_d:
                    best_d = da; best_item = (name, seg, 'a', seg.a)
                db = self._point_point_dist(p, seg.b)
                if db < best_d:
                    best_d = db; best_item = (name, seg, 'b', seg.b)
        if best_item and best_d <= thresh:
            return best_item
        return None

    def set_zoom_mode(self, on: bool):
        self.zoom_mode = bool(on)

    def wheelEvent(self, ev):
        # Zoom when in zoom_mode. Use angleDelta().y() to compute factor.
        if not self.zoom_mode:
            # default: ignore (could be used for vertical scrolling later)
            return
        delta = ev.angleDelta().y()
        if delta == 0:
            return
        # compute cursor device pos and corresponding world pos BEFORE zoom using floats
        pos_dev = ev.pos()
        total_scale = self.scale * PX_PER_MM
        # world coords (float) = offset + device / total_scale
        pos_world_x = self.offset_x + (pos_dev.x() / total_scale)
        pos_world_y = self.offset_y + (pos_dev.y() / total_scale)
        # smooth factor
        factor = 1.001 ** delta
        new_scale = max(0.01, min(20.0, self.scale * factor))
        # apply new scale and compute offsets so the visual cursor location maps to the same world point
        self.scale = new_scale
        total_scale = self.scale * PX_PER_MM
        self.offset_x = pos_world_x - (pos_dev.x() / total_scale)
        self.offset_y = pos_world_y - (pos_dev.y() / total_scale)
        self.update()

    def resizeEvent(self, ev):
        # On first resize, set scale so that the view covers approx 200 x 200 world units
        if not self._auto_fitted:
            w = self.width(); h = self.height()
            if w > 0 and h > 0:
                # total pixels-per-mm = w/200 -> scale = (pixels-per-mm) / PX_PER_MM
                self.scale = min(w / 200.0, h / 200.0) / PX_PER_MM
                self.offset_x = 0.0
                self.offset_y = 0.0
                self._auto_fitted = True
        super().resizeEvent(ev)

    # inline widget helpers removed; segments are now clickable and use a popup menu

    def find_segment_by_id(self, seg_id: int):
        for name, shp in self.shapes.items():
            for seg in shp.lines:
                if seg.id == seg_id:
                    return name, seg
        return None, None

    def delete_glue_by_id(self, gid: int):
        if gid in self.glue_tabs:
            self.save_state()
            del self.glue_tabs[gid]
            try:
                self.shapes_changed.emit()
            except Exception:
                pass
            self.update()

    def edit_glue_by_id(self, gid: int):
        g = self.glue_tabs.get(gid)
        if g:
            self._edit_length(g, 'glue', gid)

    def delete_segment_by_id(self, seg_id: int):
        name, seg = self.find_segment_by_id(seg_id)
        if name and seg:
            self.save_state()
            self.shapes[name].lines = [s for s in self.shapes[name].lines if s.id != seg_id]
            self.shapes_changed.emit()
            self.update()

    def edit_segment_by_id(self, seg_id: int):
        name, seg = self.find_segment_by_id(seg_id)
        if seg:
            # reuse existing edit handler for shapes
            self._edit_length(seg, 'shape', name)

    def _del_seg(self, seg, shape_name):
        shp = self.shapes.get(shape_name)
        if shp:
            self.save_state()
            shp.lines = [s for s in shp.lines if s.id != seg.id]
        try:
            self.shapes_changed.emit()
        except Exception:
            pass
        self.update()

    def _del_glue(self, gid):
        if gid in self.glue_tabs:
            self.save_state()
            g = self.glue_tabs.pop(gid)
            try:
                self.shapes_changed.emit()
            except Exception:
                pass
            self.update()

    def _edit_length(self, seg_or_glue, owner_type, owner):
        """Open a dialog to set length in millimeters for a segment or glue tab.

        seg_or_glue: LineSeg instance when owner_type=='shape', or GlueTab when 'glue'.
        """
        # Determine endpoints
        if owner_type == 'shape':
            seg = seg_or_glue
            a = seg.a
            b = seg.b
        else:
            g = seg_or_glue if isinstance(seg_or_glue, GlueTab) else self.glue_tabs.get(seg_or_glue)
            if not g or not g.a or not g.b:
                QMessageBox.information(self, "Edit Length", "Glue tab does not have endpoints yet.")
                return
            a = g.a; b = g.b

        # Current length in mm (world coords are mm)
        cur_mm = math.hypot(b.x()-a.x(), b.y()-a.y())
        val, ok = QInputDialog.getDouble(self, "Set length", "Length (mm):", cur_mm, 0.0, 100000.0, 3)
        if not ok:
            return
        
        self.save_state() # Save state before applying the change
        new_mm = val

        dx = b.x() - a.x(); dy = b.y() - a.y()
        if dx == 0 and dy == 0:
            angle = 0.0
        else:
            angle = math.atan2(dy, dx)

        nx = int(round(a.x() + math.cos(angle) * new_mm))
        ny = int(round(a.y() + math.sin(angle) * new_mm))
        # new_pt is in world coords (mm)
        new_pt = QPoint(nx, ny)

        if owner_type == 'shape':
            seg.b = new_pt
        else:
            # Since g might have been fetched from the dictionary, ensure we modify the instance in the dictionary
            g_to_modify = self.glue_tabs.get(owner)
            if g_to_modify:
                g_to_modify.b = new_pt
        self.update()
        self.shapes_changed.emit()

    # --- Zoom / view control methods ---
    def set_scale(self, scale: float):
        self.scale = max(0.1, min(10.0, float(scale)))
        # reposition buttons and redraw
        self.update()

    def zoom_in(self):
        self.set_scale(self.scale * 1.25)

    def zoom_out(self):
        self.set_scale(self.scale / 1.25)

    def reset_zoom(self):
        self.set_scale(1.0)

class Sidebar(QWidget):
    def __init__(self, grid: GridWidget):
        super().__init__()
        self.grid = grid
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Shapes"))
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.itemClicked.connect(self.on_click)
        # Rebuild the tree when shapes change in the grid
        try:
            self.grid.shapes_changed.connect(self.rebuild_tree)
            self.grid.history_changed.connect(self.update_history_buttons)
        except Exception:
            pass
        self.layout.addWidget(self.tree)

        btns = QHBoxLayout()
        nb = QPushButton("New Shape"); nb.clicked.connect(self.new_shape); btns.addWidget(nb)
        nd = QPushButton("Delete"); nd.clicked.connect(self.delete_selected); btns.addWidget(nd)
        self.layout.addLayout(btns)

        # Undo / Redo Buttons
        history_btns = QHBoxLayout()
        self.undo_btn = QPushButton("Undo"); self.undo_btn.clicked.connect(self.grid.undo); history_btns.addWidget(self.undo_btn)
        self.redo_btn = QPushButton("Redo"); self.redo_btn.clicked.connect(self.grid.redo); history_btns.addWidget(self.redo_btn)
        self.layout.addLayout(history_btns)

    # (segment operations removed; use click-on-segment popup/menu instead)

        self.layout.addWidget(QLabel("Glue Tabs"))
        gbtns = QHBoxLayout()
        gg = QPushButton("New Glue"); gg.clicked.connect(self.new_glue); gbtns.addWidget(gg)
        gd = QPushButton("Delete Glue"); gd.clicked.connect(self.delete_glue); gbtns.addWidget(gd)
        self.layout.addLayout(gbtns)

        # --- View Control Modes ---
        self.layout.addWidget(QLabel("View Controls"))
        
        # Zoom mode
        zbtns = QHBoxLayout()
        self.zmode_btn = QPushButton("Zoom Mode")
        self.zmode_btn.setCheckable(True)
        self.zmode_btn.toggled.connect(lambda v: self.grid.set_zoom_mode(v))
        zbtns.addWidget(self.zmode_btn)
        zinstruct = QLabel("(scroll wheel)")
        zbtns.addWidget(zinstruct)
        self.layout.addLayout(zbtns)

        # Pan mode
        pbtns = QHBoxLayout()
        self.pmode_btn = QPushButton("Pan Mode")
        self.pmode_btn.setCheckable(True)
        self.pmode_btn.toggled.connect(self.toggle_pan_mode)
        pbtns.addWidget(self.pmode_btn)
        pinstruct = QLabel("(left-drag to pan)")
        pbtns.addWidget(pinstruct)
        self.layout.addLayout(pbtns)
        
        # Drag mode
        dbtns = QHBoxLayout()
        self.dmode_btn = QPushButton("Drag Mode")
        self.dmode_btn.setCheckable(True)
        self.dmode_btn.toggled.connect(self.toggle_drag_mode)
        dbtns.addWidget(self.dmode_btn)
        dinstruct = QLabel("(left-drag to move segments)")
        dbtns.addWidget(dinstruct)
        self.layout.addLayout(dbtns)

        exp = QPushButton("Export TXT"); exp.clicked.connect(self.export_txt); self.layout.addWidget(exp)
        self.layout.addStretch()

        self.current_glue = None
        self.update_history_buttons()

    def toggle_pan_mode(self, checked):
        """Activates pan mode and deactivates drag mode."""
        self.grid.pan_mode = checked
        if checked and self.dmode_btn.isChecked():
            self.dmode_btn.setChecked(False)
    
    def toggle_drag_mode(self, checked):
        """Activates drag mode and deactivates pan mode."""
        self.grid.drag_mode = checked
        if checked and self.pmode_btn.isChecked():
            self.pmode_btn.setChecked(False)

    def update_history_buttons(self):
        """Enables/disables undo/redo buttons based on stack state."""
        self.undo_btn.setEnabled(bool(self.grid.undo_stack))
        self.redo_btn.setEnabled(bool(self.grid.redo_stack))


    def new_shape(self):
        self.grid.save_state()
        name = f"Shape_{len(self.grid.shapes)+1}"
        color = QColor.fromHsv((len(self.grid.shapes)*37)%360,180,200)
        shp = ShapeObj(name, color)
        self.grid.shapes[name] = shp
        item = QTreeWidgetItem([name])
        item.setBackground(0, color)
        self.tree.addTopLevelItem(item)
        self.grid.selected_shape = name
        self.grid.current_mode = 'shape'
        self.grid.update()
        try:
            self.grid.shapes_changed.emit()
        except Exception:
            pass

    # composites feature removed

    def on_click(self, item):
        # If the clicked item has a parent, it's a segment entry
        parent = item.parent()
        if parent is not None:
            # segment item
            self.grid.selected_shape = parent.text(0)
            seg_id = item.data(0, Qt.UserRole)
            self.grid.selected_segment_id = seg_id
            self.grid.current_mode = 'shape'
        else:
            name = item.text(0)
            if name in self.grid.shapes:
                self.grid.selected_shape = name
                self.grid.current_mode = 'shape'
            else:
                self.grid.selected_shape = None
                self.grid.current_mode = ''
        self.grid.update()

    def rebuild_tree(self):
        self.tree.clear()
        for name, shp in self.grid.shapes.items():
            item = QTreeWidgetItem([name])
            item.setBackground(0, shp.color)
            self.tree.addTopLevelItem(item)
            # add segments as children
            for seg in shp.lines:
                dx = seg.b.x()-seg.a.x(); dy = seg.b.y()-seg.a.y()
                length = ((dx*dx+dy*dy)**0.5)
                child = QTreeWidgetItem([f"seg {seg.id}: L={length:.1f} mm"])
                child.setData(0, Qt.UserRole, seg.id)
                item.addChild(child)
        # composites feature removed

    def delete_selected(self):
        item = self.tree.currentItem()
        if not item: return
        name = item.text(0)
        if name in self.grid.shapes:
            self.grid.save_state()
            shp = self.grid.shapes.pop(name)
        idx = self.tree.indexOfTopLevelItem(item)
        if idx >= 0: self.tree.takeTopLevelItem(idx)
        self.grid.update()
        try:
            self.grid.shapes_changed.emit()
        except Exception:
            pass

    def new_glue(self):
        self.grid.save_state()
        g = GlueTab()
        self.grid.glue_tabs[g.id] = g
        self.current_glue = g.id
        self.grid.selected_glue_id = g.id
        self.grid.current_mode = 'glue'
        QMessageBox.information(self, "Glue", "Drag to create glue tab.")
        self.grid.update()

    def delete_glue(self):
        gid = self.grid.selected_glue_id or self.current_glue
        if gid and gid in self.grid.glue_tabs:
            self.grid.save_state()
            g = self.grid.glue_tabs.pop(gid)
        self.grid.selected_glue_id = None
        self.grid.update()
        try:
            self.grid.shapes_changed.emit()
        except Exception:
            pass

    def delete_selected_segment(self):
        item = self.tree.currentItem()
        if not item: return
        parent = item.parent()
        if parent is None: return
        seg_id = item.data(0, Qt.UserRole)
        if seg_id:
            self.grid.delete_segment_by_id(seg_id)

    def edit_selected_segment(self):
        item = self.tree.currentItem()
        if not item: return
        parent = item.parent()
        if parent is None: return
        seg_id = item.data(0, Qt.UserRole)
        if seg_id:
            self.grid.edit_segment_by_id(seg_id)

    def export_txt(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export TXT", filter="Text Files (*.txt)")
        if not path: return
        # Collect all coordinates (in pixels) to compute origin offset
        xs, ys = [], []
        for shp in self.grid.shapes.values():
            for seg in shp.lines:
                xs += [seg.a.x(), seg.b.x()]
                ys += [seg.a.y(), seg.b.y()]
        for glue in self.grid.glue_tabs.values():
            if glue.a and glue.b:
                xs += [glue.a.x(), glue.b.x()]
                ys += [glue.a.y(), glue.b.y()]

        minx, maxy = (min(xs), max(ys)) if xs and ys else (0, 0)

        # Helper: coordinates are stored in world units (mm); return mm relative to bottom-left origin
        def px_to_mm_tuple(px, py):
            # px,py are world coords in mm. Origin should be bottom-left: x relative to minx, y relative to maxy
            return (round((px - minx), 3), round((maxy - py), 3))


        out_lines = []
        out_lines.append("SHAPES:")
        # Export all regular shapes first: collect unique vertices per shape (deduplicate endpoints)
        for name, shp in self.grid.shapes.items():
            verts = []
            seen = set()
            for seg in shp.lines:
                for pt in (seg.a, seg.b):
                    key = (pt.x(), pt.y())
                    if key not in seen:
                        seen.add(key)
                        verts.append(px_to_mm_tuple(pt.x(), pt.y()))
            out_lines.append(f"{name}: {verts}")

        # composites feature removed

        out_lines.append("\nGLUE_TABS:")
        for gid, g in self.grid.glue_tabs.items():
            if g.a and g.b:
                a_mm = px_to_mm_tuple(g.a.x(), g.a.y())
                b_mm = px_to_mm_tuple(g.b.x(), g.b.y())
                out_lines.append(f"{gid}: ({a_mm}, {b_mm})")

        with open(path, 'w') as f:
            f.write("\n".join(out_lines))
        QMessageBox.information(self, "Export", f"Saved to {path}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Shape Editor v3")
        self.resize(1100, 700)
        self.grid = GridWidget()
        self.sidebar = Sidebar(self.grid)
        central = QWidget(); lay = QHBoxLayout(central)
        lay.addWidget(self.sidebar, 2); lay.addWidget(self.grid, 6)
        self.setCentralWidget(central)
        self.create_menus()

    def create_menus(self):
        """Creates the main menu bar with an Edit menu for Undo/Redo."""
        menu_bar = self.menuBar()
        edit_menu = menu_bar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)  # Ctrl+Z
        undo_action.triggered.connect(self.grid.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.Redo)  # Ctrl+Y or Ctrl+Shift+Z
        redo_action.triggered.connect(self.grid.redo)
        edit_menu.addAction(redo_action)

        # Connect the grid's history signal to update menu item state
        self.grid.history_changed.connect(
            lambda: undo_action.setEnabled(bool(self.grid.undo_stack))
        )
        self.grid.history_changed.connect(
            lambda: redo_action.setEnabled(bool(self.grid.redo_stack))
        )
        # Set initial state
        undo_action.setEnabled(False)
        redo_action.setEnabled(False)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec_())