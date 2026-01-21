#!/usr/bin/env python3
"""
Deployment List Dialog for Soroban Contracts
Displays and manages deployment history
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QPushButton, QComboBox, QMessageBox, QHeaderView, QWidget, QMenu
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette

import webbrowser
from deployment_manager import DeploymentManager


class DeploymentListDialog(QDialog):
    """Dialog for viewing and managing Soroban deployments"""
    
    def __init__(self, parent=None, network: str = "testnet"):
        super().__init__(parent)
        self.network = network
        self.deployment_manager = DeploymentManager()
        self.setup_ui()
        self.load_deployments()
        
        # Auto-refresh every 30 seconds
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.load_deployments)
        self.refresh_timer.start(30000)  # 30 seconds
    
    def setup_ui(self):
        """Setup the dialog UI"""
        self.setWindowTitle(f"Soroban Deployments - {self.network.upper()}")
        self.setModal(False)
        self.resize(1000, 600)
        
        layout = QVBoxLayout()
        
        # Header with title and refresh
        header_layout = QHBoxLayout()
        
        title = QLabel(f"Soroban Deployments - {self.network.upper()}")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_deployments)
        refresh_btn.setStyleSheet("""
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
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Network filter
        network_label = QLabel("Network:")
        network_label.setFont(QFont("Arial", 10, QFont.Bold))
        filter_layout.addWidget(network_label)
        
        self.network_filter = QComboBox()
        self.network_filter.addItems(["All", "Testnet", "Mainnet", "Futurenet"])
        self.network_filter.setCurrentText(self.network.capitalize())
        self.network_filter.currentTextChanged.connect(self.filter_deployments)
        filter_layout.addWidget(self.network_filter)
        
        filter_layout.addStretch()
        
        # Status filter
        status_label = QLabel("Status:")
        status_label.setFont(QFont("Arial", 10, QFont.Bold))
        filter_layout.addWidget(status_label)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Success", "Failed", "Pending", "Error"])
        self.status_filter.currentTextChanged.connect(self.filter_deployments)
        filter_layout.addWidget(self.status_filter)
        
        # Search
        search_label = QLabel("Search:")
        search_label.setFont(QFont("Arial", 10, QFont.Bold))
        filter_layout.addWidget(search_label)
        
        self.search_input = QPushButton("🔍 Search")
        self.search_input.clicked.connect(self.show_search_dialog)
        filter_layout.addWidget(self.search_input)
        
        layout.addLayout(filter_layout)
        
        # Deployment Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Contract ID", "Network", "Wallet", "Date", "Status", "Explorer", "Actions"
        ])
        
        # Configure table
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        # Set column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Contract ID
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Network
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Wallet
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Explorer
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Actions
        
        layout.addWidget(self.table)
        
        # Status Bar
        self.status_label = QLabel("Loading deployments...")
        self.status_label.setStyleSheet("color: #666; font-size: 9px;")
        layout.addWidget(self.status_label)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("📊 Export")
        export_btn.clicked.connect(self.export_deployments)
        export_btn.setStyleSheet("""
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
        
        cleanup_btn = QPushButton("🧹 Cleanup Old")
        cleanup_btn.clicked.connect(self.cleanup_old_deployments)
        cleanup_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        
        close_btn = QPushButton("✖ Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
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
        
        button_layout.addWidget(export_btn)
        button_layout.addWidget(cleanup_btn)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Setup context menu for table
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
    
    def load_deployments(self):
        """Load deployment records"""
        try:
            network_filter = self.network_filter.currentText().lower()
            if network_filter == "all":
                network_filter = None
            
            status_filter = self.status_filter.currentText().lower()
            if status_filter == "all":
                status_filter = None
            
            deployments = self.deployment_manager.get_deployments(
                network=network_filter, 
                status=status_filter
            )
            
            self.table.setRowCount(len(deployments))
            self.status_label.setText(f"Found {len(deployments)} deployments")
            
            for row, deployment in enumerate(deployments):
                self.populate_table_row(row, deployment)
                
        except Exception as e:
            self.status_label.setText(f"Error loading deployments: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load deployments: {str(e)}")
    
    def populate_table_row(self, row: int, deployment: dict):
        """Populate a single table row with deployment data"""
        # Contract ID
        contract_id = deployment.get("contract_id", "")
        contract_item = QTableWidgetItem(contract_id[:12] + "..." if len(contract_id) > 15 else contract_id)
        contract_item.setToolTip(contract_id)
        contract_item.setData(Qt.UserRole, deployment)  # Store full deployment data
        self.table.setItem(row, 0, contract_item)
        
        # Network with color coding
        network = deployment.get("network", "unknown")
        network_item = QTableWidgetItem(network.upper())
        if network == "mainnet":
            network_item.setBackground(QColor("#ffebee"))
            network_item.setToolTip("Mainnet deployment (real XLM)")
        elif network == "testnet":
            network_item.setBackground(QColor("#e8f5e8"))
            network_item.setToolTip("Testnet deployment (test XLM)")
        else:
            network_item.setBackground(QColor("#fff3e0"))
            network_item.setToolTip(f"{network.capitalize()} deployment")
        self.table.setItem(row, 1, network_item)
        
        # Wallet
        wallet_name = deployment.get("deployment_wallet", "Unknown")
        wallet_item = QTableWidgetItem(wallet_name)
        wallet_item.setToolTip(f"Address: {deployment.get('wallet_address', 'N/A')}")
        self.table.setItem(row, 2, wallet_item)
        
        # Date
        timestamp = deployment.get("timestamp", "")
        if timestamp:
            date_str = timestamp[:19].replace("T", " ")
        else:
            date_str = "Unknown"
        date_item = QTableWidgetItem(date_str)
        self.table.setItem(row, 3, date_item)
        
        # Status with icon and color
        status = deployment.get("status", "unknown")
        status_item = QTableWidgetItem(status.title())
        
        if status == "success":
            status_item.setText("✅ Success")
            status_item.setBackground(QColor("#e8f5e8"))
            status_item.setForeground(QColor("#2e7d32"))
        elif status == "failed":
            status_item.setText("❌ Failed")
            status_item.setBackground(QColor("#ffebee"))
            status_item.setForeground(QColor("#c62828"))
        elif status == "pending":
            status_item.setText("⏳ Pending")
            status_item.setBackground(QColor("#fff3e0"))
            status_item.setForeground(QColor("#f57c00"))
        else:
            status_item.setText("❓ Error")
            status_item.setBackground(QColor("#fce4ec"))
            status_item.setForeground(QColor("#ad1457"))
        
        self.table.setItem(row, 4, status_item)
        
        # Explorer Link
        if deployment.get("stellar_expert_url"):
            explorer_btn = QPushButton("🔗 View")
            explorer_btn.clicked.connect(lambda checked, url=deployment["stellar_expert_url"]: self.open_explorer(url))
            explorer_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 4px;
                    border-radius: 3px;
                    font-size: 9px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            self.table.setCellWidget(row, 5, explorer_btn)
        
        # Actions
        actions_widget = QWidget()
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(2, 2, 2, 2)
        
        copy_btn = QPushButton("📋 ID")
        copy_btn.clicked.connect(lambda checked, cid=deployment.get("contract_id", ""): self.copy_contract_id(cid))
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 4px;
                border-radius: 3px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        details_btn = QPushButton("📄 Details")
        details_btn.clicked.connect(lambda checked, d=deployment: self.show_deployment_details(d))
        details_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 4px;
                border-radius: 3px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.clicked.connect(lambda checked, did=deployment.get("deployment_id", ""): self.delete_deployment(did))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border: none;
                padding: 4px;
                border-radius: 3px;
                font-size: 9px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        actions_layout.addWidget(copy_btn)
        actions_layout.addWidget(details_btn)
        actions_layout.addWidget(delete_btn)
        actions_widget.setLayout(actions_layout)
        
        self.table.setCellWidget(row, 6, actions_widget)
    
    def filter_deployments(self):
        """Apply current filters and reload"""
        self.load_deployments()
    
    def show_search_dialog(self):
        """Show search dialog"""
        from PyQt5.QtWidgets import QInputDialog
        
        search_term, ok = QInputDialog.getText(
            self, "Search Deployments", 
            "Enter contract ID, wallet address, or transaction hash:"
        )
        
        if ok and search_term:
            try:
                network_filter = self.network_filter.currentText().lower()
                if network_filter == "all":
                    network_filter = None
                
                results = self.deployment_manager.search_deployments(search_term, network_filter)
                
                if results:
                    self.table.setRowCount(len(results))
                    self.status_label.setText(f"Found {len(results)} matching deployments")
                    
                    for row, deployment in enumerate(results):
                        self.populate_table_row(row, deployment)
                else:
                    self.table.setRowCount(0)
                    self.status_label.setText("No matching deployments found")
                    
            except Exception as e:
                QMessageBox.critical(self, "Search Error", f"Search failed: {str(e)}")
    
    def show_context_menu(self, position):
        """Show context menu for table"""
        item = self.table.itemAt(position)
        if not item:
            return
        
        deployment = item.data(Qt.UserRole)
        if not deployment:
            return
        
        menu = QMenu(self)
        
        copy_action = menu.addAction("📋 Copy Contract ID")
        copy_action.triggered.connect(lambda: self.copy_contract_id(deployment.get("contract_id", "")))
        
        if deployment.get("stellar_expert_url"):
            explorer_action = menu.addAction("🔗 Open in Explorer")
            explorer_action.triggered.connect(lambda: self.open_explorer(deployment["stellar_expert_url"]))
        
        details_action = menu.addAction("📄 View Details")
        details_action.triggered.connect(lambda: self.show_deployment_details(deployment))
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑️ Delete Record")
        delete_action.triggered.connect(lambda: self.delete_deployment(deployment.get("deployment_id", "")))
        
        menu.exec_(self.table.mapToGlobal(position))
    
    def open_explorer(self, url: str):
        """Open Stellar Expert URL"""
        try:
            webbrowser.open(url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open browser: {str(e)}")
    
    def copy_contract_id(self, contract_id: str):
        """Copy contract ID to clipboard"""
        if contract_id:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(contract_id)
            QMessageBox.information(self, "Copied", "Contract ID copied to clipboard")
    
    def show_deployment_details(self, deployment: dict):
        """Show detailed deployment information"""
        from .deployment_completion_dialog import DeploymentCompletionDialog
        
        details_dialog = DeploymentCompletionDialog(self, deployment)
        details_dialog.exec_()
    
    def delete_deployment(self, deployment_id: str):
        """Delete deployment record"""
        if not deployment_id:
            return
        
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this deployment record?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.deployment_manager.delete_deployment(deployment_id):
                self.load_deployments()
                QMessageBox.information(self, "Deleted", "Deployment record deleted successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to delete deployment record")
    
    def export_deployments(self):
        """Export deployments to file"""
        from PyQt5.QtWidgets import QFileDialog, QInputDialog
        
        # Ask for export format
        format_items = ["JSON", "CSV"]
        format_item, ok = QInputDialog.getItem(
            self, "Export Format", "Select export format:", format_items, 0, False
        )
        
        if not ok or not format_item:
            return
        
        # Ask for file location
        file_filter = f"{format_item} files (*.{format_item.lower()})"
        file_path, _ = QFileDialog.getSaveFileName(
            self, f"Export Deployments ({format_item})", 
            f"deployments.{format_item.lower()}", 
            file_filter
        )
        
        if file_path:
            try:
                network_filter = self.network_filter.currentText().lower()
                if network_filter == "all":
                    network_filter = None
                
                export_data = self.deployment_manager.export_deployments(
                    network=network_filter, 
                    format=format_item.lower()
                )
                
                with open(file_path, 'w') as f:
                    f.write(export_data)
                
                QMessageBox.information(self, "Export Complete", f"Deployments exported to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export deployments: {str(e)}")
    
    def cleanup_old_deployments(self):
        """Clean up old deployment records"""
        from PyQt5.QtWidgets import QInputDialog
        
        days, ok = QInputDialog.getInt(
            self, "Cleanup Old Deployments", 
            "Delete deployments older than how many days?", 30, 1, 365
        )
        
        if ok:
            deleted_count = self.deployment_manager.cleanup_old_deployments(days)
            
            if deleted_count > 0:
                self.load_deployments()
                QMessageBox.information(
                    self, "Cleanup Complete", 
                    f"Deleted {deleted_count} old deployment records"
                )
            else:
                QMessageBox.information(
                    self, "Cleanup Complete", 
                    "No old deployment records found to delete"
                )
    
    def closeEvent(self, event):
        """Handle dialog close event"""
        # Stop refresh timer
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        
        event.accept()
