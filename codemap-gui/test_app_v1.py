import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("CodeMap GUI v0")
        self.setCentralWidget(QLabel("GUI boot OK"))


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.resize(900, 600)
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
