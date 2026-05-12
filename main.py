import sys
import pyotp
import time
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout, 
                              QHBoxLayout, QWidget, QScrollArea, QPushButton,
                              QDialog, QLineEdit, QFormLayout, QMessageBox)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFontDatabase, QFont

ACCOUNTS_FILE = "accounts.json"

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)

class AddAccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Account")
        self.setMinimumWidth(300)

        layout = QFormLayout(self)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        self.name_input = QLineEdit()
        self.secret_input = QLineEdit()

        layout.addRow("Account Name:", self.name_input)
        layout.addRow("Secret:", self.secret_input)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addRow(buttons)

    def get_values(self):
        return self.name_input.text().strip(), self.secret_input.text().strip()

class AccountCard(QWidget):
    def __init__(self, account, digital_font, on_delete):
        super().__init__()
        self.account = account
        self.totp = pyotp.TOTP(account["secret"])
        self.on_delete = on_delete

        self.setStyleSheet("background-color: #1e1e1e; border-radius: 8px; padding: 8px;")

        layout = QVBoxLayout(self)

        self.name_label = QLabel(account["name"])
        self.name_label.setStyleSheet("background-color: #121212; color: white;")
        self.code_label = QLabel()
        self.code_label.setFont(digital_font)
        self.code_label.setStyleSheet("font-size: 48px; color: #00ff99; letter-spacing: 8px;")

        self.timer_label = QLabel()
        self.timer_label.setStyleSheet("font-size: 12px; color: #666666;")

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet("color: red; border: none; font-size: 12px;")
        delete_btn.clicked.connect(self.delete)

        top_row = QHBoxLayout()
        top_row.addWidget(self.name_label)
        top_row.addStretch()
        top_row.addWidget(delete_btn)

        fullscreen_btn = QPushButton("⛶")
        fullscreen_btn.setStyleSheet("color: white; border: none; font-size: 16px;")
        fullscreen_btn.clicked.connect(self.open_fullscreen)
        top_row.addWidget(fullscreen_btn)

        layout.addLayout(top_row)
        layout.addWidget(self.code_label)
        layout.addWidget(self.timer_label)

        self.update_code()

    def update_code(self):
        self.code_label.setText(self.totp.now())
        remaining = 30 - (int(time.time()) % 30)
        self.timer_label.setText(f"Refreshes in {remaining}s")

    def delete(self):
        confirm = QMessageBox.question(self, "Delete", f"Delete {self.account['name']}?")
        if confirm == QMessageBox.StandardButton.Yes:
            self.on_delete(self.account)
    def open_fullscreen(self):
        self.fullscreen = FullscreenCard(self.account, self.code_label.font())
        self.fullscreen.show()


class FullscreenCard(QWidget):
    def __init__(self, account, digital_font):
        super().__init__()
        self.totp = pyotp.TOTP(account["secret"])
        self.setWindowTitle(account["name"])
        self.showFullScreen()
        self.setStyleSheet("background-color: #121212;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(account["name"])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("font-size: 24px; color: #aaaaaa;")

        self.code_label = QLabel()
        self.code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_label.setFont(digital_font)
        self.code_label.setStyleSheet("color: #00ff99; letter-spacing: 8px;")

        self.timer_label = QLabel()
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 18px; color: #666666;")

        close_btn = QPushButton("Exit Fullscreen")
        close_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #333; color: white; border-radius: 6px;")
        close_btn.clicked.connect(self.close)

        layout.addWidget(name_label)
        layout.addWidget(self.code_label)
        layout.addWidget(self.timer_label)
        layout.addWidget(close_btn)

        self.update_code()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_code)
        self.timer.start(1000)

    def update_code(self):
        self.code_label.setText(self.totp.now())
        remaining = 30 - (int(time.time()) % 30)
        self.timer_label.setText(f"Refreshes in {remaining}s")

class AuthApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Authenticator")
        self.setMinimumSize(400, 500)
        self.setStyleSheet("background-color: #121212;")

        font_id = QFontDatabase.addApplicationFont("digital-7.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.digital_font = QFont(font_family, 48)

        self.accounts = load_accounts()
        self.cards = []

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        add_btn = QPushButton("+ Add Account")
        add_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #333; color: white; border-radius: 6px;")
        add_btn.clicked.connect(self.add_account)
        main_layout.addWidget(add_btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self.cards_widget)
        main_layout.addWidget(scroll)

        self.load_cards()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_cards)
        self.timer.start(1000)

    def load_cards(self):
        for card in self.cards:
            self.cards_layout.removeWidget(card)
            card.deleteLater()
        self.cards = []
        for account in self.accounts:
            card = AccountCard(account, self.digital_font, self.delete_account)
            self.cards.append(card)
            self.cards_layout.addWidget(card)

    def update_cards(self):
        for card in self.cards:
            card.update_code()

    def add_account(self):
        dialog = AddAccountDialog(self)
        if dialog.exec():
            name, secret = dialog.get_values()
            if name and secret:
                try:
                    pyotp.TOTP(secret).now()
                    self.accounts.append({"name": name, "secret": secret})
                    save_accounts(self.accounts)
                    self.load_cards()
                except Exception:
                    QMessageBox.warning(self, "Error", "Invalid secret key.")

    def delete_account(self, account):
        self.accounts = [a for a in self.accounts if a != account]
        save_accounts(self.accounts)
        self.load_cards()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuthApp()
    window.show()
    sys.exit(app.exec())