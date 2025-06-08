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
    
    def pan(self, dx, dy):
        """Pan the image view."""
        self.pan_offset[0] += dx
        self.pan_offset[1] += dy
        self.update()
    
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        try:
            # Get the position of the mouse
            pos = event.position()
            
            # Calculate the old scale factor
            old_scale = self.scale_factor
            
            # Update scale factor
            if event.angleDelta().y() > 0:
                self.scale_factor *= 1.1
            else:
                self.scale_factor /= 1.1
            
            # Limit scale factor
            self.scale_factor = max(0.1, min(10.0, self.scale_factor))
            
            # Calculate the new position of the mouse
            new_pos = QPointF(
                pos.x() * (self.scale_factor / old_scale),
                pos.y() * (self.scale_factor / old_scale)
            )
            
            # Update pan offset to keep the mouse position fixed
            self.pan_offset[0] += (pos.x() - new_pos.x())
            self.pan_offset[1] += (pos.y() - new_pos.y())
            
            # Update display
            self._update_scaled_pixmap()
            self.update()
        except Exception as e:
            logger.error(f"Error in wheel event: {e}")
    
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