import sys
import os
from PySide6.QtWidgets import QApplication
from gui import MainWindow
from watcher import DrawingsWatcher

def main():
    # Set the working directory to the script's directory to find assets
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    app = QApplication(sys.argv)
    
    # Inizializza il watcher silente in background
    watcher = DrawingsWatcher(parent=app)
    
    # Light Theme - High Contrast for legibility
    app.setStyleSheet("""
        QMainWindow { background-color: #f5f5f5; }
        QWidget { color: #333333; font-size: 13px; }
        QPushButton { 
            background-color: #ffffff; 
            border: 1px solid #cccccc; 
            padding: 8px; 
            border-radius: 4px;
        }
        QPushButton:hover { background-color: #f0f0f0; border-color: #00bcd4; }
        QTableWidget { 
            background-color: #ffffff; 
            border: 1px solid #cccccc; 
            gridline-color: #eeeeee;
        }
        QHeaderView::section {
            background-color: #e0e0e0;
            color: #007c91;
            padding: 5px;
            border: 1px solid #cccccc;
            font-weight: bold;
        }
        QGraphicsView { background-color: #ffffff; border: 1px solid #cccccc; }
        QLineEdit, QTextEdit, QDoubleSpinBox {
            background-color: #ffffff;
            border: 1px solid #cccccc;
            padding: 5px;
            color: #333333;
        }
        QGroupBox {
            border: 1px solid #cccccc;
            margin-top: 10px;
            font-weight: bold;
        }
    """)
    
    window = MainWindow()
    
    # Colleghiamo il segnale del watcher alla finestra per aggiornare la UI
    watcher.new_product_ready.connect(window.on_new_product_ready)
    
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
