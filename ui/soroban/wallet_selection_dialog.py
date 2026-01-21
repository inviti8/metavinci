#!/usr/bin/env python3
"""
Wallet Selection Dialog for Soroban Contract Deployment
Allows users to select a wallet for contract deployment operations
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QLineEdit, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from wallet_manager import WalletManager


class WalletSelectionDialog(QDialog):
    """Dialog for selecting wallet for Soroban deployment"""
    
    def __init__(self, parent=None, network: str = "testnet"):
        super().__init__(parent)
        self.network = network
        self.selected_wallet = None
        self.wallet_password = None
        self.wallet_manager = WalletManager()
        self.setup_ui()
        self.load_wallets()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Select Deployment Wallet")
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Title
        title = QLabel(f"Select Wallet for {self.network.upper()} Deployment")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Network warning
        if self.network == "mainnet":
            warning = QLabel("⚠️ Mainnet Deployment - Real XLM will be used")
            warning.setStyleSheet("color: red; font-weight: bold; padding: 10px;")
            warning.setAlignment(Qt.AlignCenter)
            layout.addWidget(warning)
        
        # Wallet List
        wallet_label = QLabel("Available Wallets:")
        wallet_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(wallet_label)
        
        self.wallet_list = QListWidget()
        self.wallet_list.itemDoubleClicked.connect(self.accept_wallet)
        layout.addWidget(self.wallet_list)
        
        # Password Input (for mainnet)
        self.password_widget = QWidget()
        password_layout = QVBoxLayout()
        
        password_label = QLabel("Wallet Password:")
        password_label.setFont(QFont("Arial", 10, QFont.Bold))
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter wallet password for mainnet deployment...")
        password_layout.addWidget(self.password_input)
        
        self.password_widget.setLayout(password_layout)
        layout.addWidget(self.password_widget)
        
        # Initially hide password widget
        self.password_widget.hide()
        
        # Balance Info
        self.balance_label = QLabel("")
        self.balance_label.setStyleSheet("color: #666; font-size: 9px;")
        layout.addWidget(self.balance_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.ok_button = QPushButton("Select Wallet")
        self.ok_button.clicked.connect(self.accept_wallet)
        self.ok_button.setEnabled(False)  # Disabled until wallet selected
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Connect wallet selection
        self.wallet_list.itemSelectionChanged.connect(self.on_wallet_selection_changed)
    
    def load_wallets(self):
        """Load wallets for current network"""
        try:
            wallets = self.wallet_manager.list_wallets(network=self.network)
            
            self.wallet_list.clear()
            
            if not wallets:
                no_wallets_item = QListWidgetItem(f"No {self.network} wallets found")
                no_wallets_item.setData(Qt.UserRole, None)
                self.wallet_list.addItem(no_wallets_item)
                return
            
            for wallet in wallets:
                # Create wallet item with label and address
                display_name = wallet.label or "Unnamed Wallet"
                address_short = wallet.address[:8] + "..." + wallet.address[-4:]
                
                item_text = f"{display_name}\n{address_short}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, wallet)
                
                # Set tooltip with full address
                item.setToolTip(f"Address: {wallet.address}\nNetwork: {wallet.network}")
                
                self.wallet_list.addItem(item)
            
            # Show password widget if mainnet
            if self.network == "mainnet":
                self.password_widget.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load wallets: {str(e)}")
    
    def on_wallet_selection_changed(self):
        """Handle wallet selection change"""
        current_item = self.wallet_list.currentItem()
        
        if current_item and current_item.data(Qt.UserRole):
            self.ok_button.setEnabled(True)
            wallet = current_item.data(Qt.UserRole)
            
            # Show balance info
            try:
                balance = self.wallet_manager.get_balance(wallet.address, wallet.network)
                if balance and 'balance' in balance:
                    balance_amount = balance['balance']
                    self.balance_label.setText(f"Balance: {balance_amount} XLM")
                else:
                    self.balance_label.setText("Balance: Unknown")
            except Exception:
                self.balance_label.setText("Balance: Unable to fetch")
        else:
            self.ok_button.setEnabled(False)
            self.balance_label.setText("")
    
    def accept_wallet(self):
        """Handle wallet selection"""
        current_item = self.wallet_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a wallet")
            return
        
        wallet = current_item.data(Qt.UserRole)
        if not wallet:
            QMessageBox.warning(self, "Invalid Selection", "Please select a valid wallet")
            return
        
        # Validate password for mainnet
        if self.network == "mainnet":
            password = self.password_input.text()
            if not password:
                QMessageBox.warning(self, "Password Required", "Please enter wallet password for mainnet deployment")
                return
            
            # Test password decryption
            try:
                self.wallet_manager.get_secret_key(wallet.address, password)
            except Exception as e:
                QMessageBox.critical(self, "Invalid Password", f"Wallet password is incorrect: {str(e)}")
                return
            
            self.wallet_password = password
        
        self.selected_wallet = wallet
        self.accept()
    
    def get_selected_wallet(self):
        """Return selected wallet and password"""
        return self.selected_wallet, self.wallet_password
