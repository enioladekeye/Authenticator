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


ACCOUNTS_FILE = "accounts.json" # hopefully this isnt too inconspicuously named

# def is how you define a function in python, thats fun but i dont like it
# idk man i miss c#- oh what i never thought i would say that ew

# anyway i hope the function names are descriptive enough for whatever poor soul will need to read this in the future
def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)

#should i have broken this into multiple files? probably. but will i? heheheheno. 
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
    def __init__(self, account, digital_font, on_delete, on_favourite):
        super().__init__()
        self.account = account
        self.totp = pyotp.TOTP(account["secret"])
        self.on_delete = on_delete
        self.on_favourite = on_favourite

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

        # star is filled if favourited, empty if not
        self.favourite_btn = QPushButton("★" if account.get("favourite") else "⚝")
        self.favourite_btn.setStyleSheet(
            "color: gold; border: none; font-size: 16px;" if account.get("favourite")
            else "color: white; border: none; font-size: 16px;"
        )
        self.favourite_btn.clicked.connect(self.toggle_favourite)

        top_row = QHBoxLayout()
        top_row.addWidget(self.name_label)
        top_row.addStretch()
        top_row.addWidget(self.favourite_btn)
        top_row.addWidget(delete_btn)

        layout.addLayout(top_row)
        layout.addWidget(self.code_label)
        layout.addWidget(self.timer_label)

        self.update_code()

    def toggle_favourite(self):
        self.on_favourite(self.account)

    def update_favourite_btn(self):
        # update the star button to reflect current favourite state
        if self.account.get("favourite"):
            self.favourite_btn.setText("★")
            self.favourite_btn.setStyleSheet("color: gold; border: none; font-size: 16px;")
        else:
            self.favourite_btn.setText("⚝")
            self.favourite_btn.setStyleSheet("color: white; border: none; font-size: 16px;")

    def update_code(self):
        self.code_label.setText(self.totp.now())
        remaining = 30 - (int(time.time()) % 30)
        self.timer_label.setText(f"Refreshes in {remaining}s")

    def delete(self):
        confirm = QMessageBox(self)
        confirm.setStyleSheet("background-color: #1e1e1e; color: white;")
        confirm.setWindowTitle("Delete")
        confirm.setText(f"Delete {self.account['name']}?")
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        result = confirm.exec()
        if result == QMessageBox.StandardButton.Yes:
            self.on_delete(self.account)


class FullscreenCycle(QWidget):
    def __init__(self, favourites, digital_font):
        super().__init__()
        self.favourites = favourites
        self.digital_font = digital_font
        self.current_index = 0

        self.setWindowTitle("Favourites")
        self.showFullScreen()
        self.setStyleSheet("background-color: #121212;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.name_label = QLabel()
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size: 24px; color: #aaaaaa;")

        self.code_label = QLabel()
        self.code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_label.setFont(digital_font)
        self.code_label.setStyleSheet("color: #00ff99; letter-spacing: 8px;")

        self.timer_label = QLabel()
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 18px; color: #666666;")

        # shows how long until we switch to the next favourite
        self.cycle_label = QLabel()
        self.cycle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cycle_label.setStyleSheet("font-size: 14px; color: #444444;")

        close_btn = QPushButton("Exit Fullscreen")
        close_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #333; color: white; border-radius: 6px;")
        close_btn.clicked.connect(self.close)

        layout.addWidget(self.name_label)
        layout.addWidget(self.code_label)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.cycle_label)
        layout.addWidget(close_btn)

        # seconds until next cycle switch
        self.seconds_until_switch = 6

        self.load_current()

        # ticks every second for code update and cycle countdown
        self.tick_timer = QTimer()
        self.tick_timer.timeout.connect(self.tick)
        self.tick_timer.start(1000)

    def load_current(self):
        account = self.favourites[self.current_index]
        self.totp = pyotp.TOTP(account["secret"])
        self.name_label.setText(account["name"])
        self.update_code()

    def tick(self):
        self.seconds_until_switch -= 1
        self.cycle_label.setText(f"Next in {self.seconds_until_switch}s  •  {self.current_index + 1}/{len(self.favourites)}")
        self.update_code()

        if self.seconds_until_switch <= 0:
            # move to next favourite, loop back to start
            self.current_index = (self.current_index + 1) % len(self.favourites)
            self.seconds_until_switch = 6
            self.load_current()

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

        import pathlib
        font_path = str(pathlib.Path(__file__).parent / "digital-7.ttf")
        font_id = QFontDatabase.addApplicationFont(font_path)
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        self.digital_font = QFont(font_family, 48)

        self.accounts = load_accounts()
        self.cards = []

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        top_row = QHBoxLayout()

        add_btn = QPushButton("+ Add Account")
        add_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #333; color: white; border-radius: 6px;")
        add_btn.clicked.connect(self.add_account)
        top_row.addWidget(add_btn)

        fullscreen_btn = QPushButton("⛶ Favourites")
        fullscreen_btn.setStyleSheet("font-size: 14px; padding: 8px; background-color: #333; color: white; border-radius: 6px;")
        fullscreen_btn.clicked.connect(self.open_fullscreen)
        top_row.addWidget(fullscreen_btn)

        main_layout.addLayout(top_row)

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
            card = AccountCard(account, self.digital_font, self.delete_account, self.toggle_favourite)
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

    def toggle_favourite(self, account):
        favourites = [a for a in self.accounts if a.get("favourite")]
        
        if account.get("favourite"):
            # unfavourite it
            account["favourite"] = False
        else:
            # max 3 favourites
            if len(favourites) >= 3:
                QMessageBox.warning(self, "Max Favourites", "You can only favourite up to 3 accounts.")
                return
            account["favourite"] = True

        save_accounts(self.accounts)
        self.load_cards()

    def open_fullscreen(self):
        favourites = [a for a in self.accounts if a.get("favourite")]
        if not favourites:
            QMessageBox.warning(self, "No Favourites", "Star up to 3 accounts first.")
            return
        self.fullscreen = FullscreenCycle(favourites, self.digital_font)
        self.fullscreen.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuthApp()
    window.show()
    if "--favourites" in sys.argv:
        QTimer.singleShot(500, window.open_fullscreen)
    sys.exit(app.exec())