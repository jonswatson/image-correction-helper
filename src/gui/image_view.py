import logging
import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QImage, QPixmap, QPainter

logger = logging.getLogger(__name__)

class ImageView(QWidget):
    def __init__(self):
        super().__init__()
        self.image = None
        self.original_image = None
        self.scaled_pixmap = None
        self.scale_factor = 1.0
        self.pan_offset = [0, 0]
        self.point_selector = None
        self.grid_overlay = None
        self.is_panning = False
        self.last_mouse_pos = None
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def load_image(self, file_path):
        """Load an image from file."""
        try:
            # Read image with OpenCV
            image = cv2.imread(file_path)
            if image is None:
                raise ValueError(f"Failed to load image: {file_path}")
            
            # Convert BGR to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Store original and current image
            self.original_image = image.copy()
            self.image = image
            
            # Reset view
            self.scale_factor = 1.0
            self.pan_offset = [0, 0]
            
            # Update display
            self._update_scaled_pixmap()
            self.update()
            
            logger.info(f"Image loaded: {file_path}")
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            raise
    
    def save_image(self, file_path):
        """Save the current image to file."""
        try:
            if self.image is None:
                raise ValueError("No image to save")
            
            # Convert RGB to BGR for OpenCV
            image = cv2.cvtColor(self.image, cv2.COLOR_RGB2BGR)
            
            # Save image
            cv2.imwrite(file_path, image)
            logger.info(f"Image saved: {file_path}")
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            raise
    
    def set_panning(self, panning):
        """Set the panning state."""
        self.is_panning = panning
        if not panning:
            self.last_mouse_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_panning:
            self.last_mouse_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.is_panning and self.last_mouse_pos is not None:
            delta = event.position() - self.last_mouse_pos
            self.pan_offset[0] += delta.x()
            self.pan_offset[1] += delta.y()
            self.last_mouse_pos = event.position()
            self._update_scaled_pixmap()
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = None
            if self.is_panning:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Handle wheel events for zooming."""
        if self.image is None:
            return
        
        # Calculate zoom factor
        zoom_factor = 1.1 if event.angleDelta().y() > 0 else 0.9
        
        # Get mouse position
        mouse_pos = event.position()
        
        # Calculate new scale factor
        new_scale = self.scale_factor * zoom_factor
        
        # Limit zoom range
        if 0.1 <= new_scale <= 10.0:
            # Calculate the position of the mouse relative to the image
            image_x = (mouse_pos.x() - self.pan_offset[0]) / self.scale_factor
            image_y = (mouse_pos.y() - self.pan_offset[1]) / self.scale_factor
            
            # Update scale factor
            self.scale_factor = new_scale
            
            # Adjust pan offset to keep the point under the mouse in the same position
            self.pan_offset[0] = mouse_pos.x() - image_x * self.scale_factor
            self.pan_offset[1] = mouse_pos.y() - image_y * self.scale_factor
            
            self._update_scaled_pixmap()
            self.update()
    
    def _update_scaled_pixmap(self):
        """Update the scaled pixmap."""
        if self.image is None:
            return
        
        try:
            # Convert numpy array to QImage
            height, width, channel = self.image.shape
            bytes_per_line = 3 * width
            q_image = QImage(
                self.image.data,
                width,
                height,
                bytes_per_line,
                QImage.Format.Format_RGB888
            )
            
            # Create pixmap and scale it
            pixmap = QPixmap.fromImage(q_image)
            self.scaled_pixmap = pixmap.scaled(
                int(width * self.scale_factor),
                int(height * self.scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        except Exception as e:
            logger.error(f"Error updating scaled pixmap: {e}")
    
    def paintEvent(self, event):
        """Handle paint events."""
        painter = None
        try:
            if self.image is None:
                return
            
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            
            # Calculate position to center the image
            x = int((self.width() - self.scaled_pixmap.width()) // 2 + self.pan_offset[0])
            y = int((self.height() - self.scaled_pixmap.height()) // 2 + self.pan_offset[1])
            
            # Draw the image
            painter.drawPixmap(x, y, self.scaled_pixmap)
        except Exception as e:
            logger.error(f"Error in paint event: {e}")
        finally:
            if painter is not None:
                painter.end()
    
    def resizeEvent(self, event):
        """Handle resize events."""
        super().resizeEvent(event)
        if self.point_selector:
            self.point_selector.setGeometry(0, 0, self.width(), self.height())
        if self.grid_overlay:
            self.grid_overlay.setGeometry(0, 0, self.width(), self.height())
        if self.image is not None:
            self._update_scaled_pixmap()
            self.update()
    
    def fit_to_view(self):
        """Scale the image to fit the view while maintaining aspect ratio."""
        try:
            if self.image is None:
                return
            
            # Get image and view dimensions
            img_height, img_width = self.image.shape[:2]
            view_width = self.width()
            view_height = self.height()
            
            # Calculate scale factors for both dimensions
            width_scale = view_width / img_width
            height_scale = view_height / img_height
            
            # Use the smaller scale factor to ensure the image fits
            self.scale_factor = min(width_scale, height_scale)
            
            # Reset pan offset
            self.pan_offset = [0, 0]
            
            # Update display
            self._update_scaled_pixmap()
            self.update()
            
            logger.info("Image fitted to view")
        except Exception as e:
            logger.error(f"Error fitting image to view: {e}")
    
    def setPointSelector(self, selector):
        """Set the point selector widget."""
        self.point_selector = selector
        if self.point_selector:
            self.point_selector.setGeometry(0, 0, self.width(), self.height())
            self.point_selector.start_selection()
    
    def setGridOverlay(self, overlay):
        """Set the grid overlay widget."""
        self.grid_overlay = overlay
        if self.grid_overlay:
            self.grid_overlay.setGeometry(0, 0, self.width(), self.height())
    
    def map_to_image(self, viewport_pos):
        """Convert viewport coordinates to image coordinates."""
        if self.image is None or self.scaled_pixmap is None:
            return QPointF(0, 0)
        
        try:
            # Calculate image position in viewport
            image_x = (self.width() - self.scaled_pixmap.width()) // 2 + self.pan_offset[0]
            image_y = (self.height() - self.scaled_pixmap.height()) // 2 + self.pan_offset[1]
            
            # Convert from viewport to image coordinates
            x = (viewport_pos.x() - image_x) / self.scale_factor
            y = (viewport_pos.y() - image_y) / self.scale_factor
            
            return QPointF(x, y)
        except Exception as e:
            logger.error(f"Error mapping to image coordinates: {e}")
            return QPointF(0, 0)
    
    def map_to_viewport(self, image_pos):
        """Convert image coordinates to viewport coordinates."""
        if self.image is None or self.scaled_pixmap is None:
            return QPointF(0, 0)
        
        try:
            # Calculate image position in viewport
            image_x = (self.width() - self.scaled_pixmap.width()) // 2 + self.pan_offset[0]
            image_y = (self.height() - self.scaled_pixmap.height()) // 2 + self.pan_offset[1]
            
            # Convert from image to viewport coordinates
            x = image_pos.x() * self.scale_factor + image_x
            y = image_pos.y() * self.scale_factor + image_y
            
            return QPointF(x, y)
        except Exception as e:
            logger.error(f"Error mapping to viewport coordinates: {e}")
            return QPointF(0, 0) 