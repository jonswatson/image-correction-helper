import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QToolBar,
    QFileDialog, QMessageBox, QSpinBox, QLabel,
    QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QImage
import numpy as np
import cv2

from .image_view import ImageView
from .point_selector import PointSelector
from .grid_overlay import GridOverlay

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Correction Helper")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        load_action = toolbar.addAction("Load Image")
        load_action.triggered.connect(self._load_image)
        
        save_action = toolbar.addAction("Save Image")
        save_action.triggered.connect(self._save_image)
        
        toolbar.addSeparator()
        
        fit_action = toolbar.addAction("Fit to View")
        fit_action.triggered.connect(self._fit_to_view)
        
        clear_action = toolbar.addAction("Clear Points")
        clear_action.triggered.connect(self._clear_points)
        
        # Create image view
        self.image_view = ImageView()
        layout.addWidget(self.image_view)
        
        # Create point selector
        self.point_selector = PointSelector(self.image_view)
        self.image_view.setPointSelector(self.point_selector)
        self.point_selector.point_added.connect(self._on_point_added)
        self.point_selector.point_removed.connect(self._on_point_removed)
        
        # Create grid overlay
        self.grid_overlay = GridOverlay(self.image_view)
        self.image_view.setGridOverlay(self.grid_overlay)
        self.grid_overlay.set_points(self.point_selector.get_points())
        
        # Set focus policy to ensure we receive key events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.image_view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set up grid size controls
        self._setup_grid_controls()
        
        # Set up space bar panning
        self.space_pressed = False
        self.last_mouse_pos = None
        
        # Store original image for preview
        self.original_image = None
        
        # Add preview checkbox
        self.preview_checkbox = QCheckBox("Preview Perspective")
        self.preview_checkbox.stateChanged.connect(self._on_preview_changed)
        toolbar.addWidget(self.preview_checkbox)
    
    def _create_toolbar(self):
        """Create the main toolbar."""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Load image action
        load_action = QAction("Load Image", self)
        load_action.triggered.connect(self._on_load_image)
        toolbar.addAction(load_action)
        
        # Save image action
        save_action = QAction("Save Image", self)
        save_action.triggered.connect(self._on_save_image)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # Fit to view action
        fit_action = QAction("Fit to View", self)
        fit_action.triggered.connect(self._fit_to_view)
        toolbar.addAction(fit_action)
        
        # Clear points action
        clear_action = QAction("Clear Points", self)
        clear_action.triggered.connect(self._on_clear_points)
        toolbar.addAction(clear_action)
    
    def _setup_grid_controls(self):
        """Set up grid size controls in the toolbar."""
        toolbar = self.findChild(QToolBar)
        if not toolbar:
            return
        
        toolbar.addSeparator()
        
        # Add grid size controls
        toolbar.addWidget(QLabel("Grid Size:"))
        
        # Rows spinbox
        self.rows_spinbox = QSpinBox()
        self.rows_spinbox.setRange(2, 20)
        self.rows_spinbox.setValue(4)
        self.rows_spinbox.valueChanged.connect(self._update_grid_size)
        toolbar.addWidget(self.rows_spinbox)
        
        toolbar.addWidget(QLabel("x"))
        
        # Columns spinbox
        self.cols_spinbox = QSpinBox()
        self.cols_spinbox.setRange(2, 20)
        self.cols_spinbox.setValue(4)
        self.cols_spinbox.valueChanged.connect(self._update_grid_size)
        toolbar.addWidget(self.cols_spinbox)
    
    def _load_image(self):
        """Load an image file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Image",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
            
            if file_path:
                # Load image for display
                self.image_view.load_image(file_path)
                
                # Store original image for preview
                image = QImage(file_path)
                if image.isNull():
                    raise ValueError("Failed to load image")
                
                # Convert QImage to numpy array
                width = image.width()
                height = image.height()
                ptr = image.bits()
                ptr.setsize(height * width * 4)
                arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
                
                # Convert RGBA to BGR (OpenCV format)
                self.original_image = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
                
                # Reset points and preview
                self.point_selector.clear_points()
                self.grid_overlay.set_points([])
                self.preview_checkbox.setChecked(False)
                
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
    
    def _on_preview_changed(self, state):
        """Handle preview checkbox changes."""
        try:
            if not self.original_image is not None:
                return
            
            points = self.point_selector.get_points()
            if len(points) != 4:
                self.preview_checkbox.setChecked(False)
                return
            
            if state == Qt.CheckState.Checked.value:
                # Convert QPointF points to numpy array
                src_points = np.array([[p.x(), p.y()] for p in points], dtype=np.float32)
                
                # Calculate target points to make grid cells square
                width = max(
                    np.linalg.norm(src_points[1] - src_points[0]),
                    np.linalg.norm(src_points[2] - src_points[3])
                )
                height = max(
                    np.linalg.norm(src_points[3] - src_points[0]),
                    np.linalg.norm(src_points[2] - src_points[1])
                )
                
                # Create target points in a rectangle
                target_points = np.array([
                    [0, 0],           # Top-left
                    [width, 0],       # Top-right
                    [width, height],  # Bottom-right
                    [0, height]       # Bottom-left
                ], dtype=np.float32)
                
                # Calculate perspective transform
                transform = cv2.getPerspectiveTransform(src_points, target_points)
                
                # Apply transform
                transformed = cv2.warpPerspective(
                    self.original_image,
                    transform,
                    (int(width), int(height))
                )
                
                # Save transformed image to temp file
                temp_path = "temp_transformed.png"
                cv2.imwrite(temp_path, transformed)
                
                # Load transformed image
                self.image_view.load_image(temp_path)
            else:
                # Load original image
                self.image_view.load_image(self.image_view.current_image_path)
            
        except Exception as e:
            logger.error(f"Error handling preview change: {e}")
            self.preview_checkbox.setChecked(False)
            QMessageBox.critical(self, "Error", f"Failed to update preview: {e}")
    
    def _save_image(self):
        """Save the current image."""
        try:
            if not self.image_view.image:
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Image",
                "",
                "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;BMP Files (*.bmp)"
            )
            
            if file_path:
                self.image_view.save_image(file_path)
        except Exception as e:
            logger.error(f"Error saving image: {e}")
    
    def _fit_to_view(self):
        """Fit the image to the view."""
        try:
            self.image_view.fit_to_view()
        except Exception as e:
            logger.error(f"Error fitting to view: {e}")
    
    def _update_grid_size(self):
        """Update the grid size based on spinbox values."""
        try:
            rows = self.rows_spinbox.value()
            cols = self.cols_spinbox.value()
            self.grid_overlay.set_grid_size(rows, cols)
        except Exception as e:
            logger.error(f"Error updating grid size: {e}")
    
    def _on_point_added(self, index, point):
        """Handle point added event."""
        try:
            points = self.point_selector.get_points()
            self.grid_overlay.set_points(points)
            # Show grid when we have 4 points
            if len(points) == 4:
                self.grid_overlay.show_grid(True)
        except Exception as e:
            logger.error(f"Error handling point added: {e}")
    
    def _on_point_removed(self, index):
        """Handle point removed event."""
        try:
            points = self.point_selector.get_points()
            self.grid_overlay.set_points(points)
            # Hide grid if we don't have 4 points
            if len(points) != 4:
                self.grid_overlay.show_grid(False)
        except Exception as e:
            logger.error(f"Error handling point removed: {e}")
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Space:
            self.image_view.set_panning(True)
            self.image_view.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        """Handle key release events."""
        if event.key() == Qt.Key.Key_Space:
            self.image_view.set_panning(False)
            self.image_view.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().keyReleaseEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if self.space_pressed and event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = event.pos()
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.space_pressed and self.last_mouse_pos is not None:
            delta = event.pos() - self.last_mouse_pos
            self.image_view.pan(delta.x(), delta.y())
            self.last_mouse_pos = event.pos()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = None
        super().mouseReleaseEvent(event)
    
    def _clear_points(self):
        """Clear all selected points."""
        try:
            self.point_selector.clear_points()
            self.grid_overlay.set_points([])
            self.grid_overlay.show_grid(False)
            self.preview_checkbox.setChecked(False)
        except Exception as e:
            logger.error(f"Error clearing points: {e}") 