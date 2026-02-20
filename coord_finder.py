from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QScrollArea
from PySide6.QtGui import QPixmap, QMouseEvent
from PySide6.QtCore import Qt
import sys

class CoordFinder(QMainWindow):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Coordinate Finder")
        self.label = QLabel()
        pixmap = QPixmap(image_path)
        self.label.setPixmap(pixmap)
        self.label.mousePressEvent = self.on_click
        
        scroll = QScrollArea()
        scroll.setWidget(self.label)
        self.setCentralWidget(scroll)
        self.resize(1000, 800)

    def on_click(self, event: QMouseEvent):
        x = event.position().x()
        y = event.position().y()
        print(f"[{round(x)}, {round(y)}, ???],")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CoordFinder("disegni/Valvola VA50.png")
    window.show()
    sys.exit(app.exec())
