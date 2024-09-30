from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QCheckBox, QSystemTrayIcon, QSpacerItem, QSizePolicy, QMenu, QAction, QStyle, qApp, QVBoxLayout, QPushButton, QDialog
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon
from pathlib import Path
import subprocess
import os
import stat
from urllib.request import urlopen
from zipfile import ZipFile
from tinydb import TinyDB, Query
from gradientmessagebox import *
import click
import getpass
import shutil
from biscuit_auth import KeyPair,PrivateKey, PublicKey,BiscuitBuilder,Fact,Authorizer,Biscuit
from cryptography.fernet import Fernet
import json
import re
from datetime import datetime, timedelta, timezone
import time

HOME = os.path.expanduser('~')
FILE_PATH = Path(__file__).parent
CWD = Path.cwd()
SERVICE_RUN_DEST = CWD / '.metavinci'
SERVICE_RUN_FILE = os.path.join(HOME, '.metavinci', 'run.sh')
SERVICE_START = os.path.join(FILE_PATH, 'service', 'start.sh')
APP_ICON_FILE = os.path.join(HOME, '.metavinci', 'app_icon.png')
APP_ICON = os.path.join(FILE_PATH, 'images', 'app_icon.png')
DB_PATH = os.path.join(FILE_PATH, 'data', 'db.json')
FG_TXT_COLOR = '#98314a'

def _config_popup(popup):
      popup.fg_luminance(0.8)
      popup.bg_saturation(0.6)
      popup.bg_luminance(0.4)
      popup.custom_msg_color(FG_TXT_COLOR)

def _choice_popup(msg):
      """ Show choice popup, message based on passed msg arg."""
      popup = PresetChoiceWindow(msg)
      _config_popup(popup)
      result = popup.Ask()
      return result.response


def _prompt_popup(msg, wide=False):
      """ Show choice popup, message based on passed msg arg."""
      popup = PresetPromptWindow(msg)
      if wide:
        popup = PresetWidePromptWindow(msg)

      _config_popup(popup)
      result = popup.Prompt()


def _loading_message(msg):
    loading = PresetLoadingMessage(msg)
    _config_popup(loading)
    return loading


def _download_unzip(url, out_path):
      with urlopen(url) as zipresp:
          with ZipFile(BytesIO(zipresp.read())) as zfile:
              zfile.extractall(out_path)


def _subprocess(command):
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return output.decode('utf-8')
        except Exception as e:
            return None

def _install_hvym():
    _subprocess('curl -L https://github.com/inviti8/hvym/raw/main/install.sh | bash')
    if _subprocess('hvym check').strip() == 'ONE-TWO':
        print('hvym is on path')
        _subprocess('hvym splash')
    else:
        print('hvym not installed.')


def _install_icon():
    if not os.path.isfile(str(APP_ICON_FILE)):
        shutil.copy(str(APP_ICON), SERVICE_RUN_DEST)
     
class Metavinci(QMainWindow):
    """
        Network Daemon for Heavymeta
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
        self.UPDATE_IMG = os.path.join(self.FILE_PATH, 'images', 'update.png')
        self.ICP_LOGO_IMG = os.path.join(self.FILE_PATH, 'images', 'icp_logo.png')
        self.icon = QIcon(self.LOGO_IMG)
        self.update_icon = QIcon(self.UPDATE_IMG)
        self.ic_icon = QIcon(self.ICP_LOGO_IMG)
        self.user_pid = self._subprocess('hvym icp-principal').strip()
        self.metavinci_dir = os.path.join(self.HOME, '.metavinci')
        self.publik_key = None
        self.private_key = None
        self.refresh_interval = 8 * 60 * 60  # 8 hours in seconds

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
        icp_balance_action = QAction("ICP Balance", self)
        oro_balance_action = QAction("ORO Balance", self)
        ckETH_balance_action = QAction("ckETH Balance", self)
        ckBTC_balance_action = QAction("ckBTC Balance", self)
        update_tools_action = QAction(self.update_icon, "Update Tools", self)
        quit_action = QAction("Exit", self)
        icp_new_account_action.triggered.connect(self.new_ic_account)
        icp_change_account_action.triggered.connect(self.change_ic_account)
        icp_balance_action.triggered.connect(self.get_icp_balance)
        oro_balance_action.triggered.connect(self.get_oro_balance)
        ckETH_balance_action.triggered.connect(self.get_ckETH_balance)
        ckBTC_balance_action.triggered.connect(self.get_ckBTC_balance)
        update_tools_action.triggered.connect(self.update_tools)

        # Add a new action for tasks
        task_action = QAction("Show Tasks", self)
        task_action.triggered.connect(self.show_tasks_popup)

        quit_action.triggered.connect(qApp.quit)
        tray_menu = QMenu()
        tray_accounts_menu = tray_menu.addMenu("Accounts")
        tray_accounts_menu.addAction(icp_new_account_action)
        tray_accounts_menu.addAction(icp_change_account_action)
        tray_balances_menu = tray_menu.addMenu("Balances")
        tray_balances_menu.addAction(icp_balance_action)
        tray_balances_menu.addAction(oro_balance_action)
        tray_balances_menu.addAction(ckETH_balance_action)
        tray_balances_menu.addAction(ckBTC_balance_action)
        tray_menu.addAction(task_action)
        tray_menu.addAction(update_tools_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self._installation_check()
        self.generate_store_keypair()
        self.import_keys()
     
    def show_tasks_popup(self):
        #Create a dict for popup buttons
        tasks = {
            "Generate and Store App Keypair" : self.generate_store_keypair,
            "Import App Keypair" : self.import_keys,
            "Generate and Store Token" : self.generate_store_token,
            "Start Authorization Loop" : self.authorization_loop
        }
        #create the popup
        popup = PresetMultiButtonWindow(tasks)
        popup.Show()

    # Task function for generating and storing the app keypair using biscuit-python
    def generate_store_keypair(self):
        try:
            # Generate keypair using biscuit-python
            keypair = KeyPair()

            serialized_keys = {
                "private_key": keypair.private_key.to_hex(),
                "public_key": keypair.public_key.to_hex()
            }
            
            # print("key generated & stored : ",serialized_keys)
            # locate .metavinci directory in user's home directory
            meta_dir = os.path.join(HOME, '.metavinci')
            if not os.path.exists(meta_dir):
                os.makedirs(meta_dir, mode=0o700)  # Create directory with secure permissions

            # # Generate a symmetric encryption key
            encryption_key = Fernet.generate_key()
            cipher_suite = Fernet(encryption_key)

            serialized_keys_str = json.dumps(serialized_keys)
            encrpted_keys = cipher_suite.encrypt(serialized_keys_str.encode())

            keystore_path = os.path.join(meta_dir, 'keystore.enc')
            encryption_key_path = os.path.join(meta_dir, 'encryption_key.key')

            # # # Write the private key securely (restrict access to owner)
            with open(keystore_path, 'wb') as keystore_file:
                keystore_file.write(encrpted_keys)
            os.chmod(keystore_path, 0o600)

            # # # Write the encryption key
            with open(encryption_key_path, 'wb') as encrypt_key_file:
                encrypt_key_file.write(encryption_key)

            # # Show success message
            _prompt_popup("keypair generated and stored successfully at : "+keystore_path, True)
        except Exception as e:
            # Show error message
            print(e)
            _prompt_popup("Error generating and storing app keypair.")

    def import_keys(self):
        try:
            # locate .metavinci directory in user's home directory
            meta_dir = os.path.join(HOME, '.metavinci')
            if not os.path.exists(meta_dir):
                os.makedirs(meta_dir, mode=0o700)
            
            # Read the encrypted keys
            keystore_path = os.path.join(meta_dir, 'keystore.enc')
            encrypt_key_path = os.path.join(meta_dir, 'encryption_key.key')

            if not os.path.exists(keystore_path) or not os.path.exists(encrypt_key_path):
                _prompt_popup("No keypair found to import.")
                return
            
            with open(encrypt_key_path, 'rb') as encrypt_key_file:
                encryption_key = encrypt_key_file.read()
            cipher_suite = Fernet(encryption_key)

            with open(keystore_path, 'rb') as keystore_file:
                encrypted_keys = keystore_file.read()

            decrypted_keys = cipher_suite.decrypt(encrypted_keys)
            serialized_keys = json.loads(decrypted_keys)

            # print("key imported : ",serialized_keys)
            self.private_key = PrivateKey.from_hex(serialized_keys['private_key'])
            self.public_key = PublicKey.from_hex(serialized_keys['public_key'])

            # Show success message
            _prompt_popup("keypair imported successfully.")
        except Exception as e:
            # Show error message
            print(e)
            _prompt_popup("Error importing app keypair.")

    def get_icp_balance(self):
        icp_canister_id = "ryjl3-tyaaa-aaaaa-aaaba-cai"

        command = f'dfx canister call {icp_canister_id} icrc1_balance_of "(record {{ owner = principal \\"{self.user_pid}\\" }})" --ic'
        try:
            balance = self._subprocess(command)
            
            # Extract the numeric part from the returned string using a regular expression
            match = re.search(r'\(([\d_]+) : nat\)', balance)
            if match:
                numeric_balance = int(match.group(1).replace('_', ''))  # 
                _prompt_popup(f"ICP Balance: {numeric_balance}")
            else:
                _prompt_popup("Invalid balance format returned.")
        except Exception as e:
            print(e)
            _prompt_popup("Error fetching ICP balance.")

    def get_oro_balance(self):
        oro_canister_id = "ryjl3-tyaaa-aaaaa-aaaba-cai" # currently set to ICP canister id

        command = f'dfx canister call {oro_canister_id} icrc1_balance_of "(record {{ owner = principal \\"{self.user_pid}\\" }})" --ic'
        try:
            balance = self._subprocess(command)
            
            # Extract the numeric part from the returned string using a regular expression
            match = re.search(r'\(([\d_]+) : nat\)', balance)
            if match:
                numeric_balance = int(match.group(1).replace('_', '' ) )  # 
                _prompt_popup(f"ORO Balance: {numeric_balance}")
            else:
                _prompt_popup("Invalid balance format returned.")
        except Exception as e:
            print(e)
            _prompt_popup("Error fetching ORO balance.")

    def get_ckETH_balance(self):
        ckETH_canister_id = "ss2fx-dyaaa-aaaar-qacoq-cai"

        command = f'dfx canister call {ckETH_canister_id} icrc1_balance_of "(record {{ owner = principal \\"{self.user_pid}\\" }})" --ic'
        try:
            balance = self._subprocess(command)
            
            # Extract the numeric part from the returned string using a regular expression
            match = re.search(r'\(([\d_]+) : nat\)', balance)
            if match:
                numeric_balance = int(match.group(1).replace('_', '' ) )  # 
                _prompt_popup(f"ckETH Balance: {numeric_balance}")
            else:
                _prompt_popup("Invalid balance format returned.")
        except Exception as e:
            print(e)
            _prompt_popup("Error fetching ckETH balance.")

    def get_ckBTC_balance(self):
        ckBTC_canister_id = "mxzaz-hqaaa-aaaar-qaada-cai"

        command = f'dfx canister call {ckBTC_canister_id} icrc1_balance_of "(record {{ owner = principal \\"{self.user_pid}\\" }})" --ic'
        try:
            balance = self._subprocess(command)
            
            # Extract the numeric part from the returned string using a regular expression
            match = re.search(r'\(([\d_]+) : nat\)', balance)
            if match:
                numeric_balance = int(match.group(1).replace('_', '' ) )  # 
                _prompt_popup(f"ckBTC Balance: {numeric_balance}")
            else:
                _prompt_popup("Invalid balance format returned.")
        except Exception as e:
            print(e)
            _prompt_popup("Error fetching ckBTC balance.")

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
            token_path = os.path.join(self.metavinci_dir, 'auth_token.enc')

            # Write the token securely (restrict access to owner)
            with open(token_path, 'wb') as token_file:
                token_file.write(serialized_token)
            os.chmod(token_path, 0o600)

        except Exception as e:
            # Show error message
            print(e)
            _prompt_popup("Error generating and storing token.")

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
            _prompt_popup("Error authorizing token.")
            return False

    def get_serialized_token(self):
        try:
            token_path = os.path.join(self.metavinci_dir, 'auth_token.enc')
            if not os.path.exists(token_path):
                _prompt_popup("No token found.")
                return
            
            with open(token_path, 'rb') as token_file:
                serialized_token = token_file.read()
            
            return serialized_token

        except Exception as e:
            # Show error message
            print(e)
            _prompt_popup("Error fetching token.")

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
    def _subprocess(self, command):
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            return output.decode('utf-8')
        except Exception as e:
            return None

    def new_ic_account(self):
        return(self._subprocess(f'{self.HVYM} icp-new-account'))

    def change_ic_account(self):
        return(self._subprocess(f'{self.HVYM} icp-set-account'))

    def hvym_check(self):
        return(self._subprocess(f'{self.HVYM} check'))

    def update_tools(self):
        answer = _choice_popup('You want to update Heavymeta Tools?')
        home = Path.home()
        hvym = home / '.local' / 'share' / 'heavymeta-cli' / 'hvym'
        print(hvym)
        _prompt_popup(str(hvym))

        if answer.response == 'OK':
            loading= _loading_message('UPDATING')
            loading.Play()
            _update_blender_addon(version)
            _update_cli()
            self._subprocess(f'{self.HVYM} update-npm-modules')
            loading.Close()

    def _installation_check(self):
        if not os.path.isfile(self.HVYM):
            print('Install the cli')
            self._install_hvym()
        else:
            print('hvym is installed')
            check = self.hvym_check()
            if check != None and check.strip() == 'ONE-TWO':
                print('hvym is on path')

    def _install_hvym(self):
        installed = self._subprocess('curl -L https://github.com/inviti8/hvym/raw/main/install.sh | bash')
        check = self.hvym_check()
        if installed != None and check != None and check.strip() == 'ONE-TWO':
            print('hvym is on path')
            print(self.HVYM)
            self._subprocess(f'{self.HVYM} up')
            self._subprocess('. ~/.bashrc')
        else:
            print('hvym not installed.')

    def _delete_hvym(self):
        home = Path.home()
        hvym = home / '.local' / 'share' / 'heavymeta-cli' / 'hvym'
        
        hvym.unlink

    def _delete_blender_addon(self, version):
        home = Path.home()
        addon_dir = home / '.config' / 'blender' / version /'scripts' / 'addons' / 'heavymeta_standard'
        for item in addon_dir.iterdir():
                if item.name != '.git' and item.name != 'README.md' and item.name != 'install.sh':
                    if item.is_file():
                        item.unlink()
                    else:
                        shutil.rmtree(item)

        shutil.rmtree(addon_dir)

    def _install_blender_addon(self, version):
        home = Path.home()
        addon_dir = home / '.config' / 'blender' / version /'scripts' / 'addons' 
        _download_unzip('https://github.com/inviti8/heavymeta_standard/archive/refs/heads/main.zip', str(addon_dir))

    def _update_blender_addon(self, version):
        self._delete_blender_addon(version)
        self._install_blender_addon(version)

    def _update_cli(self):
        self._delete_hvym()
        self._install_hvym()

         

@click.command()
def up():
    import sys
    app = QApplication(sys.argv)
    mw = Metavinci()
    #mw.show()
    sys.exit(app.exec())
    click.echo("Metavinci up")

@click.command()
def start():
    self._subprocess('sudo systemctl start metavinci')

@click.command()
def stop():
    self._subprocess('sudo systemctl stop metavinci')

if __name__ == "__main__":
    if not os.path.isfile(str(APP_ICON_FILE)):
        #DO INSTALL
        click.echo('Metavinci needs permission to start a system service:')
        st = os.stat(SERVICE_START)
        os.chmod(SERVICE_START, st.st_mode | stat.S_IEXEC)
        _install_icon()
        metavinci = str(SERVICE_RUN_DEST)
        cmd = f'sudo {SERVICE_START} {getpass.getuser()} "{metavinci}"'
        output = subprocess.check_output(f'sudo {SERVICE_START} {getpass.getuser()} "{metavinci}"', shell=True, stderr=subprocess.STDOUT)
        click.echo(output.decode('utf-8'))

    up()
    click.echo("Metavinci Installed, close this terminal.")

