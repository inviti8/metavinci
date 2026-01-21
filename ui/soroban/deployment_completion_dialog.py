#!/usr/bin/env python3
"""
Deployment Completion Dialog for Soroban Contracts
Shows deployment results and provides access to contract information
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPlainTextEdit,
    QPushButton, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPalette, QColor
from PyQt5.QtWidgets import QApplication

import webbrowser


class DeploymentCompletionDialog(QDialog):
    """Dialog showing deployment completion results"""
    
    def __init__(self, parent=None, deployment_record: dict = None):
        super().__init__(parent)
        self.deployment_record = deployment_record
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle("Deployment Result")
        self.setModal(True)
        self.resize(600, 500)
        
        layout = QVBoxLayout()
        
        if self.deployment_record and self.deployment_record.get("status") == "success":
            # Success UI
            self.setup_success_ui(layout)
        else:
            # Failure UI
            self.setup_failure_ui(layout)
        
        self.setLayout(layout)
    
    def setup_success_ui(self, layout):
        """Setup success UI"""
        # Success Title
        title = QLabel("🎉 Contract Deployment Successful!")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #4CAF50; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Contract Details
        contract_group = QGroupBox("Contract Details")
        contract_layout = QVBoxLayout()
        
        # Contract ID
        contract_id_label = QLabel("Contract ID:")
        contract_id_label.setFont(QFont("Arial", 10, QFont.Bold))
        contract_layout.addWidget(contract_id_label)
        
        contract_id_input = QLineEdit(self.deployment_record["contract_id"])
        contract_id_input.setReadOnly(True)
        contract_id_input.setStyleSheet("background: #f0f0f0; padding: 5px;")
        contract_layout.addWidget(contract_id_input)
        
        # Copy Contract ID Button
        copy_contract_btn = QPushButton("📋 Copy Contract ID")
        copy_contract_btn.clicked.connect(self.copy_contract_id)
        copy_contract_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        contract_layout.addWidget(copy_contract_btn)
        
        contract_group.setLayout(contract_layout)
        layout.addWidget(contract_group)
        
        # Network Information
        network_group = QGroupBox("Network Information")
        network_layout = QVBoxLayout()
        
        network_label = QLabel(f"Network: {self.deployment_record['network'].upper()}")
        wallet_label = QLabel(f"Deployed from: {self.deployment_record['deployment_wallet']}")
        timestamp_label = QLabel(f"Deployed: {self.format_timestamp(self.deployment_record['timestamp'])}")
        
        # Network color coding
        if self.deployment_record['network'] == 'mainnet':
            network_label.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            network_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        
        network_layout.addWidget(network_label)
        network_layout.addWidget(wallet_label)
        network_layout.addWidget(timestamp_label)
        
        # WASM size and fees
        if 'wasm_size' in self.deployment_record:
            size_kb = self.deployment_record['wasm_size'] / 1024
            size_label = QLabel(f"WASM Size: {size_kb:.2f} KB")
            network_layout.addWidget(size_label)
        
        if 'fees_paid' in self.deployment_record:
            fee_xlm = self.deployment_record['fees_paid'] / 10000000
            fee_label = QLabel(f"Fees Paid: {fee_xlm:.7f} XLM")
            network_layout.addWidget(fee_label)
        
        network_group.setLayout(network_layout)
        layout.addWidget(network_group)
        
        # Explorer Links
        links_group = QGroupBox("Explorer Links")
        links_layout = QVBoxLayout()
        
        if self.deployment_record.get("stellar_expert_url"):
            expert_link = QLabel(f'<a href="{self.deployment_record["stellar_expert_url"]}" style="color: #2196F3;">🔗 View on Stellar Expert</a>')
            expert_link.setOpenExternalLinks(True)
            links_layout.addWidget(expert_link)
        
        # Transaction hash link
        if self.deployment_record.get("transaction_hash"):
            tx_hash = self.deployment_record["transaction_hash"]
            if self.deployment_record['network'] == 'mainnet':
                tx_url = f"https://stellar.expert/explorer/mainnet/tx/{tx_hash}"
            else:
                tx_url = f"https://stellar.expert/explorer/testnet/tx/{tx_hash}"
            
            tx_link = QLabel(f'<a href="{tx_url}" style="color: #2196F3;">🔍 View Transaction</a>')
            tx_link.setOpenExternalLinks(True)
            links_layout.addWidget(tx_link)
        
        links_group.setLayout(links_layout)
        layout.addWidget(links_group)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        copy_all_btn = QPushButton("📋 Copy All Details")
        copy_all_btn.clicked.connect(self.copy_all_details)
        copy_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        close_btn = QPushButton("✓ Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        button_layout.addWidget(copy_all_btn)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
    def setup_failure_ui(self, layout):
        """Setup failure UI"""
        # Failure Title
        title = QLabel("❌ Contract Deployment Failed")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #F44336; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Error Information
        error_group = QGroupBox("Error Details")
        error_layout = QVBoxLayout()
        
        # Network info if available
        if self.deployment_record:
            network_label = QLabel(f"Network: {self.deployment_record.get('network', 'Unknown').upper()}")
            wallet_label = QLabel(f"Wallet: {self.deployment_record.get('deployment_wallet', 'Unknown')}")
            timestamp_label = QLabel(f"Attempted: {self.format_timestamp(self.deployment_record.get('timestamp', ''))}")
            
            error_layout.addWidget(network_label)
            error_layout.addWidget(wallet_label)
            error_layout.addWidget(timestamp_label)
        
        error_label = QLabel("Error Message:")
        error_label.setFont(QFont("Arial", 10, QFont.Bold))
        error_layout.addWidget(error_label)
        
        error_text = QPlainTextEdit(
            self.deployment_record.get("error", "Unknown error occurred") if self.deployment_record else "Unknown error occurred"
        )
        error_text.setReadOnly(True)
        error_text.setMaximumHeight(150)
        error_text.setStyleSheet("background: #ffebee; border: 1px solid #f44336;")
        error_layout.addWidget(error_text)
        
        error_group.setLayout(error_layout)
        layout.addWidget(error_group)
        
        # Troubleshooting Tips
        tips_group = QGroupBox("Troubleshooting Tips")
        tips_layout = QVBoxLayout()
        
        tips = [
            "• Check if wallet has sufficient XLM balance (minimum 2 XLM required)",
            "• Verify network connectivity",
            "• Ensure Soroban CLI is properly installed",
            "• Check if contract WASM file is valid",
            "• Try again with a different wallet if available"
        ]
        
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setWordWrap(True)
            tips_layout.addWidget(tip_label)
        
        tips_group.setLayout(tips_layout)
        layout.addWidget(tips_group)
        
        # Close Button
        close_button = QPushButton("✖ Close")
        close_button.clicked.connect(self.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        layout.addWidget(close_button)
    
    def copy_contract_id(self):
        """Copy contract ID to clipboard"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.deployment_record["contract_id"])
        QMessageBox.information(self, "Copied", "Contract ID copied to clipboard")
    
    def copy_all_details(self):
        """Copy all deployment details to clipboard"""
        if not self.deployment_record:
            return
        
        details = f"""Contract Deployment Details
==========================
Contract ID: {self.deployment_record.get('contract_id', 'N/A')}
Network: {self.deployment_record.get('network', 'N/A').upper()}
Wallet: {self.deployment_record.get('deployment_wallet', 'N/A')}
Timestamp: {self.format_timestamp(self.deployment_record.get('timestamp', 'N/A'))}
Status: {self.deployment_record.get('status', 'N/A')}

Transaction Hash: {self.deployment_record.get('transaction_hash', 'N/A')}
Stellar Expert URL: {self.deployment_record.get('stellar_expert_url', 'N/A')}

WASM Size: {self.deployment_record.get('wasm_size', 'N/A')} bytes
Fees Paid: {self.deployment_record.get('fees_paid', 'N/A')} stroops
"""
        
        clipboard = QApplication.clipboard()
        clipboard.setText(details)
        QMessageBox.information(self, "Copied", "All deployment details copied to clipboard")
    
    def format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display"""
        if not timestamp:
            return "Unknown"
        
        try:
            # Remove microseconds and add space before time
            formatted = timestamp[:19].replace("T", " ")
            return formatted
        except Exception:
            return timestamp
    
    def open_explorer(self, url: str):
        """Open Stellar Expert URL"""
        try:
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open browser: {str(e)}")
