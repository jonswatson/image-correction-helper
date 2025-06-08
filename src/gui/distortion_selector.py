import logging
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor

logger = logging.getLogger(__name__)

class DistortionSelector(QWidget):
    # Define signals
    point_added = pyqtSignal(QPointF, QPointF)  # Emits (point, grid_point)
    point_removed = pyqtSignal(QPointF)  # Emits point
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []  # List of QPointF coordinates
        self.grid_points = None  # 2D array of grid points
        self.hover_point = None
        self.is_active = False
        
        # Set up the widget
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.raise_()  # Ensure widget is on top
        
        # Set widget to be transparent but still receive events
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def set_active(self, active):
        """Set the active state."""
        self.is_active = active
        if active:
            self.raise_()  # Ensure widget is on top when active
        self.update()
    
    def set_grid_points(self, grid_points):
        """Set the grid points for matching."""
        self.grid_points = grid_points
        self.update()
    
    def _find_nearest_grid_point(self, point):
        """Find the nearest grid point to the given point."""
        if self.grid_points is None:
            return None
        
        # Flatten grid points to 2D array
        flat_points = self.grid_points.reshape(-1, 2)
        
        # Convert QPointF to numpy array
        point_array = np.array([point.x(), point.y()])
        
        # Calculate distances to all grid points
        distances = np.linalg.norm(flat_points - point_array, axis=1)
        
        # Find nearest point
        nearest_idx = np.argmin(distances)
        nearest_point = flat_points[nearest_idx]
        
        return QPointF(nearest_point[0], nearest_point[1])
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        try:
            if not self.is_active:
                event.ignore()
                return
            
            # Get the parent ImageView
            image_view = self.parent()
            if not image_view:
                return
            
            # Convert viewport coordinates to image coordinates
            viewport_pos = event.position()
            image_pos = image_view.map_to_image(viewport_pos)
            
            if event.button() == Qt.MouseButton.LeftButton:
                # Find nearest grid point
                grid_point = self._find_nearest_grid_point(image_pos)
                if grid_point:
                    # Add point
                    self.points.append(image_pos)
                    self.point_added.emit(image_pos, grid_point)
                    self.update()
                    event.accept()
                else:
                    event.ignore()
            elif event.button() == Qt.MouseButton.RightButton:
                # Remove point if right-clicking near it
                for i, point in enumerate(self.points):
                    # Convert point to viewport coordinates for hit detection
                    viewport_point = image_view.map_to_viewport(point)
                    if (viewport_point - viewport_pos).manhattanLength() < 10:
                        removed_point = self.points.pop(i)
                        self.point_removed.emit(removed_point)
                        self.update()
                        event.accept()
                        break
                else:
                    event.ignore()
        except Exception as e:
            logger.error(f"Error in mouse press event: {e}")
            event.ignore()
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        try:
            if not self.is_active:
                event.ignore()
                return
            
            # Get the parent ImageView
            image_view = self.parent()
            if not image_view:
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
            
            self.update()
            event.accept()
        except Exception as e:
            logger.error(f"Error in mouse move event: {e}")
            event.ignore()
    
    def paintEvent(self, event):
        """Handle paint events."""
        try:
            if not self.is_active:
                return
            
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Get the parent ImageView
            image_view = self.parent()
            if not image_view:
                return
            
            # Draw points
            for i, point in enumerate(self.points):
                # Convert image coordinates to viewport coordinates
                viewport_point = image_view.map_to_viewport(point)
                
                # Draw point
                pen = QPen(QColor(0, 0, 255))  # Blue
                pen.setWidth(2)
                painter.setPen(pen)
                
                size = 10
                painter.drawEllipse(viewport_point, size, size)
            
            # Draw hover effect
            if self.hover_point is not None:
                # Convert image coordinates to viewport coordinates
                viewport_point = image_view.map_to_viewport(self.points[self.hover_point])
                
                pen = QPen(QColor(0, 0, 255, 128))  # Semi-transparent blue
                pen.setWidth(3)
                painter.setPen(pen)
                
                size = 15
                painter.drawEllipse(viewport_point, size, size)
        except Exception as e:
            logger.error(f"Error in paint event: {e}")
    
    def get_points(self):
        """Get the current points."""
        return self.points.copy()
    
    def clear_points(self):
        """Clear all points."""
        self.points.clear()
        self.hover_point = None
        self.update() 