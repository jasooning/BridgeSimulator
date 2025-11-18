"""
Section Builder (PyQt6)

A simplified SkyCiv-style Section Builder implemented with PyQt6.

Features:
- Add Rectangle, Circle, Polygon (click to add vertices)
- Select / move shapes on a canvas
- Tree view showing shapes and composite groups (group/ungroup)
- Property inspector: edit position, rotation, size
- Compute geometric properties (area, centroid, Ixx, Iyy, Ixy)
- Import / Export JSON
- Zoom with mouse wheel

Run:
    pip install PyQt6 numpy
    python section_builder_pyqt6.py

Notes:
- Circles are approximated as polygons for inertia calculations.
- This file targets PyQt6. If you want PyQt5 instead, ask and I'll rewrite.
"""

import sys
import json
import math
from functools import partial

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QTreeWidget, QTreeWidgetItem, QFileDialog,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsPolygonItem, QFormLayout, QDoubleSpinBox,
    QMessageBox
)
from PyQt6.QtGui import QPolygonF, QPen, QBrush, QColor, QTransform, QPainter, QAction
from PyQt6.QtCore import Qt, QPointF, QEvent
import numpy as np

# ---------- Geometry utilities ----------

def polygon_area_centroid_moments(points):
    """Compute area, centroid (cx, cy), and second moments (Ixx, Iyy, Ixy) for a polygon.
    Points: list of (x,y) tuples in order.
    """
    if len(points) < 3:
        return 0.0, (0.0, 0.0), (0.0, 0.0, 0.0)
    pts = np.array(points, dtype=float)
    x = pts[:, 0]
    y = pts[:, 1]
    x2 = np.roll(x, -1)
    y2 = np.roll(y, -1)
    a = x * y2 - x2 * y
    A = 0.5 * a.sum()
    if abs(A) < 1e-9:
        return 0.0, (0.0, 0.0), (0.0, 0.0, 0.0)
    cx = (1.0 / (6.0 * A)) * ((x + x2) * a).sum()
    cy = (1.0 / (6.0 * A)) * ((y + y2) * a).sum()
    Ixx = (1.0 / 12.0) * ((y * y + y * y2 + y2 * y2) * a).sum()
    Iyy = (1.0 / 12.0) * ((x * x + x * x2 + x2 * x2) * a).sum()
    Ixy = (1.0 / 24.0) * ((x * y2 + 2 * x * y + 2 * x2 * y2 + x2 * y) * a).sum()
    if A < 0:
        A = -A
        Ixx = -Ixx
        Iyy = -Iyy
        Ixy = -Ixy
    return A, (cx, cy), (Ixx, Iyy, Ixy)

# ---------- Graphics items for shapes ----------

class BaseShapeItem(QGraphicsItem):
    def __init__(self, name='Shape'):
        super().__init__()
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.name = name
        self.fill = QColor(150, 200, 250, 180)
        self.stroke = QColor(20, 20, 60)
        self.pen = QPen(self.stroke, 1)

    def properties(self):
        return {}

    def to_dict(self):
        return {
            'type': 'base',
            'name': self.name,
            'pos': [self.x(), self.y()],
            'rotation': self.rotation(),
        }

    def from_dict(self, d):
        pos = d.get('pos', [0, 0])
        self.setPos(pos[0], pos[1])
        self.setRotation(d.get('rotation', 0))


class RectangleItem(QGraphicsRectItem, BaseShapeItem):
    def __init__(self, w=100, h=50, name='Rectangle'):
        QGraphicsRectItem.__init__(self, -w/2, -h/2, w, h)
        BaseShapeItem.__init__(self, name)
        self.w = w
        self.h = h
        self.setBrush(QBrush(self.fill))
        self.setPen(self.pen)

    def properties(self):
        return {'width': self.w, 'height': self.h}

    def update_geometry(self):
        self.setRect(-self.w/2, -self.h/2, self.w, self.h)

    def shape_polygon(self):
        r = self.rect()
        pts = [self.mapToScene(QPointF(r.x(), r.y())),
               self.mapToScene(QPointF(r.x()+r.width(), r.y())),
               self.mapToScene(QPointF(r.x()+r.width(), r.y()+r.height())),
               self.mapToScene(QPointF(r.x(), r.y()+r.height()))]
        return [(p.x(), p.y()) for p in pts]

    def to_dict(self):
        d = BaseShapeItem.to_dict(self)
        d.update({'type': 'rectangle', 'w': self.w, 'h': self.h})
        return d

    def from_dict(self, d):
        BaseShapeItem.from_dict(self, d)
        self.w = d.get('w', self.w)
        self.h = d.get('h', self.h)
        self.update_geometry()


class CircleItem(QGraphicsEllipseItem, BaseShapeItem):
    def __init__(self, r=25, name='Circle'):
        QGraphicsEllipseItem.__init__(self, -r, -r, 2*r, 2*r)
        BaseShapeItem.__init__(self, name)
        self.r = r
        self.setBrush(QBrush(self.fill))
        self.setPen(self.pen)

    def properties(self):
        return {'radius': self.r}

    def update_geometry(self):
        self.setRect(-self.r, -self.r, 2*self.r, 2*self.r)

    def shape_polygon(self, n=64):
        pts = []
        for i in range(n):
            theta = 2 * math.pi * i / n
            p = self.mapToScene(QPointF(self.r * math.cos(theta), self.r * math.sin(theta)))
            pts.append((p.x(), p.y()))
        return pts

    def to_dict(self):
        d = BaseShapeItem.to_dict(self)
        d.update({'type': 'circle', 'r': self.r})
        return d

    def from_dict(self, d):
        BaseShapeItem.from_dict(self, d)
        self.r = d.get('r', self.r)
        self.update_geometry()


class PolygonItem(QGraphicsPolygonItem, BaseShapeItem):
    def __init__(self, points=None, name='Polygon'):
        if points is None:
            points = [QPointF(0,0), QPointF(50,0), QPointF(30,40)]
        QGraphicsPolygonItem.__init__(self, QPolygonF(points))
        BaseShapeItem.__init__(self, name)
        self.setBrush(QBrush(self.fill))
        self.setPen(self.pen)

    def to_point_list(self):
        poly = self.polygon()
        pts = []
        for i in range(poly.count()):
            p = self.mapToScene(poly.at(i))
            pts.append((p.x(), p.y()))
        return pts

    def properties(self):
        return {'vertices': self.polygon().count()}

    def to_dict(self):
        d = BaseShapeItem.to_dict(self)
        pts = [(self.mapToScene(p).x(), self.mapToScene(p).y()) for p in self.polygon()]
        d.update({'type': 'polygon', 'points': pts})
        return d

    def from_dict(self, d):
        BaseShapeItem.from_dict(self, d)
        pts = d.get('points', [])
        qpts = [QPointF(x, y) for (x, y) in pts]
        if qpts:
            self.setPolygon(QPolygonF(qpts))

# ---------- Main application window ----------

class SectionBuilderMain(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Section Builder - PyQt6')
        self.resize(1200, 800)
        self.scene = QGraphicsScene(-2000, -2000, 4000, 4000)
        self.view = QGraphicsView(self.scene)
        # enable antialiasing and smooth pixmap transform
        self.view.setRenderHints(self.view.renderHints() | QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.scale = 1.0

        # Left: tree and buttons
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Sections / Shapes'])
        left_layout.addWidget(self.tree)

        btn_add_rect = QPushButton('Add Rectangle')
        btn_add_rect.clicked.connect(self.add_rectangle)
        btn_add_circle = QPushButton('Add Circle')
        btn_add_circle.clicked.connect(self.add_circle)
        btn_add_poly = QPushButton('Start Polygon')
        btn_add_poly.clicked.connect(self.start_polygon_mode)
        btn_group = QPushButton('Group Selected')
        btn_group.clicked.connect(self.group_selected)
        btn_ungroup = QPushButton('Ungroup Selected')
        btn_ungroup.clicked.connect(self.ungroup_selected)
        btn_export = QPushButton('Export JSON')
        btn_export.clicked.connect(self.export_json)
        btn_import = QPushButton('Import JSON')
        btn_import.clicked.connect(self.import_json)
        btn_compute = QPushButton('Compute Properties')
        btn_compute.clicked.connect(self.compute_properties)

        for b in [btn_add_rect, btn_add_circle, btn_add_poly, btn_group, btn_ungroup, btn_export, btn_import, btn_compute]:
            left_layout.addWidget(b)

        # Right: properties
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)

        self.prop_form = QFormLayout()
        self.prop_container = QWidget()
        self.prop_container.setLayout(self.prop_form)
        right_layout.addWidget(QLabel('Properties'))
        right_layout.addWidget(self.prop_container)

        # connect tree selection
        self.tree.itemSelectionChanged.connect(self.on_tree_selection_changed)

        central = QWidget()
        layout = QHBoxLayout()
        central.setLayout(layout)
        layout.addWidget(left_widget, 2)
        layout.addWidget(self.view, 6)
        layout.addWidget(right_widget, 2)
        self.setCentralWidget(central)

        # polygon creation state
        self.creating_polygon = False
        self.current_poly_points = []
        self.temp_poly_item = None

        # scene mouse handling
        self.view.viewport().installEventFilter(self)

        # menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu('File')
        file_menu.addAction(ACTION := QAction('Export JSON', self))
        ACTION.triggered.connect(self.export_json)
        file_menu.addAction(ACTION2 := QAction('Import JSON', self))
        ACTION2.triggered.connect(self.import_json)

        help_menu = menubar.addMenu('Help')
        help_menu.addAction(ACTION3 := QAction('Instructions', self))
        ACTION3.triggered.connect(self.show_help)

    # ---------- Shape creation ----------

    def add_rectangle(self):
        item = RectangleItem(120, 60, name='Rectangle')
        self.scene.addItem(item)
        item.setPos(0, 0)
        self.add_tree_item(item)

    def add_circle(self):
        item = CircleItem(40, name='Circle')
        self.scene.addItem(item)
        item.setPos(0, 0)
        self.add_tree_item(item)

    def start_polygon_mode(self):
        self.creating_polygon = True
        self.current_poly_points = []
        QMessageBox.information(self, 'Polygon mode', 'Click in the canvas to add vertices. Double-click to finish.')

    def finish_polygon(self):
        if len(self.current_poly_points) < 3:
            QMessageBox.warning(self, 'Polygon', 'Need at least 3 points')
            self.cancel_polygon()
            return
        poly_item = PolygonItem(self.current_poly_points, name='Polygon')
        self.scene.addItem(poly_item)
        poly_item.setPos(0, 0)
        self.add_tree_item(poly_item)
        self.cancel_polygon()

    def cancel_polygon(self):
        self.creating_polygon = False
        self.current_poly_points = []
        if self.temp_poly_item:
            self.scene.removeItem(self.temp_poly_item)
            self.temp_poly_item = None

    # ---------- Tree management ----------

    def add_tree_item(self, graphics_item, parent_item=None):
        entry = QTreeWidgetItem([graphics_item.name])
        entry.setData(0, Qt.ItemDataRole.UserRole, graphics_item)
        if parent_item is None:
            self.tree.addTopLevelItem(entry)
        else:
            parent_item.addChild(entry)
        graphics_item.setToolTip(graphics_item.name)
        graphics_item.setSelected(True)

    def group_selected(self):
        selected = self.scene.selectedItems()
        if len(selected) < 2:
            QMessageBox.information(self, 'Grouping', 'Select at least two shapes to group.')
            return
        group = QTreeWidgetItem(['Composite'])
        self.tree.addTopLevelItem(group)
        # naive move: find and re-parent corresponding tree items
        to_move = []
        for i in range(self.tree.topLevelItemCount()):
            t = self.tree.topLevelItem(i)
            to_move.extend(self._collect_graphics_items_from_tree(t))
        for gitem in selected:
            it = self.find_tree_item_for_graphics(gitem)
            if it:
                clone = it.clone()
                group.addChild(clone)
                parent = it.parent()
                if parent:
                    parent.takeChild(parent.indexOfChild(it))
                else:
                    idx = self.tree.indexOfTopLevelItem(it)
                    if idx >= 0:
                        self.tree.takeTopLevelItem(idx)

    def ungroup_selected(self):
        sel = self.tree.selectedItems()
        for s in sel:
            if s.text(0) == 'Composite':
                parent = s.parent()
                while s.childCount() > 0:
                    c = s.child(0)
                    s.removeChild(c)
                    if parent:
                        parent.addChild(c)
                    else:
                        self.tree.addTopLevelItem(c)
                if parent:
                    parent.removeChild(s)
                else:
                    idx = self.tree.indexOfTopLevelItem(s)
                    if idx >= 0:
                        self.tree.takeTopLevelItem(idx)

    def _collect_graphics_items_from_tree(self, node):
        found = []
        if node.data(0, Qt.ItemDataRole.UserRole) is not None:
            found.append(node.data(0, Qt.ItemDataRole.UserRole))
        for i in range(node.childCount()):
            found.extend(self._collect_graphics_items_from_tree(node.child(i)))
        return found

    def find_tree_item_for_graphics(self, gitem):
        def recurse(node):
            for i in range(node.childCount()):
                c = node.child(i)
                if c.data(0, Qt.ItemDataRole.UserRole) is gitem:
                    return c
                res = recurse(c)
                if res:
                    return res
            return None
        for i in range(self.tree.topLevelItemCount()):
            t = self.tree.topLevelItem(i)
            if t.data(0, Qt.ItemDataRole.UserRole) is gitem:
                return t
            res = recurse(t)
            if res:
                return res
        return None

    # ---------- Import/Export ----------

    def export_json(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Export JSON', filter='JSON files (*.json)')
        if not path:
            return
        data = []
        for i in range(self.tree.topLevelItemCount()):
            t = self.tree.topLevelItem(i)
            self._gather_tree_item(t, data)
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        QMessageBox.information(self, 'Export', f'Exported {len(data)} items to {path}')

    def _gather_tree_item(self, tree_item, collector):
        g = tree_item.data(0, Qt.ItemDataRole.UserRole)
        if g is not None:
            if isinstance(g, RectangleItem):
                collector.append(g.to_dict())
            elif isinstance(g, CircleItem):
                collector.append(g.to_dict())
            elif isinstance(g, PolygonItem):
                collector.append(g.to_dict())
            else:
                collector.append(g.to_dict())
        for i in range(tree_item.childCount()):
            self._gather_tree_item(tree_item.child(i), collector)

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Import JSON', filter='JSON files (*.json)')
        if not path:
            return
        with open(path, 'r') as f:
            data = json.load(f)
        self.scene.clear()
        self.tree.clear()
        for d in data:
            t = d.get('type')
            if t == 'rectangle':
                it = RectangleItem(d.get('w', 100), d.get('h', 50), name=d.get('name', 'Rectangle'))
                it.from_dict(d)
                self.scene.addItem(it)
                self.add_tree_item(it)
            elif t == 'circle':
                it = CircleItem(d.get('r', 30), name=d.get('name', 'Circle'))
                it.from_dict(d)
                self.scene.addItem(it)
                self.add_tree_item(it)
            elif t == 'polygon':
                pts = d.get('points', [])
                qpts = [QPointF(x, y) for (x, y) in pts]
                it = PolygonItem(qpts, name=d.get('name', 'Polygon'))
                it.from_dict(d)
                self.scene.addItem(it)
                self.add_tree_item(it)

    # ---------- Compute properties ----------

    def compute_properties(self):
        sel = self.scene.selectedItems()
        if not sel:
            QMessageBox.information(self, 'Compute', 'Select a shape or shapes')
            return
        polys = []
        for s in sel:
            if isinstance(s, RectangleItem):
                polys.append(s.shape_polygon())
            elif isinstance(s, CircleItem):
                polys.append(s.shape_polygon())
            elif isinstance(s, PolygonItem):
                polys.append(s.to_point_list())
        total_area = 0.0
        cx_num = 0.0
        cy_num = 0.0
        Ixx_total = 0.0
        Iyy_total = 0.0
        Ixy_total = 0.0
        for p in polys:
            A, (cx, cy), (Ixx, Iyy, Ixy) = polygon_area_centroid_moments(p)
            total_area += A
            cx_num += A * cx
            cy_num += A * cy
            Ixx_total += Ixx + A * (cy**2)
            Iyy_total += Iyy + A * (cx**2)
            Ixy_total += Ixy + A * (cx * cy)
        if total_area == 0:
            QMessageBox.warning(self, 'Compute', 'Zero total area')
            return
        cx = cx_num / total_area
        cy = cy_num / total_area
        msg = f'Total Area: {total_area:.3f}\nCentroid: ({cx:.3f}, {cy:.3f})\nIxx: {Ixx_total:.3f}\nIyy: {Iyy_total:.3f}\nIxy: {Ixy_total:.3f}'
        QMessageBox.information(self, 'Properties', msg)

    # ---------- Selection handling & properties panel ----------

    def on_tree_selection_changed(self):
        items = self.tree.selectedItems()
        if not items:
            self.clear_properties()
            return
        tree_item = items[0]
        g = tree_item.data(0, Qt.ItemDataRole.UserRole)
        if g is None:
            self.clear_properties()
            return
        self.show_properties_for(g)

    def clear_properties(self):
        while self.prop_form.rowCount():
            self.prop_form.removeRow(0)

    def show_properties_for(self, g):
        self.clear_properties()
        xpos = QDoubleSpinBox(); xpos.setRange(-10000, 10000); xpos.setValue(g.x())
        ypos = QDoubleSpinBox(); ypos.setRange(-10000, 10000); ypos.setValue(g.y())
        rot = QDoubleSpinBox(); rot.setRange(-360, 360); rot.setValue(g.rotation())
        xpos.valueChanged.connect(lambda v: g.setX(v))
        ypos.valueChanged.connect(lambda v: g.setY(v))
        rot.valueChanged.connect(lambda v: g.setRotation(v))
        self.prop_form.addRow('X', xpos)
        self.prop_form.addRow('Y', ypos)
        self.prop_form.addRow('Rotation', rot)
        if isinstance(g, RectangleItem):
            w = QDoubleSpinBox(); w.setRange(0.1, 10000); w.setValue(g.w)
            h = QDoubleSpinBox(); h.setRange(0.1, 10000); h.setValue(g.h)
            w.valueChanged.connect(lambda v: setattr(g, 'w', v) or g.update_geometry())
            h.valueChanged.connect(lambda v: setattr(g, 'h', v) or g.update_geometry())
            self.prop_form.addRow('Width', w)
            self.prop_form.addRow('Height', h)
        elif isinstance(g, CircleItem):
            r = QDoubleSpinBox(); r.setRange(0.1, 10000); r.setValue(g.r)
            r.valueChanged.connect(lambda v: setattr(g, 'r', v) or g.update_geometry())
            self.prop_form.addRow('Radius', r)
        elif isinstance(g, PolygonItem):
            verts = len(g.polygon())
            self.prop_form.addRow('Vertices', QLabel(str(verts)))

    # ---------- Event filter to capture canvas clicks for polygon creation ----------

    def eventFilter(self, watched, event):
        if watched is self.view.viewport():
            if event.type() == QEvent.Type.MouseButtonPress:
                pos = self.view.mapToScene(event.pos())
                if self.creating_polygon:
                    self.current_poly_points.append(QPointF(pos))
                    if self.temp_poly_item:
                        self.scene.removeItem(self.temp_poly_item)
                    if len(self.current_poly_points) >= 2:
                        self.temp_poly_item = QGraphicsPolygonItem(QPolygonF(self.current_poly_points))
                        self.temp_poly_item.setPen(QPen(Qt.PenStyle.DashLine))
                        self.scene.addItem(self.temp_poly_item)
                    return True
            elif event.type() == QEvent.Type.MouseButtonDblClick:
                if self.creating_polygon:
                    self.finish_polygon()
                    return True
            elif event.type() == QEvent.Type.Wheel:
                delta = event.angleDelta().y()
                factor = 1.0 + (delta / 1200.0)
                self.scale *= factor
                self.view.scale(factor, factor)
                return True
        return False

    def show_help(self):
        text = (
            "Instructions:\n"
            "- Use 'Add Rectangle' / 'Add Circle' to add shapes.\n"
            "- Start Polygon and click on the canvas to add vertices; double-click to finish.\n"
            "- Select shapes on the canvas or in the left tree.\n"
            "- Use properties panel to edit position, rotation, and size.\n"
            "- Group/Ungroup to create composite entries in the tree.\n"
            "- Compute Properties to calculate area, centroid, and moments for selected items.\n"
            "- Export/Import JSON to save or load sections.\n"
        )
        QMessageBox.information(self, 'Help', text)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = SectionBuilderMain()
    win.show()
    sys.exit(app.exec())