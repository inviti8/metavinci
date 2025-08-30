#!/usr/bin/env python3
"""
Test script for verifying loading animation functionality across platforms.
This script demonstrates a simple loading animation using QSplashScreen.
"""
import os
import sys
import time
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QMovie, QPixmap
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                           QVBoxLayout, QWidget, QLabel, QSplashScreen)
from PIL import Image

class WorkerThread(QThread):
    """Worker thread that simulates a long-running task."""
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    
    def run(self):
        """Simulate work by sleeping and emitting progress."""
        for i in range(1, 6):
            time.sleep(1)  # Simulate work
            self.progress.emit(i * 20)  # 20% progress each second
        self.finished.emit()

class LoadingSplash(QSplashScreen):
    """Custom splash screen with animated GIF support."""
    def __init__(self, gif_path, parent=None):
        print(f"Creating LoadingSplash with GIF: {gif_path}")
        
        # First, use PIL to get the GIF dimensions
        try:
            with Image.open(gif_path) as img:
                gif_size = img.size
                print(f"GIF dimensions from PIL: {gif_size}")
                # Create a pixmap with the GIF dimensions
                pixmap = QPixmap(*gif_size)
        except Exception as e:
            print(f"Error getting GIF dimensions: {e}")
            # Fallback to a default size
            pixmap = QPixmap(200, 200)
            gif_size = (200, 200)
        
        # Fill with a transparent background
        pixmap.fill(Qt.transparent)
        
        # Initialize with the pixmap
        super().__init__(pixmap)
        
        # Store the original size
        self.original_size = gif_size
        
        # Set window flags to make it stay on top and frameless
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Set up the movie
        print(f"Loading movie from: {gif_path}")
        self.movie = QMovie(gif_path)
        
        if not self.movie.isValid():
            print(f"Error: Could not load animation from {gif_path}")
            # Fallback to a simple message if GIF loading fails
            self.showMessage("Loading...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
        else:
            print(f"Movie frame count: {self.movie.frameCount()}")
            print(f"Movie size: {self.movie.scaledSize()}")
            
            # Set the window size to match the GIF dimensions
            self.setFixedSize(*gif_size)
            
            # Connect the frame changed signal
            self.movie.frameChanged.connect(self.update_pixmap)
            
            # Start the animation
            self.movie.start()
        
        # Center on screen
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        print(f"Window positioned at: ({x}, {y})")
        
        # Show the splash screen
        self.show()
        print("Splash screen shown")
    
    def update_pixmap(self, frame_number=None):
        """Update the splash screen with the current frame."""
        try:
            if hasattr(self, 'movie') and self.movie.state() == QMovie.Running:
                current_pixmap = self.movie.currentPixmap()
                if not current_pixmap.isNull():
                    # Set the pixmap directly without scaling
                    self.setPixmap(current_pixmap)
                    # Set the mask to make the background transparent
                    self.setMask(current_pixmap.mask())
                    # Force update
                    self.repaint()
                    QApplication.processEvents()
        except Exception as e:
            print(f"Error updating pixmap: {e}")
    
    def update_progress(self, value):
        """Update the progress message."""
        self.showMessage(
            f"Loading... {value}%",
            Qt.AlignBottom | Qt.AlignCenter,
            Qt.white
        )
        QApplication.processEvents()

class TestWindow(QMainWindow):
    """Main test window with a button to trigger the loading animation."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loading Animation Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Add a button to trigger the loading animation
        self.test_button = QPushButton("Start Long Operation")
        self.test_button.clicked.connect(self.start_long_operation)
        layout.addWidget(self.test_button)
        
        # Status label
        self.status_label = QLabel("Click the button to start a long operation")
        layout.addWidget(self.status_label)
        
        # Determine the path to the loading GIF
        self.loading_gif = self.find_loading_gif()
        
        # Show the window
        self.show()
    
    def find_loading_gif(self):
        """Find the loading GIF in common locations."""
        # Try resource path first (for built app)
        resource_path = ":/images/loading.gif"
        if QMovie(resource_path).isValid():
            print("Using resource path:", resource_path)
            return resource_path
            
        # Try relative path (for development)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        dev_path = os.path.join(script_dir, "images", "loading.gif")
        if os.path.exists(dev_path):
            print("Using development path:", dev_path)
            return dev_path
            
        # Fallback to a simple built-in animation
        print("Warning: Could not find loading.gif, using built-in animation")
        return None
    
    def start_long_operation(self):
        """Start a long operation with loading animation."""
        self.test_button.setEnabled(False)
        self.status_label.setText("Operation in progress...")
        
        # Create and show the splash screen
        try:
            if self.loading_gif and os.path.exists(self.loading_gif):
                self.splash = LoadingSplash(self.loading_gif, self)
            else:
                # Fallback to a simple QSplashScreen
                self.splash = QSplashScreen()
                self.splash.showMessage("Loading...", 
                                      Qt.AlignBottom | Qt.AlignCenter, 
                                      Qt.white)
            self.splash.show()
        except Exception as e:
            print(f"Error creating splash screen: {e}")
            # Fallback to a simple message box
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Loading", "Operation in progress...")
            self.splash = None
        
        # Create and start the worker thread
        self.worker = WorkerThread()
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.operation_finished)
        self.worker.start()
        
        # Check periodically if the worker is done
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_worker)
        self.timer.start(100)  # Check every 100ms
    
    def update_progress(self, value):
        """Update the progress in the splash screen."""
        if hasattr(self, 'splash') and hasattr(self.splash, 'update_progress'):
            self.splash.update_progress(value)
        QApplication.processEvents()
    
    def check_worker(self):
        """Check if the worker has finished."""
        if not self.worker.isRunning():
            self.timer.stop()
            self.operation_finished()
    
    def operation_finished(self):
        """Clean up after the operation is finished."""
        if hasattr(self, 'splash'):
            self.splash.finish(self)
            self.splash.deleteLater()
            del self.splash
            
        self.test_button.setEnabled(True)
        self.status_label.setText("Operation completed!")

def main():
    """Main function to run the test application."""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Print debug info
    print("Starting application...")
    print(f"Style: {app.style().objectName()}")
    print(f"Screens: {app.screens()}")
    
    # Create and show the main window
    print("Creating main window...")
    window = TestWindow()
    window.show()
    
    # Print window geometry
    print(f"Main window geometry: {window.geometry()}")
    
    # Run the application
    print("Starting event loop...")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
