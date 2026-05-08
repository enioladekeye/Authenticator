import sys
import pyotp
import time
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer, Qt

SECRET = "JBSWY3DPEHPK3PXP"  # Example secret key, replace with your own

class AuthApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Authenticator")
        self.setMinimumSize(300, 150)
        
        self.totp = pyotp.TOTP(SECRET)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        self.code_label = QLabel()
        self.code_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_label.setStyleSheet("font-size: 48px; font-weight: bold; letter-spacing: 8px;")
        
        self.timer_label = QLabel()
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 16px; color: gray;")
        
        layout.addWidget(self.code_label)
        layout.addWidget(self.timer_label)
        
        self.update_code()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_code)
        self.timer.start(1000)
    
    def update_code(self):
        self.code_label.setText(self.totp.now())
        remaining = 30 - (int(time.time()) % 30)
        self.timer_label.setText(f"Refreshes in {remaining}s")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AuthApp()
    window.show()
    sys.exit(app.exec())