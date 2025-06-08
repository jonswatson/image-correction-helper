import logging
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor

logger = logging.getLogger(__name__)

class PointSelector(QWidget):
    # Define signals
    point_added = pyqtSignal(int, QPointF)  # Emits (index, point)
    point_removed = pyqtSignal(int)  # Emits index
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []  # List of QPointF coordinates
        self.dragging_point = None
        self.drag_start = None
        self.hover_point = None
        self.is_selecting = False
        self.is_locked = False  # New flag for transform preview state
        
        # Set up the widget
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.raise_()  # Ensure widget is on top
    
    def start_selection(self):
        """Start point selection mode."""
        self.is_selecting = True
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.raise_()  # Ensure widget is on top
        self.update()
    
    def stop_selection(self):
        """Stop point selection mode."""
        self.is_selecting = False
        self.update()
    
    def get_points(self):
        """Get the current points."""
        return self.points.copy()
    
    def clear_points(self):
        """Clear all points."""
        self.points.clear()
        self.hover_point = None
        self.dragging_point = None
        self.drag_start = None
        self.is_locked = False
        self.is_selecting = True  # Ensure selection is enabled after clearing
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.raise_()  # Ensure widget is on top
        self.update()
    
    def set_locked(self, locked):
        """Set the locked state for transform preview."""
        self.is_locked = locked
        self.update()
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        try:
            # Get the parent ImageView
            image_view = self.parent()
            if not image_view:
                return
            
            # Don't handle point selection if panning is active
            if image_view.is_panning:
                event.ignore()
                return
            
            # Don't handle point selection if locked
            if self.is_locked:
                event.ignore()
                return
            
            # Convert viewport coordinates to image coordinates
            viewport_pos = event.position()
            image_pos = image_view.map_to_image(viewport_pos)
            
            if event.button() == Qt.MouseButton.LeftButton:
                # Check if we're clicking near an existing point
                for i, point in enumerate(self.points):
                    # Convert point to viewport coordinates for hit detection
                    viewport_point = image_view.map_to_viewport(point)
                    if (viewport_point - viewport_pos).manhattanLength() < 10:
                        self.dragging_point = i
                        self.drag_start = image_pos
                        return
                
                # Add new point if not near existing point
                self.points.append(image_pos)
                self.point_added.emit(len(self.points) - 1, image_pos)
                self.update()
            
            elif event.button() == Qt.MouseButton.RightButton:
                # Remove point if right-clicking near it
                for i, point in enumerate(self.points):
                    # Convert point to viewport coordinates for hit detection
                    viewport_point = image_view.map_to_viewport(point)
                    if (viewport_point - viewport_pos).manhattanLength() < 10:
                        self.points.pop(i)
                        self.point_removed.emit(i)
                        self.update()
                        break
        except Exception as e:
            logger.error(f"Error in mouse press event: {e}")
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        try:
            # Get the parent ImageView
            image_view = self.parent()
            if not image_view:
                return
            
            # Don't handle point selection if panning is active
            if image_view.is_panning:
                event.ignore()
                return
            
            # Don't handle point selection if locked
            if self.is_locked:
                event.ignore()
                return
            
            # Convert viewport coordinates to image coordinates
            viewport_pos = event.position()
            image_pos = image_view.map_to_image(viewport_pos)
            
            # Update hover point
            self.hover_point = None
            for i, point in enumerate(self.points):
                # Convert point to viewport coordinates for hit detection
                viewport_point = image_view.map_to_viewport(point)
                if (viewport_point - viewport_pos).manhattanLength() < 10:
                    self.hover_point = i
                    break
            
            # Handle point dragging
            if self.dragging_point is not None:
                self.points[self.dragging_point] = image_pos
                # Emit point added signal to update grid
                self.point_added.emit(self.dragging_point, image_pos)
                self.update()
        except Exception as e:
            logger.error(f"Error in mouse move event: {e}")
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        try:
            if event.button() == Qt.MouseButton.LeftButton:
                if self.dragging_point is not None:
                    # Emit point added signal one final time to ensure grid is updated
                    self.point_added.emit(self.dragging_point, self.points[self.dragging_point])
                self.dragging_point = None
                self.drag_start = None
        except Exception as e:
            logger.error(f"Error in mouse release event: {e}")
    
    def paintEvent(self, event):
        """Handle paint events."""
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Get the image view for coordinate mapping
            image_view = self.parent()
            if not image_view:
                return
            
            # Don't draw points if locked
            if self.is_locked:
                return
            
            # Draw points
            for i, point in enumerate(self.points):
                # Convert image coordinates to viewport coordinates
                viewport_point = image_view.map_to_viewport(point)
                
                # Draw crosshair
                pen = QPen(QColor(255, 255, 0))  # Yellow
                pen.setWidth(2)
                painter.setPen(pen)
                
                size = 15
                
                # Draw crosshair lines
                painter.drawLine(int(viewport_point.x() - size), int(viewport_point.y()),
                               int(viewport_point.x() + size), int(viewport_point.y()))
                painter.drawLine(int(viewport_point.x()), int(viewport_point.y() - size),
                               int(viewport_point.x()), int(viewport_point.y() + size))
                
                # Draw center circle
                painter.drawEllipse(viewport_point, 2, 2)
            
            # Draw hover effect
            if self.hover_point is not None:
                # Convert image coordinates to viewport coordinates
                viewport_point = image_view.map_to_viewport(self.points[self.hover_point])
                
                pen = QPen(QColor(255, 255, 0, 128))  # Semi-transparent yellow
                pen.setWidth(3)
                painter.setPen(pen)
                
                size = 20
                
                # Draw hover circle
                painter.drawEllipse(viewport_point, size, size)
        except Exception as e:
            logger.error(f"Error in paint event: {e}")
    
    def _distance(self, p1, p2):
        """Calculate distance between two points."""
        return ((p1.x() - p2.x()) ** 2 + (p1.y() - p2.y()) ** 2) ** 0.5 