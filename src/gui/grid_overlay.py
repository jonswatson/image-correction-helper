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
        self.distortion_points = []  # List of QPointF coordinates for distortion points
        self.distortion_vectors = []  # List of (point, grid_point) pairs
        
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
    
    def set_distortion_points(self, points, vectors):
        """Set the distortion points and their corresponding grid points."""
        self.distortion_points = points
        self.distortion_vectors = vectors
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
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Get the image view for coordinate mapping
            image_view = self.parent()
            if not image_view:
                return
            
            # Draw grid lines
            if self.grid_points is not None:
                # Use semi-transparent green for grid lines
                pen = QPen(QColor(0, 255, 0, 128))  # Semi-transparent green
                pen.setWidth(1)
                painter.setPen(pen)
                
                # Draw horizontal lines
                for row in self.grid_points:
                    for i in range(len(row) - 1):
                        p1 = image_view.map_to_viewport(QPointF(row[i][0], row[i][1]))
                        p2 = image_view.map_to_viewport(QPointF(row[i + 1][0], row[i + 1][1]))
                        painter.drawLine(p1, p2)
                
                # Draw vertical lines
                for col in range(len(self.grid_points[0])):
                    for i in range(len(self.grid_points) - 1):
                        p1 = image_view.map_to_viewport(QPointF(self.grid_points[i][col][0], self.grid_points[i][col][1]))
                        p2 = image_view.map_to_viewport(QPointF(self.grid_points[i + 1][col][0], self.grid_points[i + 1][col][1]))
                        painter.drawLine(p1, p2)
            
            # Draw distortion points and vectors
            if self.distortion_points and self.distortion_vectors:
                # Draw distortion points in blue
                pen = QPen(QColor(0, 0, 255))  # Blue
                pen.setWidth(2)
                painter.setPen(pen)
                
                for point, grid_point in self.distortion_vectors:
                    # Convert points to viewport coordinates
                    viewport_point = image_view.map_to_viewport(point)
                    viewport_grid = image_view.map_to_viewport(grid_point)
                    
                    # Draw distortion point
                    size = 10
                    painter.drawEllipse(viewport_point, size, size)
                    
                    # Draw vector from grid point to distortion point
                    pen.setStyle(Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    painter.drawLine(viewport_grid, viewport_point)
                    
                    # Reset pen style
                    pen.setStyle(Qt.PenStyle.SolidLine)
                    painter.setPen(pen)
        except Exception as e:
            logger.error(f"Error in paint event: {e}")
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        if len(self.points) == 4:
            self._generate_grid()
        self.update() 