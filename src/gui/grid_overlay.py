import logging
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor

logger = logging.getLogger(__name__)

class GridOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []  # List of (x, y) coordinates in image space
        self.grid_points = None  # 2D array of grid points in image space
        self.rows = 4
        self.cols = 4
        self.is_visible = False
        
        # Set up the widget
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
    
    def set_points(self, points):
        """Set the corner points and generate the grid."""
        self.points = points
        if len(points) == 4:
            self._generate_grid()
        else:
            self.grid_points = None
        self.update()
    
    def set_grid_size(self, rows, cols):
        """Set the grid size and regenerate the grid."""
        self.rows = rows
        self.cols = cols
        if len(self.points) == 4:
            self._generate_grid()
        self.update()
    
    def show_grid(self, show=True):
        """Show or hide the grid."""
        self.is_visible = show
        self.update()
    
    def _generate_grid(self):
        """Generate grid points based on corner points."""
        try:
            if len(self.points) != 4:
                return
            
            # Convert QPointF points to numpy array
            corners = np.array([[p.x(), p.y()] for p in self.points])
            
            # Create arrays of interpolation parameters
            rows = np.linspace(0, 1, self.rows)
            cols = np.linspace(0, 1, self.cols)
            
            # Initialize grid points array
            self.grid_points = np.zeros((self.rows, self.cols, 2))
            
            # Generate grid points using bilinear interpolation
            for i, r in enumerate(rows):
                for j, c in enumerate(cols):
                    # Interpolate between corners
                    p1 = corners[0] * (1 - r) * (1 - c)
                    p2 = corners[1] * (1 - r) * c
                    p3 = corners[2] * r * c
                    p4 = corners[3] * r * (1 - c)
                    
                    self.grid_points[i, j] = p1 + p2 + p3 + p4
            
            logger.info(f"Generated grid with {self.rows}x{self.cols} points")
        except Exception as e:
            logger.error(f"Error generating grid: {e}")
            self.grid_points = None
    
    def paintEvent(self, event):
        """Handle paint events."""
        if not self.is_visible or self.grid_points is None:
            return
        
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Draw grid lines
            pen = QPen(QColor(255, 255, 0, 128))  # Semi-transparent yellow
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setWidth(2)
            painter.setPen(pen)
            
            # Get the image view for coordinate mapping
            image_view = self.parent()
            if not image_view:
                return
            
            # Draw horizontal lines
            for i in range(self.rows):
                for j in range(self.cols - 1):
                    # Convert image coordinates to viewport coordinates
                    p1 = image_view.map_to_viewport(QPointF(self.grid_points[i, j, 0], self.grid_points[i, j, 1]))
                    p2 = image_view.map_to_viewport(QPointF(self.grid_points[i, j + 1, 0], self.grid_points[i, j + 1, 1]))
                    painter.drawLine(p1, p2)
            
            # Draw vertical lines
            for j in range(self.cols):
                for i in range(self.rows - 1):
                    # Convert image coordinates to viewport coordinates
                    p1 = image_view.map_to_viewport(QPointF(self.grid_points[i, j, 0], self.grid_points[i, j, 1]))
                    p2 = image_view.map_to_viewport(QPointF(self.grid_points[i + 1, j, 0], self.grid_points[i + 1, j, 1]))
                    painter.drawLine(p1, p2)
            
            # Draw grid points
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setColor(QColor(255, 255, 0, 200))  # More opaque yellow
            painter.setPen(pen)
            
            for i in range(self.rows):
                for j in range(self.cols):
                    # Convert image coordinates to viewport coordinates
                    point = image_view.map_to_viewport(QPointF(self.grid_points[i, j, 0], self.grid_points[i, j, 1]))
                    painter.drawEllipse(point, 3, 3)
        except Exception as e:
            logger.error(f"Error in paint event: {e}")
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        if len(self.points) == 4:
            self._generate_grid()
        self.update() 