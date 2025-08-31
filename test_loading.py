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
                           QVBoxLayout, QWidget, QLabel, QSplashScreen, QMessageBox)
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
        
        # Initialize with a default pixmap (will be updated by the movie)
        super().__init__(QPixmap(1, 1))
        
        # Set window flags to make it stay on top and frameless
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Set up the movie
        print(f"Loading movie from: {gif_path}")
        self.movie = QMovie(gif_path)
        
        if not self.movie.isValid():
            print(f"Error: Could not load animation from {gif_path}")
            # Fallback to a simple message if GIF loading fails
            self.showMessage("Loading...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
            self.setFixedSize(200, 200)  # Default size for fallback
        else:
            print(f"Movie frame count: {self.movie.frameCount()}")
            print(f"Movie size: {self.movie.scaledSize()}")
            
            # Connect the frame changed signal
            self.movie.frameChanged.connect(self.update_pixmap)
            
            # Start the animation
            self.movie.start()
            
            # Set initial size based on the first frame
            first_frame = self.movie.currentPixmap()
            if not first_frame.isNull():
                self.setFixedSize(first_frame.size())
        
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
                    # Set the pixmap
                    self.setPixmap(current_pixmap)
                    # Set the mask to make the background transparent
                    self.setMask(current_pixmap.mask())
        except Exception as e:
            print(f"Error updating pixmap: {e}")
    
    def update_progress(self, value):
        """Optional: Update the progress message if needed.
        This is not required for the animation to work.
        """
        if hasattr(self, 'movie') and self.movie.isValid():
            self.showMessage(
                f"Loading... {value}%",
                Qt.AlignBottom | Qt.AlignCenter,
                Qt.white
            )

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
        """Find the loading GIF in multiple possible locations.
        
        This method checks several locations in order:
        1. Qt resource path (for built app)
        2. Next to the executable (for frozen app)
        3. In an images/ subdirectory (for development)
        4. Fallback to a built-in animation if no file is found
        """
        possible_paths = [
            # 1. Qt resource path (works in built app)
            (":/images/loading.gif", "Qt resource path"),
            
            # 2. Next to executable (for frozen app)
            (os.path.join(sys._MEIPASS, "images", "loading.gif") if hasattr(sys, '_MEIPASS') else None, 
             "MEIPATH bundle"),
            
            # 3. In application directory (for frozen app on some platforms)
            (os.path.join(os.path.dirname(sys.executable), "images", "loading.gif") 
             if getattr(sys, 'frozen', False) else None, "executable directory"),
            
            # 4. In development directory
            (os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "loading.gif"), 
             "development directory"),
        ]
        
        for path, path_type in possible_paths:
            if not path:  # Skip None paths (conditional paths that didn't apply)
                continue
                
            # For Qt resource paths
            if path.startswith(':'):
                if QMovie(path).isValid():
                    print(f"Found loading GIF at {path_type}: {path}")
                    return path
            # For filesystem paths
            elif os.path.exists(path):
                print(f"Found loading GIF at {path_type}: {path}")
                return path
        
        # If we get here, no valid path was found
        print("Warning: Could not find loading.gif in any standard location")
        return None  # Let the caller handle the fallback
    
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
