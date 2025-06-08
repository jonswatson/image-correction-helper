import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QToolBar,
    QFileDialog, QMessageBox, QSpinBox, QLabel,
    QCheckBox
)
from PyQt6.QtCore import Qt, QPointF
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
        load_action.triggered.connect(self._on_open_image)
        
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
        self.preview_checkbox.setToolTip("Select points in order: 1) Top-left, 2) Top-right, 3) Bottom-right, 4) Bottom-left")
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
    
    def _on_open_image(self):
        """Handle open image action."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Image",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
            
            if file_path:
                # Load image
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
                
                # Reset point selector and grid
                self.point_selector.clear_points()
                self.grid_overlay.set_points([])
                self.grid_overlay.show_grid(False)
                
                # Reset preview
                self.preview_checkbox.setChecked(False)
                
                # Ensure point selector is properly initialized
                self.point_selector.setGeometry(0, 0, self.image_view.width(), self.image_view.height())
                self.point_selector.start_selection()
                self.point_selector.raise_()
                
        except Exception as e:
            logger.error(f"Error opening image: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open image: {e}")
    
    def _order_points(self, points):
        """Order points to minimize rotation and flipping."""
        try:
            # Convert QPointF points to numpy array
            points_array = np.array([[p.x(), p.y()] for p in points])
            
            # Calculate center point
            center = np.mean(points_array, axis=0)
            
            # Calculate angles relative to center
            angles = np.arctan2(points_array[:, 1] - center[1], points_array[:, 0] - center[0])
            
            # Sort points by angle (clockwise from top-left)
            sorted_indices = np.argsort(angles)
            
            # Reorder points
            ordered_points = [points[i] for i in sorted_indices]
            
            # Ensure top-left is first point
            # Find point with minimum x+y (closest to top-left)
            distances = [p.x() + p.y() for p in ordered_points]
            min_index = distances.index(min(distances))
            
            # Rotate list to start with top-left
            ordered_points = ordered_points[min_index:] + ordered_points[:min_index]
            
            return ordered_points
        except Exception as e:
            logger.error(f"Error ordering points: {e}")
            return points

    def _on_preview_changed(self, state):
        """Handle preview checkbox changes."""
        try:
            if self.original_image is None:
                return
            
            points = self.point_selector.get_points()
            if len(points) != 4:
                self.preview_checkbox.setChecked(False)
                return
            
            # Order points to minimize rotation and flipping
            ordered_points = self._order_points(points)
            
            if state == Qt.CheckState.Checked.value:
                # Store original state if not already stored
                if not hasattr(self, '_original_state'):
                    self._original_state = {
                        'image': self.original_image.copy(),
                        'points': points.copy(),
                        'grid_points': self.grid_overlay.grid_points.copy() if self.grid_overlay.grid_points is not None else None
                    }
                
                # Lock points during transform
                self.point_selector.set_locked(True)
                
                # Convert QPointF points to numpy array
                src_points = np.array([[p.x(), p.y()] for p in ordered_points], dtype=np.float32)
                
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
                
                # Calculate the full image bounds after transformation
                h, w = self.original_image.shape[:2]
                corners = np.array([[0, 0], [w, 0], [w, h], [0, h]], dtype=np.float32)
                transformed_corners = cv2.perspectiveTransform(corners.reshape(-1, 1, 2), transform).reshape(-1, 2)
                
                # Calculate the translation needed to keep all points in view
                min_x = min(transformed_corners[:, 0])
                min_y = min(transformed_corners[:, 1])
                max_x = max(transformed_corners[:, 0])
                max_y = max(transformed_corners[:, 1])
                
                # Create translation matrix
                translation = np.array([
                    [1, 0, -min_x if min_x < 0 else 0],
                    [0, 1, -min_y if min_y < 0 else 0],
                    [0, 0, 1]
                ])
                
                # Combine translation with perspective transform
                full_transform = translation @ transform
                
                # Calculate output size to fit all transformed points
                output_width = int(max_x - min_x) if min_x < 0 else int(max_x)
                output_height = int(max_y - min_y) if min_y < 0 else int(max_y)
                
                # Apply transform to image
                transformed = cv2.warpPerspective(
                    self.original_image,
                    full_transform,
                    (output_width, output_height)
                )
                
                # Update image view with transformed image
                self.image_view.image = transformed
                self.image_view._update_scaled_pixmap()
                self.image_view.update()
                
                # Transform grid points if they exist
                if self.grid_overlay.grid_points is not None:
                    # Flatten grid points to 2D array
                    grid_points = self.grid_overlay.grid_points.reshape(-1, 2)
                    transformed_grid_points = cv2.perspectiveTransform(
                        grid_points.reshape(-1, 1, 2),
                        full_transform
                    ).reshape(-1, 2)
                    
                    # Reshape back to original grid shape
                    transformed_grid_points = transformed_grid_points.reshape(
                        self.grid_overlay.rows,
                        self.grid_overlay.cols,
                        2
                    )
                    
                    # Update grid points
                    self.grid_overlay.grid_points = transformed_grid_points
                    self.grid_overlay.update()
                
                # Transform corner points
                transformed_points = cv2.perspectiveTransform(
                    src_points.reshape(-1, 1, 2),
                    full_transform
                ).reshape(-1, 2)
                
                # Update point selector points
                self.point_selector.points = [QPointF(p[0], p[1]) for p in transformed_points]
                self.point_selector.update()
                
            else:
                # Restore original state
                if hasattr(self, '_original_state'):
                    self.image_view.image = self._original_state['image']
                    self.image_view._update_scaled_pixmap()
                    self.image_view.update()
                    
                    self.point_selector.points = self._original_state['points']
                    self.point_selector.update()
                    
                    if self._original_state['grid_points'] is not None:
                        self.grid_overlay.grid_points = self._original_state['grid_points']
                        self.grid_overlay.update()
                    
                    delattr(self, '_original_state')
                
                # Unlock points
                self.point_selector.set_locked(False)
                
        except Exception as e:
            logger.error(f"Error handling preview change: {e}")
            self.preview_checkbox.setChecked(False)
            QMessageBox.critical(self, "Error", f"Failed to update preview: {e}")
    
    def _save_image(self):
        """Save the current image."""
        try:
            if self.image_view.image is None:
                return
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Image",
                "",
                "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;BMP Files (*.bmp)"
            )
            
            if file_path:
                # If preview is active, save the transformed image
                if self.preview_checkbox.isChecked():
                    # Convert RGB to BGR for OpenCV
                    image = cv2.cvtColor(self.image_view.image, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(file_path, image)
                else:
                    # Save the original image
                    cv2.imwrite(file_path, self.original_image)
                logger.info(f"Image saved: {file_path}")
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save image: {e}")
    
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