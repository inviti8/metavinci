from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QCheckBox, QSystemTrayIcon, QComboBox, QDialogButtonBox, QSpacerItem, QSizePolicy, QMenu, QAction, QStyle, qApp, QVBoxLayout, QPushButton, QDialog, QDesktopWidget, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
from pathlib import Path
import subprocess
import os
from urllib.request import urlopen
from zipfile import ZipFile
from tinydb import TinyDB, Query
import tinydb_encrypted_jsonstorage as enc_json
import shutil
from biscuit_auth import KeyPair,PrivateKey, PublicKey,BiscuitBuilder,Fact,Authorizer,Biscuit
from cryptography.fernet import Fernet
import json
import re
from datetime import datetime, timedelta, timezone
from gifanimus import GifAnimation
import time
import threading
import sys


def _download_unzip(url, out_path):
      with urlopen(url) as zipresp:
          with ZipFile(BytesIO(zipresp.read())) as zfile:
              zfile.extractall(out_path)


def _subprocess(command):
        try:
            output = subprocess.check_output(command, stderr=subprocess.STDOUT)
            return output.decode('utf-8')
        except Exception as e:
            return None


def _run(command):
    output = subprocess.run(command, shell=True, capture_output=True, text=True)
    return output.stdout


class HVYM_SeedVault(TinyDB):
    """
        A class for encrypting & storing seed phrases
    """
    # Override the class constructor
    def __init__(self, encryption_key, path, storage=enc_json.EncryptedJSONStorage):
        # Be sure to call the super class method
        TinyDB.__init__(self, encryption_key, path, storage)
        self.HOME = os.path.expanduser('~')
        self.PATH = self.HVYM = Path.home() / '.metavinci'


class Metavinci(QMainWindow):
    """
        Network Daemon for Heavymeta
    """
    # Override the class constructor
    def __init__(self):
        # Be sure to call the super class method
        QMainWindow.__init__(self)
        self.HOME = os.path.expanduser('~')
        self.PATH = self.HVYM = Path.home() / '.metavinci'
        self.BIN_PATH = self.PATH / 'bin'
        self.KEYSTORE = self.PATH / 'keystore.enc'
        self.ENC_KEY = self.PATH / 'encryption_key.key'
        self.DFX = Path.home() / '.local'/ 'share'/ 'dfx'/ 'bin' / 'dfx'
        self.HVYM = Path.home() / '.local'/ 'share'/ 'heavymeta-cli'/ 'hvym'
        self.PRESS = Path.home() / '.local' / 'share' / 'heavymeta-press' / 'hvym_press'
        self.BLENDER_PATH = Path.home() / '.config' / 'blender'
        self.BLENDER_VERSIONS = []
        self.BLENDER_VERSION = None
        self.ADDON_INSTALL_PATH = self.BLENDER_PATH / str(self.BLENDER_VERSION) / 'scripts' / 'addons'
        self.ADDON_PATH = self.ADDON_INSTALL_PATH / 'heavymeta_standard'
        self.FILE_PATH = Path(__file__).parent
        self.HVYM_IMG = os.path.join(self.FILE_PATH, 'images', 'metavinci.png')
        self.LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'hvym_logo_64.png')
        self.LOADING_GIF = os.path.join(self.FILE_PATH, 'images', 'loading.gif')
        self.UPDATE_IMG = os.path.join(self.FILE_PATH, 'images', 'update.png')
        self.INSTALL_IMG = os.path.join(self.FILE_PATH, 'images', 'install.png')
        self.ICP_LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'icp_logo.png')
        self.ICP_ADD_IMG = os.path.join(self.FILE_PATH, 'images', 'icp_add.png')
        self.ICP_TEST_IMG = os.path.join(self.FILE_PATH, 'images', 'icp_test.png')
        self.ICP_SELECT_IMG = os.path.join(self.FILE_PATH, 'images', 'icp_select.png')
        self.ICP_REMOVE_IMG = os.path.join(self.FILE_PATH, 'images', 'icp_remove.png')
        self.STYLE_SHEET = os.path.join(self.FILE_PATH, 'data', 'style.qss')
        self.DB_SRC = os.path.join(self.FILE_PATH, 'data', 'db.json')
        self.DB_PATH = self.BIN_PATH /'db.json'
        if not self.DB_PATH.exists():
            shutil.copyfile(self.DB_SRC, str(self.DB_PATH))
        self.DB = TinyDB(str(self.DB_PATH))
        self.QUERY = Query()
        self.user_pid = str(_run('dfx identity get-principal')).strip()
        self.DB.update({'INITIALIZED': True, 'principal': self.user_pid}, self.QUERY.type == 'app_data')
        self.INITIALIZED = (len(self.DB.search(self.QUERY.INITIALIZED == True)) > 0)
        self.win_icon = QIcon(self.HVYM_IMG)
        self.icon = QIcon(self.LOGO_IMG)
        self.update_icon = QIcon(self.UPDATE_IMG)
        self.install_icon = QIcon(self.INSTALL_IMG)
        self.ic_icon = QIcon(self.ICP_LOGO_IMG)
        self.ic_add_icon = QIcon(self.ICP_ADD_IMG)
        self.ic_test_icon = QIcon(self.ICP_TEST_IMG)
        self.ic_select_icon = QIcon(self.ICP_SELECT_IMG)
        self.ic_remove_icon = QIcon(self.ICP_REMOVE_IMG)
        self.publik_key = None
        self.private_key = None
        self.refresh_interval = 8 * 60 * 60  # 8 hours in seconds

        self.setMinimumSize(QSize(64, 64))             # Set sizes
        self.setWindowTitle("Metavinci")  # Set a title
        self.central_widget = QWidget(self) 
        self.central_widget.setWindowIcon(self.win_icon)                # Create a central widget
        self.setCentralWidget(self.central_widget)           # Set the central widget
        self.setWindowIcon(self.win_icon)          # Set the icon
        # label = QLabel("", self)
        # label.setPixmap(QPixmap(self.LOGO_IMG))
        # label.adjustSize()

        self.setWindowFlag(Qt.FramelessWindowHint) 

        if self.BLENDER_PATH.exists():
            for file in os.listdir(str(self.BLENDER_PATH)):
                d = os.path.join(str(self.BLENDER_PATH), file)
                if os.path.isdir(d):
                    self.BLENDER_VERSIONS.append(file)

        idx=0
        for ver in self.BLENDER_VERSIONS:
            if self.BLENDER_VERSION == None:
                self.BLENDER_VERSION = ver
            if idx > 0:
                if float(ver) > float(self.BLENDER_VERSIONS[idx-1]):
                    self.BLENDER_VERSION = ver
                    self.ADDON_INSTALL_PATH = self.BLENDER_PATH / str(self.BLENDER_VERSION) / 'scripts' / 'addons'
                    self.ADDON_PATH = self.ADDON_INSTALL_PATH / 'heavymeta_standard'
            idx += 1
     
        # Add a checkbox, which will depend on the behavior of the program when the window is closed
        #self.check_box = QCheckBox('Minimize to Tray')
        #grid_layout.addWidget(self.check_box, 1, 0)
        #grid_layout.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding), 2, 0)
    
        # Init QSystemTrayIcon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.icon)
     
        '''
            Define and add steps to work with the system tray icon
            show - show window
            hide - hide window
            exit - exit from application
        '''
        post_init_action = QAction(self.icon, "Initialize", self)
        post_init_action.triggered.connect(self.init_post)

        icp_principal_action = QAction(self.ic_icon, "Get Principal", self)
        icp_principal_action.triggered.connect(self.get_ic_principal)

        icp_new_account_action = QAction(self.ic_add_icon, "New Account", self)
        icp_new_account_action.triggered.connect(self.new_ic_account)

        icp_new_test_account_action = QAction(self.ic_test_icon, "New Test Account", self)
        icp_new_test_account_action.triggered.connect(self.new_ic_test_account)

        icp_change_account_action = QAction(self.ic_select_icon, "Change Account", self)
        icp_change_account_action.triggered.connect(self.change_ic_account)

        icp_remove_account_action = QAction(self.ic_remove_icon, "Remove Account", self)
        icp_remove_account_action.triggered.connect(self.remove_ic_account)

        icp_balance_action = QAction("ICP Balance", self)
        icp_balance_action.triggered.connect(self.get_icp_balance)

        oro_balance_action = QAction("ORO Balance", self)
        oro_balance_action.triggered.connect(self.get_oro_balance)

        ckETH_balance_action = QAction("ckETH Balance", self)
        ckETH_balance_action.triggered.connect(self.get_ckETH_balance)

        ckBTC_balance_action = QAction("ckBTC Balance", self)
        ckBTC_balance_action.triggered.connect(self.get_ckBTC_balance)

        install_hvym_action = QAction(self.install_icon, "Install hvym", self)
        install_hvym_action.triggered.connect(self._install_hvym)

        update_hvym_action = QAction(self.update_icon, "Update hvym", self)
        update_hvym_action.triggered.connect(self._update_hvym)

        run_press_action = QAction(self.icon, "Run press", self)
        run_press_action.triggered.connect(self.run_press)

        install_press_action = QAction(self.install_icon, "Install press", self)
        install_press_action.triggered.connect(self._install_press)

        update_press_action = QAction(self.update_icon, "Update press", self)
        update_press_action.triggered.connect(self._update_press)

        install_addon_action = QAction(self.install_icon, "Install Blender Addon", self)
        install_addon_action.triggered.connect(self._install_blender_addon)

        update_addon_action = QAction(self.update_icon, "Update Blender Addon", self)
        update_addon_action.triggered.connect(self._update_blender_addon)

        update_tools_action = QAction(self.update_icon, "Update All Tools", self)
        update_tools_action.triggered.connect(self.update_tools)

        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(qApp.quit)

        gen_keys_action = QAction("Generate Key Pair", self)
        gen_keys_action.triggered.connect(self.generate_store_keypair)

        import_keys_action = QAction("Import Key Pair", self)
        import_keys_action.triggered.connect(self.import_keys)
        
        # Add a new actions for tasks
        gen_keypair_action = QAction("Generate Keypair", self)
        gen_keypair_action.triggered.connect(self.generate_store_keypair)

        import_keypair_action = QAction("Import Keypair", self)
        import_keypair_action.triggered.connect(self.import_keys)

        gen_token_action = QAction("Generate Token", self)
        gen_token_action.triggered.connect(self.generate_store_token)

        start_daemon_action = QAction("Start Daemon", self)
        start_daemon_action.triggered.connect(self.authorization_loop)

        tray_menu = QMenu()

        if self.HVYM.is_file():
            tray_accounts_menu = tray_menu.addMenu("Accounts")
            tray_ic_accounts_menu = tray_accounts_menu.addMenu("IC")
            tray_ic_accounts_menu.addAction(icp_principal_action)
            tray_ic_accounts_menu.addAction(icp_new_test_account_action)
            tray_ic_accounts_menu.addAction(icp_new_account_action)
            tray_ic_accounts_menu.addAction(icp_change_account_action)
            tray_ic_accounts_menu.addAction(icp_remove_account_action)

        tray_tools_menu = tray_menu.addMenu("Tools")

        if self.PRESS.is_file():
            tray_tools_menu.addAction(run_press_action)

        tray_tools_update_menu = tray_tools_menu.addMenu("Updates")

        if not self.HVYM.is_file():
            tray_tools_update_menu.addAction(install_hvym_action)
        else:
            tray_tools_update_menu.addAction(update_hvym_action)

        if not self.PRESS.is_file():
            tray_tools_update_menu.addAction(install_press_action)
        else:
            tray_tools_update_menu.addAction(update_press_action)

        if not self.ADDON_PATH.exists():
            tray_tools_update_menu.addAction(install_addon_action)
        else:
            tray_tools_update_menu.addAction(update_addon_action)

        if self.HVYM.is_file():
            tray_tools_update_menu.addAction(update_tools_action)

            tray_balances_menu = tray_ic_accounts_menu.addMenu("Balances")
            tray_balances_menu.addAction(icp_balance_action)
            tray_balances_menu.addAction(oro_balance_action)
            tray_balances_menu.addAction(ckETH_balance_action)
            tray_balances_menu.addAction(ckBTC_balance_action)

        tray_keys_menu = tray_menu.addMenu("Keys")
        tray_keys_menu.addAction(gen_keys_action)
        tray_keys_menu.addAction(import_keys_action)

        tray_tasks_menu = tray_menu.addMenu("Tasks")
        tray_tasks_menu.addAction(gen_keypair_action)
        tray_tasks_menu.addAction(import_keypair_action)
        tray_tasks_menu.addAction(gen_token_action)
        tray_tasks_menu.addAction(start_daemon_action)

        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.setStyleSheet(Path(str(self.STYLE_SHEET)).read_text())
        

    def init_post(self):
        self.user_pid = str(_run('dfx identity get-principal')).strip()
        self.DB.update({'INITIALIZED': True, 'principal': self.user_pid}, self.QUERY.type == 'app_data')
        self._installation_check()
        msg = QMessageBox(self)
        msg.setWindowTitle("!")
        msg.setText("Metavinci must restart now...")
        msg.exec_()
        self.close()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def restart(self):
        confirm = self.open_confirm_dialog("Metavinci must close now, restart it after close...")
        self.close()

    def open_dir_dialog(self, prompt):
        self.show()
        dir_name = QFileDialog.getExistingDirectory(self, prompt)
        if dir_name:
            path = Path(dir_name)
            return str(path)
        
        self.hide()

    def loading_indicator(self, prompt):
        return GifAnimation(str(self.LOADING_GIF), 1000, True, prompt)
        
    def open_file_dialog(self, prompt, filter="*.key"):
        self.show
        filename, ok = QFileDialog.getOpenFileName(
            self,
            prompt, 
            self.HOME, 
            filter
        )
        if filename:
            path = Path(filename)
            return str(path)

        self.hide()
        
    def open_confirm_dialog(self, prompt):
        self.show()
        result = False
        response = QMessageBox.question(self, '?', prompt, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if response == QMessageBox.Yes:
            result = True

        self.hide()
        return result

    def open_msg_dialog(self, prompt):
        msg = QMessageBox(self)
        msg.setWindowTitle("!")
        msg.setText(prompt)
        msg.exec_()
    
    def open_option_dialog(self, prompt, options):
        self.show()
        result = False
        dlg =  QFileDialog(self)
        label = QLabel(prompt)
        combo = QComboBox()
        combo.addItems(["option1", "option2", "option3"])
        box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            centerButtons=True,
        )

        box.accepted.connect(dlg.accept)
        box.rejected.connect(dlg.reject)

        lay = QGridLayout(self)
        lay.addWidget(label, 0, 0)
        lay.addWidget(combo, 0, 1)
        lay.addWidget(box, 1, 0, 1, 2)

        dlg.resize(640, 240)

        response = box.Ok

        if response == QDialogButtonBox.Ok:
            result = True

        self.hide()
        return result

    # Task function for generating and storing the app keypair using biscuit-python
    def generate_store_keypair(self):
        encryption_key_path = self.open_dir_dialog("Select Directory to Store Encryption Key")

        if encryption_key_path == None:
            return
        else:
            encryption_key_path = os.path.join(encryption_key_path, 'encryption_key.key')
            print(encryption_key_path)
            print(os.path.isfile(encryption_key_path))
        
        try:
            # Generate keypair using biscuit-python
            keypair = KeyPair()

            serialized_keys = {
                "private_key": keypair.private_key.to_hex(),
                "public_key": keypair.public_key.to_hex()
            }
            
            # print("key generated & stored : ",serialized_keys)
            # locate .metavinci directory in user's home directory
            if not self.PATH.exists():
                self.PATH.mkdir(mode=0o700)  # Create directory with secure permissions

            # # Generate a symmetric encryption key
            encryption_key = Fernet.generate_key()
            cipher_suite = Fernet(encryption_key)

            serialized_keys_str = json.dumps(serialized_keys)
            encrpted_keys = cipher_suite.encrypt(serialized_keys_str.encode())

            keystore_path = str(self.KEYSTORE)

            if os.path.isfile(encryption_key_path):
                overwrite = self.open_confirm_dialog(f"File {encryption_key_path} already exists, do you want to overwrite it?")
                if overwrite == True:
                    # # # Write the encryption key
                    with open(encryption_key_path, 'wb') as encrypt_key_file:
                        encrypt_key_file.write(encryption_key)

            if self.KEYSTORE.is_file():
                overwrite = self.open_confirm_dialog(f"File {keystore_path} already exists, do you want to overwrite it?")
                if overwrite == True:
                    # # # Write the private key securely (restrict access to owner)
                    with open(keystore_path, 'wb') as keystore_file:
                        keystore_file.write(encrpted_keys)
                    os.chmod(keystore_path, 0o600)

        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error generating and storing app keypair.")

    def import_keys(self):
        encryption_key_path = self.open_file_dialog("Load encryption key.")

        print(encryption_key_path)

        if encryption_key_path == None:
            return
        
        try:
            # locate .metavinci directory in user's home directory
            if not self.PATH.exists():
                self.PATH.mkdir(mode=0o700)
            
            # Read the encrypted keys
            keystore_path = str(self.KEYSTORE)
            encryption_key_path = str(self.ENC_KEY)

            if not os.path.exists(keystore_path) or not os.path.exists(encryption_key_path):
                self.open_msg_dialog("No keypair found to import.")
                return
            
            with open(encryption_key_path, 'rb') as encrypt_key_file:
                encryption_key = encrypt_key_file.read()
            cipher_suite = Fernet(encryption_key)

            with open(keystore_path, 'rb') as keystore_file:
                encrypted_keys = keystore_file.read()

            decrypted_keys = cipher_suite.decrypt(encrypted_keys)
            serialized_keys = json.loads(decrypted_keys)

            # print("key imported : ",serialized_keys)
            self.private_key = PrivateKey.from_hex(serialized_keys['private_key'])
            self.public_key = PublicKey.from_hex(serialized_keys['public_key'])

        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error importing app keypair.")

    def get_icp_balance(self):
        icp_canister_id = "ryjl3-tyaaa-aaaaa-aaaba-cai"

        command = f'dfx canister call {icp_canister_id} icrc1_balance_of "(record {{ owner = principal \\"{self.user_pid}\\" }})" --ic'
        try:
            balance = self._subprocess(command)
            
            # Extract the numeric part from the returned string using a regular expression
            match = re.search(r'\(([\d_]+) : nat\)', balance)
            if match:
                numeric_balance = int(match.group(1).replace('_', ''))  # 
                self.open_msg_dialog(f"ICP Balance: {numeric_balance}")
            else:
                self.open_msg_dialog("Invalid balance format returned.")
        except Exception as e:
            print(e)
            self.open_msg_dialog("Error fetching ICP balance.")

    def get_oro_balance(self):
        oro_canister_id = "ryjl3-tyaaa-aaaaa-aaaba-cai" # currently set to ICP canister id

        command = f'dfx canister call {oro_canister_id} icrc1_balance_of "(record {{ owner = principal \\"{self.user_pid}\\" }})" --ic'
        try:
            balance = self._subprocess(command)
            
            # Extract the numeric part from the returned string using a regular expression
            match = re.search(r'\(([\d_]+) : nat\)', balance)
            if match:
                numeric_balance = int(match.group(1).replace('_', '' ) )  # 
                self.open_msg_dialog(f"ORO Balance: {numeric_balance}")
            else:
                self.open_msg_dialog("Invalid balance format returned.")
        except Exception as e:
            print(e)
            self.open_msg_dialog("Error fetching ORO balance.")

    def get_ckETH_balance(self):
        ckETH_canister_id = "ss2fx-dyaaa-aaaar-qacoq-cai"

        command = f'dfx canister call {ckETH_canister_id} icrc1_balance_of "(record {{ owner = principal \\"{self.user_pid}\\" }})" --ic'
        try:
            balance = self._subprocess(command)
            
            # Extract the numeric part from the returned string using a regular expression
            match = re.search(r'\(([\d_]+) : nat\)', balance)
            if match:
                numeric_balance = int(match.group(1).replace('_', '' ) )  # 
                self.open_msg_dialog(f"ckETH Balance: {numeric_balance}")
            else:
                self.open_msg_dialog("Invalid balance format returned.")
        except Exception as e:
            print(e)
            self.open_msg_dialog("Error fetching ckETH balance.")

    def get_ckBTC_balance(self):
        ckBTC_canister_id = "mxzaz-hqaaa-aaaar-qaada-cai"

        command = f'dfx canister call {ckBTC_canister_id} icrc1_balance_of "(record {{ owner = principal \\"{self.user_pid}\\" }})" --ic'
        try:
            balance = self._subprocess(command)
            
            # Extract the numeric part from the returned string using a regular expression
            match = re.search(r'\(([\d_]+) : nat\)', balance)
            if match:
                numeric_balance = int(match.group(1).replace('_', '' ) )  # 
                self.open_msg_dialog(f"ckBTC Balance: {numeric_balance}")
            else:
                self.open_msg_dialog("Invalid balance format returned.")
        except Exception as e:
            print(e)
            self.open_msg_dialog("Error fetching ckBTC balance.")

    def generate_store_token(self):
        try:
            builder = BiscuitBuilder()
            
            account_name = self._subprocess('dfx identity whoami').strip()
            oro_balance = 1000

            # Add facts to the token
            builder.add_fact(Fact(f'account_name("{account_name}")'))
            builder.add_fact(Fact(f'account_principal("{self.user_pid}")'))
            builder.add_fact(Fact(f'account_oro_balance({oro_balance})'))

            # Add expiration timestamp as a fact
            expiration_time = (datetime.now(tz=timezone.utc) + timedelta(hours=8)).timestamp()
            print(expiration_time)
            builder.add_fact(Fact(f'Timestamp("{expiration_time}")'))

            # Build and serialize the token
            token = builder.build(self.private_key)
            serialized_token = bytes(token.to_bytes())
            token_path = os.path.join(self.PATH, 'auth_token.enc')

            # Write the token securely (restrict access to owner)
            with open(token_path, 'wb') as token_file:
                token_file.write(serialized_token)
            os.chmod(token_path, 0o600)

        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error generating and storing token.")

    def authorize_token(self):
        try:
            s_token = self.get_serialized_token()
            tkn = Biscuit.from_bytes(s_token, self.public_key)
            authorizer = Authorizer("""
                                    allow if account_principal({p});
                                    """,{ "p": f'{self.user_pid}'})
            authorizer.add_token(tkn)
            idx = authorizer.authorize()
            print("token authorized (index): ",idx)
            return True
        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error authorizing token.")
            return False

    def get_serialized_token(self):
        try:
            token_path = os.path.join(self.PATH, 'auth_token.enc')
            if not os.path.exists(token_path):
                self.open_msg_dialog("No token found.")
                return
            
            with open(token_path, 'rb') as token_file:
                serialized_token = token_file.read()
            
            return serialized_token

        except Exception as e:
            # Show error message
            print(e)
            self.open_msg_dialog("Error fetching token.")

    def authorization_loop(self):
        while True:
            # print("Generating new token and authorizing...")
            # self.generate_store_token()
            authorized = self.authorize_token()
            if authorized:
                print("Token authorized. Sleeping for 8 hours...")
            else:
                print("Token authorization failed. Retrying in 10 seconds...")
            time.sleep(self.refresh_interval if authorized else 10)

    def _subprocess(self, command):
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return output.decode('utf-8')
        except Exception as e:
            return None
        
    def run_press(self):
        self._subprocess(str(self.PRESS))

    def splash(self):
        return(self._subprocess(f'{str(self.HVYM)} splash'))

    def new_ic_account(self):
        return(self._subprocess(f'{str(self.HVYM)} icp-new-account'))

    def new_ic_test_account(self):
        return(self._subprocess(f'{str(self.HVYM)} icp-new-test-account'))

    def change_ic_account(self):
        return(self._subprocess(f'{str(self.HVYM)} icp-set-account'))

    def remove_ic_account(self):
        return(self._subprocess(f'{str(self.HVYM)} icp-remove-account'))
    
    def get_ic_principal(self):
        return(self._subprocess(f'{str(self.HVYM)} icp-active-principal'))

    def hvym_check(self):
        return(self._subprocess(f'{str(self.HVYM)} check'))

    def update_tools(self):
        update = self.open_confirm_dialog('You want to update Heavymeta Tools?')
        if update == True:
            self._update_blender_addon(self.BLENDER_VERSION)
            if self.HVYM.is_file():
                self._update_cli()
                self._subprocess(f'{str(self.HVYM)} update-npm-modules')
            if self.PRESS.is_file():
                self._update_press()

    def _installation_check(self):
        if not self.HVYM.is_file():
            print('Install the cli')
            self._install_hvym()
        else:
            print('hvym is installed')
            check = self.hvym_check()
            if check != None and check.strip() == 'ONE-TWO':
                print('hvym is on path')

    def _install_hvym(self):
        install = self.open_confirm_dialog('Install Heavymeta cli?')
        if install == True:
            loading = self.loading_indicator('UPDATING HVYM')
            loading.Play()
            installed = self._subprocess('curl -L https://github.com/inviti8/hvym/raw/main/install.sh | bash')
            check = self.hvym_check()
            if installed != None and check != None and check.strip() == 'ONE-TWO':
                print('hvym is on path')
                print(str(self.HVYM))
                self._subprocess(f'{str(self.HVYM)} up')
                self._subprocess('. ~/.bashrc')
            else:
                print('hvym not installed.')
            loading.Stop()
            self.restart()

    def _update_hvym(self):
        update = self.open_confirm_dialog('Update Heavymeta cli?')
        if update == True:
            loading = self.loading_indicator('UPDATING')
            loading.Play()
            self._delete_hvym()
            self._install_hvym()
            loading.Stop()

    def _delete_hvym(self):
        if self.HVYM.is_file():
            self.HVYM.unlink

    def _install_blender_addon(self, version):
        install = self.open_confirm_dialog('Install Heavymeta Blender Addon?')
        if install == True:
            if self.BLENDER_PATH.exists() and self.ADDON_INSTALL_PATH.exists():
                loading = self.loading_indicator('Installing Blender Addon')
                loading.Play()
                if not self.ADDON_PATH.exists():
                    _download_unzip('https://github.com/inviti8/heavymeta_standard/archive/refs/heads/main.zip', str(self.ADDON_INSTALL_PATH))
                    self.open_msg_dialog(f'Blender Addon installed. Please restart Daemon.')
                loading.Stop()
                self.restart()
            else:
                self.open_msg_dialog('Blender not found. Please install blender first')

    def _update_blender_addon(self, version):
        self._delete_blender_addon(version)
        self._install_blender_addon(version)

    def _delete_blender_addon(self, version):
        for item in self.ADDON_INSTALL_PATH.iterdir():
                if item.name != '.git' and item.name != 'README.md' and item.name != 'install.sh':
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)

        shutil.rmtree(str(self.ADDON_INSTALL_PATH))

    def _install_press(self):
        install = self.open_confirm_dialog('Install Heavymeta Press?')
        if install == True:
            loading = self.loading_indicator('Installing Heavymeta Press')
            loading.Play()
            self._subprocess('curl -L https://raw.githubusercontent.com/inviti8/hvym_press/refs/heads/main/install.sh | bash')
            self.restart()
            loading.Stop()

    def _delete_press(self):
        if self.PRESS.is_file():
            self.PRESS.unlink

    def _update_press(self):
        update = self.open_confirm_dialog('Update Heavymeta Press?')
        if update == True:
            loading = self.loading_indicator('UPDATING Press')
            loading.Play()
            self._delete_press()
            self._install_press()
            loading.Stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw = Metavinci()
    mw.show()
    mw.setFixedSize(70,70)
    mw.center()
    mw.hide()
    sys.exit(app.exec())

