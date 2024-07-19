from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QCheckBox, QSystemTrayIcon, QSpacerItem, QSizePolicy, QMenu, QAction, QStyle, qApp
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from pathlib import Path
import subprocess
import os
from gradientmessagebox import *
     
class MainWindow(QMainWindow):
    """
         Сheckbox and system tray icons.
             Will initialize in the constructor.
    """
    check_box = None
    tray_icon = None
    
    # Override the class constructor
    def __init__(self):
        # Be sure to call the super class method
        QMainWindow.__init__(self)
        self.HOME = os.path.expanduser('~')
        self.HVYM = os.path.join(self.HOME, '.local', 'share', 'heavymeta-cli', 'hvym')
        self.FILE_PATH = Path(__file__).parent
        self.LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'hvym_logo_64.png')
        self.ICP_LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'icp_logo.png')
        self.icon = QIcon(self.LOGO_IMG)
        self.ic_icon = QIcon(self.ICP_LOGO_IMG)
     
        self.setMinimumSize(QSize(480, 80))             # Set sizes
        self.setWindowTitle("Metavinci")  # Set a title
        central_widget = QWidget(self)                  # Create a central widget
        self.setCentralWidget(central_widget)           # Set the central widget
     
        grid_layout = QGridLayout(self)         # Create a QGridLayout
        central_widget.setLayout(grid_layout)   # Set the layout into the central widget
        grid_layout.addWidget(QLabel("Application, which can minimize to Tray", self), 0, 0)
     
        # Add a checkbox, which will depend on the behavior of the program when the window is closed
        self.check_box = QCheckBox('Minimize to Tray')
        grid_layout.addWidget(self.check_box, 1, 0)
        grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 2, 0)
    
        # Init QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.icon)
     
        '''
            Define and add steps to work with the system tray icon
            show - show window
            hide - hide window
            exit - exit from application
        '''
        #show_action = QAction("Show", self)
        icp_new_account_action = QAction(self.ic_icon, "New Account", self)
        icp_change_account_action = QAction(self.ic_icon, "Change Account", self)
        quit_action = QAction("Exit", self)
        icp_new_account_action.triggered.connect(self.new_ic_account)
        icp_change_account_action.triggered.connect(self.change_ic_account)
        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_menu.addAction(icp_new_account_action)
        tray_menu.addAction(icp_change_account_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self._installation_check()
     
    # Override closeEvent, to intercept the window closing event
    # The window will be closed only if there is no check mark in the check box
    def closeEvent(self, event):
        if self.check_box.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Tray Program",
                "Application was minimized to Tray",
                QSystemTrayIcon.Information,
                2000
            )
    def new_ic_account(self):
        return(self._subprocess('hvym icp-new-account'))

    def change_ic_account(self):
        return(self._subprocess('hvym icp-set-account'))

    def hvym_check(self):
        return(self._subprocess('hvym check'))

    def _installation_check(self):
        if not os.path.isfile(self.HVYM):
            print('Install the cli')
        else:
            print('hvym is installed')
            if self.hvym_check().strip() == 'ONE-TWO':
                print('hvym is on path')
                self._subprocess('hvym splash')
            else:
                self._install_hvym()

    def _install_hvym(self):
        self._subprocess('curl -L https://github.com/inviti8/hvym/raw/main/install.sh | bash')
        if self.hvym_check().strip() == 'ONE-TWO':
            print('hvym is on path')
            self._subprocess('hvym splash')
        else:
            print('hvym not installed.')

    def _subprocess(self, command):
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return output.decode('utf-8')
        except Exception as e:
            return "Command failed with error: "+str(e)
         
     
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    mw = MainWindow()
    #mw.show()
    sys.exit(app.exec())