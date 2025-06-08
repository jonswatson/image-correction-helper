import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QToolBar,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from .image_view import ImageView

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
        
        # Create image view
        self.image_view = ImageView()
        layout.addWidget(self.image_view)
        
        # Set up space bar panning
        self.space_pressed = False
        self.last_mouse_pos = None
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = True
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        """Handle key release events."""
        if event.key() == Qt.Key.Key_Space:
            self.space_pressed = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
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
    
    def _load_image(self):
        """Load an image file."""
        try:
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Open Image",
                "",
                "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
            )
            if file_name:
                self.image_view.load_image(file_name)
                logger.info(f"Loaded image: {file_name}")
        except Exception as e:
            logger.error(f"Error loading image: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load image: {e}")
    
    def _save_image(self):
        """Save the current image."""
        try:
            if self.image_view.image is None:
                QMessageBox.warning(self, "Warning", "No image to save")
                return
            
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Save Image",
                "",
                "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;BMP Files (*.bmp)"
            )
            if file_name:
                self.image_view.save_image(file_name)
                logger.info(f"Saved image: {file_name}")
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save image: {e}")
    
    def _fit_to_view(self):
        """Fit the image to the view."""
        try:
            self.image_view.fit_to_view()
        except Exception as e:
            logger.error(f"Error fitting to view: {e}")
            QMessageBox.critical(self, "Error", f"Failed to fit image to view: {e}") 