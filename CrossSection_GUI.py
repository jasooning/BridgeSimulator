# shape_editor_v3.py
# unified composite/shape hierarchy + grid + delete buttons + export
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QFileDialog, QLabel, QMessageBox, QTreeWidget, QTreeWidgetItem
)
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QPoint, QRectF

# Grid and drawing constants
# We want the spacing between each grid point to be 5 mm. Screens are measured in pixels;
# to map millimeters to pixels we assume a common desktop DPI of 96 (pixels/inch).
# px_per_mm = DPI / 25.4. If you need a different DPI, change DPI value below.
DPI = 96.0
MM_PER_GRID = 5.0
PX_PER_MM = DPI / 25.4
GRID_SIZE = int(round(MM_PER_GRID * PX_PER_MM))  # pixels per grid step (approx for 5 mm)
LINE_WIDTH = 4
BTN_SIZE = 18

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

class CompositeObj:
    def __init__(self, name):
        self.name = name
        self.children: list[str] = []  # names of shapes or composites

class GlueTab:
    def __init__(self, a: QPoint=None, b: QPoint=None):
        self.a = a
        self.b = b
        self.id = id(self)

class GridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.shapes: dict[str, ShapeObj] = {}
        self.composites: dict[str, CompositeObj] = {}
        self.glue_tabs: dict[int, GlueTab] = {}
        self.current_mode = 'shape'
        self.selected_shape: str | None = None
        self.selected_glue_id: int | None = None
        self.dragging = False
        self.drag_start: QPoint | None = None
        self.delete_buttons: dict[int, QPushButton] = {}
        self.setMouseTracking(True)

    def snap(self, p: QPoint) -> QPoint:
        """Snap a QPoint to the nearest grid intersection (grid defined by GRID_SIZE pixels).

        Note: GRID_SIZE is computed from MM_PER_GRID and PX_PER_MM so this implements a
        ~5 mm spacing between grid points (in pixels).
        """
        return QPoint(round(p.x()/GRID_SIZE)*GRID_SIZE, round(p.y()/GRID_SIZE)*GRID_SIZE)

    def paintEvent(self, e):
        p = QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(QRectF(0,0,w,h), QColor(255,255,255))

        pen = QPen(QColor(230,230,230), 1)
        p.setPen(pen)
        for x in range(0, w, GRID_SIZE): p.drawLine(x, 0, x, h)
        for y in range(0, h, GRID_SIZE): p.drawLine(0, y, w, y)

        for shp in self.shapes.values():
            pen = QPen(shp.color, LINE_WIDTH)
            p.setPen(pen)
            for seg in shp.lines:
                p.drawLine(seg.a, seg.b)

        pen = QPen(QColor(0,120,0), LINE_WIDTH, Qt.DashLine)
        p.setPen(pen)
        for glue in self.glue_tabs.values():
            if glue.a and glue.b: p.drawLine(glue.a, glue.b)

        if self.dragging and self.drag_start:
            pos = self.mapFromGlobal(self.cursor().pos())
            snap_pos = self.snap(pos)
            pen = QPen(QColor(0,0,0), LINE_WIDTH, Qt.DotLine)
            p.setPen(pen)
            p.drawLine(self.drag_start, snap_pos)
        p.end()
        self.update_delete_buttons()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            pt = self.snap(ev.pos())
            if ev.modifiers() & Qt.ShiftModifier:
                self.delete_nearest_segment(ev.pos()); return
            if self.current_mode == 'shape' and self.selected_shape:
                self.dragging = True; self.drag_start = pt
            elif self.current_mode == 'glue' and self.selected_glue_id is not None:
                self.dragging = True; self.drag_start = pt

    def mouseMoveEvent(self, ev):
        if self.dragging: self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.LeftButton and self.dragging and self.drag_start:
            end = self.snap(ev.pos())
            if end != self.drag_start:
                if self.current_mode == 'shape' and self.selected_shape:
                    shp = self.shapes.get(self.selected_shape)
                    if shp: shp.lines.append(LineSeg(self.drag_start, end))
                elif self.current_mode == 'glue' and self.selected_glue_id is not None:
                    glue = self.glue_tabs.get(self.selected_glue_id)
                    if glue: glue.a, glue.b = self.drag_start, end
            self.dragging = False; self.drag_start = None; self.update()

    def delete_nearest_segment(self, pos):
        best, best_d, owner, owner_type = None, 9999, None, None
        for name, shp in self.shapes.items():
            for seg in shp.lines:
                d = self._point_seg_dist(pos, seg.a, seg.b)
                if d < best_d: best_d, best, owner, owner_type = d, seg, name, 'shape'
        for gid, glue in self.glue_tabs.items():
            if glue.a and glue.b:
                d = self._point_seg_dist(pos, glue.a, glue.b)
                if d < best_d: best_d, best, owner, owner_type = d, glue, gid, 'glue'
        if best and best_d < 12:
            if owner_type == 'shape':
                self.shapes[owner].lines = [s for s in self.shapes[owner].lines if s.id != best.id]
            else:
                del self.glue_tabs[owner]
            self.update()

    def _point_seg_dist(self, p, a, b):
        px, py, x1, y1, x2, y2 = p.x(), p.y(), a.x(), a.y(), b.x(), b.y()
        dx, dy = x2-x1, y2-y1
        if dx==0 and dy==0: return ((px-x1)**2+(py-y1)**2)**0.5
        t = ((px-x1)*dx+(py-y1)*dy)/(dx*dx+dy*dy)
        t = max(0, min(1, t))
        projx, projy = x1+t*dx, y1+t*dy
        return ((px-projx)**2+(py-projy)**2)**0.5

    def update_delete_buttons(self):
        existing_ids = {seg.id for shp in self.shapes.values() for seg in shp.lines} | {g.id for g in self.glue_tabs.values()}
        for bid in list(self.delete_buttons.keys()):
            if bid not in existing_ids:
                b = self.delete_buttons.pop(bid); b.setParent(None); b.deleteLater()
        for shp in self.shapes.values():
            for seg in shp.lines:
                self._ensure_button_for(seg, 'shape', shp.name)
        for gid, glue in self.glue_tabs.items():
            if glue.a and glue.b:
                self._ensure_button_for(glue, 'glue', gid)

    def _ensure_button_for(self, seg, owner_type, owner):
        mid = QPoint((seg.a.x()+seg.b.x())//2, (seg.a.y()+seg.b.y())//2)
        if seg.id in self.delete_buttons:
            self.delete_buttons[seg.id].move(mid.x()-BTN_SIZE//2, mid.y()-BTN_SIZE//2)
            return
        btn = QPushButton("✕", self)
        btn.setFixedSize(BTN_SIZE, BTN_SIZE)
        btn.setStyleSheet("background:rgba(255,200,200,180);font-weight:bold;")
        btn.move(mid.x()-BTN_SIZE//2, mid.y()-BTN_SIZE//2)
        if owner_type == 'shape':
            btn.clicked.connect(lambda _, s=seg, n=owner: self._del_seg(s,n))
        else:
            btn.clicked.connect(lambda _, g=owner: self._del_glue(g))
        btn.show()
        self.delete_buttons[seg.id] = btn

    def _del_seg(self, seg, shape_name):
        shp = self.shapes.get(shape_name)
        if shp: shp.lines = [s for s in shp.lines if s.id != seg.id]
        if seg.id in self.delete_buttons:
            b = self.delete_buttons.pop(seg.id); b.setParent(None); b.deleteLater()
        self.update()

    def _del_glue(self, gid):
        if gid in self.glue_tabs:
            g = self.glue_tabs.pop(gid)
            if g.id in self.delete_buttons:
                b = self.delete_buttons.pop(g.id); b.setParent(None); b.deleteLater()
            self.update()

class Sidebar(QWidget):
    def __init__(self, grid: GridWidget):
        super().__init__()
        self.grid = grid
        self.layout = QVBoxLayout(self)

        self.layout.addWidget(QLabel("Shapes / Composites"))
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.itemClicked.connect(self.on_click)
        self.layout.addWidget(self.tree)

        btns = QHBoxLayout()
        nb = QPushButton("New Shape"); nb.clicked.connect(self.new_shape); btns.addWidget(nb)
        nc = QPushButton("New Composite"); nc.clicked.connect(self.new_comp); btns.addWidget(nc)
        nd = QPushButton("Delete"); nd.clicked.connect(self.delete_selected); btns.addWidget(nd)
        self.layout.addLayout(btns)

        self.layout.addWidget(QLabel("Glue Tabs"))
        gbtns = QHBoxLayout()
        gg = QPushButton("New Glue"); gg.clicked.connect(self.new_glue); gbtns.addWidget(gg)
        gd = QPushButton("Delete Glue"); gd.clicked.connect(self.delete_glue); gbtns.addWidget(gd)
        self.layout.addLayout(gbtns)

        exp = QPushButton("Export TXT"); exp.clicked.connect(self.export_txt); self.layout.addWidget(exp)
        self.layout.addStretch()

        self.current_glue = None

    def new_shape(self):
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

    def new_comp(self):
        name = f"Composite_{len(self.grid.composites)+1}"
        comp = CompositeObj(name)
        self.grid.composites[name] = comp
        item = QTreeWidgetItem([name])
        item.setForeground(0, QColor(0,0,180))
        self.tree.addTopLevelItem(item)
        self.grid.update()

    def on_click(self, item):
        name = item.text(0)
        if name in self.grid.shapes:
            self.grid.selected_shape = name
            self.grid.current_mode = 'shape'
        elif name in self.grid.composites:
            self.grid.selected_shape = None
            self.grid.current_mode = ''
        self.grid.update()

    def delete_selected(self):
        item = self.tree.currentItem()
        if not item: return
        name = item.text(0)
        if name in self.grid.shapes:
            shp = self.grid.shapes.pop(name)
            for seg in shp.lines:
                if seg.id in self.grid.delete_buttons:
                    b = self.grid.delete_buttons.pop(seg.id)
                    b.setParent(None); b.deleteLater()
        elif name in self.grid.composites:
            del self.grid.composites[name]
        idx = self.tree.indexOfTopLevelItem(item)
        if idx >= 0: self.tree.takeTopLevelItem(idx)
        self.grid.update()

    def new_glue(self):
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
            g = self.grid.glue_tabs.pop(gid)
            if g.id in self.grid.delete_buttons:
                b = self.grid.delete_buttons.pop(g.id); b.setParent(None); b.deleteLater()
        self.grid.selected_glue_id = None
        self.grid.update()

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

        minx, miny = (min(xs), min(ys)) if xs and ys else (0, 0)

        # Helper: convert pixel value (relative to minx/miny) to mm using PX_PER_MM
        def px_to_mm_tuple(px, py):
            return (round((px - minx) / PX_PER_MM, 3), round((py - miny) / PX_PER_MM, 3))

        out_lines = []
        out_lines.append("SHAPES:")
        # For shapes: output a list of vertex tuples in millimeters (relative to min coords)
        for name, shp in self.grid.shapes.items():
            pts_mm = [px_to_mm_tuple(seg.a.x(), seg.a.y()) for seg in shp.lines]
            out_lines.append(f"{name}: {pts_mm}")

        # For composites: treat a composite like a shape but as a list of lists.
        # Each inner list contains the vertex tuples (in mm) for one child shape.
        out_lines.append("\nCOMPOSITES:")
        for cname, comp in self.grid.composites.items():
            comp_list = []
            for child_name in comp.children:
                child = self.grid.shapes.get(child_name)
                if child:
                    child_pts_mm = [px_to_mm_tuple(seg.a.x(), seg.a.y()) for seg in child.lines]
                    comp_list.append(child_pts_mm)
                else:
                    # If child is missing, include an empty list to preserve indexing
                    comp_list.append([])
            out_lines.append(f"{cname}: {comp_list}")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec_())
