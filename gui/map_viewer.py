import os
from PySide6.QtWidgets import (QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, 
                             QGraphicsEllipseItem, QGraphicsTextItem, QGraphicsItem)
from PySide6.QtCore import Qt, QRectF, Signal, QObject, QTimer
from PySide6.QtGui import QPixmap, QColor, QPen, QBrush, QPainter, QFont

class ClickableScene(QGraphicsScene):
    point_clicked = Signal(int)

class MapPoint(QGraphicsEllipseItem):
    def __init__(self, x, y, number, description="", parent=None):
        self.radius = 18 
        super().__init__(-self.radius, -self.radius, self.radius*2, self.radius*2)
        self.setPos(x, y)
        self.number = number
        self.description = description
        self.setAcceptHoverEvents(True)
        
        # Flags
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(10)
        
        # Appearance
        self.idle_brush = QBrush(QColor(0, 124, 145, 30))
        self.hover_brush = QBrush(QColor(0, 124, 145, 100))
        self.calib_brush = QBrush(QColor(255, 165, 0, 120))
        self.pen_idle = QPen(QColor(0, 124, 145), 1)
        self.pen_calib = QPen(QColor(255, 140, 0), 2)
        
        self.setBrush(self.idle_brush)
        self.setPen(self.pen_idle)
        self.setCursor(Qt.PointingHandCursor)
        
        # Visible Number
        self.label = QGraphicsTextItem(str(number), self)
        self.label.setDefaultTextColor(Qt.black)
        font = QFont("Segoe UI", 9, QFont.Bold)
        self.label.setFont(font)
        
        # Center the label
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width()/2, -rect.height()/2)
        
        self.update_tooltip()

    def update_tooltip(self):
        text = f"POSIZIONE {self.number}"
        if self.description:
            text += f"\n{self.description}"
        self.setToolTip(text)

    def set_calibration_style(self, enabled):
        self.setFlag(QGraphicsItem.ItemIsMovable, enabled)
        if enabled:
            self.setBrush(self.calib_brush)
            self.setPen(self.pen_calib)
            self.label.setDefaultTextColor(Qt.white)
        else:
            self.setBrush(self.idle_brush)
            self.setPen(self.pen_idle)
            self.label.setDefaultTextColor(Qt.black)

    def hoverEnterEvent(self, event):
        if not self.flags() & QGraphicsItem.ItemIsMovable:
            self.setBrush(self.hover_brush)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        if not self.flags() & QGraphicsItem.ItemIsMovable:
            self.setBrush(self.idle_brush)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Se è abilitato ItemIsMovable (siamo in calibrazione), permettiamo il drag.
            # Altrimenti (operazione), emettiamo il click per la distinta.
            if not (self.flags() & QGraphicsItem.ItemIsMovable):
                scene = self.scene()
                if isinstance(scene, ClickableScene):
                    scene.point_clicked.emit(self.number)
                    return # Blocca il propagarsi dell'evento così non draga
        
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # Permette di emettere il ricalcolo coordinate se spostato
        super().mouseReleaseEvent(event)

class ProductMapView(QGraphicsView):
    componentSelected = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._clickable_scene = ClickableScene(self)
        self._clickable_scene.point_clicked.connect(self.on_point_clicked)
        self.setScene(self._clickable_scene)
        
        # Rendering Quality
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # Interaction Modes
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse) # Essential for zoom
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setAlignment(Qt.AlignCenter)
        
        self.pixmap_item = None
        self._zoom_level = 0
        self._calibration_mode = False
        self._is_panning = False
        self._last_mouse_pos = None
        self._first_resize = True

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._first_resize and self.pixmap_item and self.width() > 100:
            # Increased delay to 300ms for high reliability on Windows window managers
            QTimer.singleShot(300, self.reset_view)
            self._first_resize = False

    def set_calibration_mode(self, enabled):
        self._calibration_mode = enabled
        for item in self._clickable_scene.items():
            if isinstance(item, MapPoint):
                item.set_calibration_style(enabled)
        
        # In calibration mode, we disable ScrollHandDrag (Left-click) to allow dragging points.
        # But we still support Right-Click panning.
        if enabled:
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        # Allow panning with RIGHT BUTTON always
        if event.button() == Qt.RightButton:
            self._is_panning = True
            self._last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.pos() - self._last_mouse_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._last_mouse_pos = event.pos()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor if self._calibration_mode else Qt.OpenHandCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def load_image(self, path):
        if not os.path.exists(path):
            print(f"Errore: {path} non trovato")
            return
            
        pixmap = QPixmap(path)
        if self.pixmap_item:
            self._clickable_scene.removeItem(self.pixmap_item)
            
        self.pixmap_item = self._clickable_scene.addPixmap(pixmap)
        self.pixmap_item.setZValue(-1)
        self._clickable_scene.setSceneRect(QRectF(pixmap.rect()))
        
        self.reset_view()

    def reset_view(self):
        if self.pixmap_item:
            self._clickable_scene.setSceneRect(self.pixmap_item.boundingRect())
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
            self._zoom_level = 0

    def add_point(self, x, y, number, description=""):
        point = MapPoint(x, y, number, description)
        point.set_calibration_style(self._calibration_mode)
        self._clickable_scene.addItem(point)

    def get_all_points(self):
        points = []
        for item in self._clickable_scene.items():
            if isinstance(item, MapPoint):
                points.append([round(item.pos().x()), round(item.pos().y()), item.number])
        # Sort by number for clean JSON
        points.sort(key=lambda x: x[2])
        return points

    def on_point_clicked(self, number):
        self.componentSelected.emit(number)
        
    def wheelEvent(self, event):
        # Professional Zoom Logic
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            if self._zoom_level < 15: # Cap zoom in
                self.scale(zoom_in_factor, zoom_in_factor)
                self._zoom_level += 1
        else:
            if self._zoom_level > -5: # Cap zoom out
                self.scale(zoom_out_factor, zoom_out_factor)
                self._zoom_level -= 1
