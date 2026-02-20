import sys
from PySide6.QtPdf import QPdfDocument, QPdfSearchModel
from PySide6.QtCore import QCoreApplication, QEventLoop, Qt

def test_search():
    # We need a QGuiApplication for QPdfDocument
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    doc = QPdfDocument()
    if doc.load("disegni/Valvola VA50.pdf") != QPdfDocument.Status.Ready:
        print("Failed to load PDF")
        return

    search = QPdfSearchModel()
    search.setDocument(doc)
    
    found = []
    for i in range(1, 40):
        search.setSearchString(str(i))
        # Search is synchronous in basic mode for first page? 
        # No, it's usually async. Let's wait.
        loop = QEventLoop()
        def on_count(): 
            if search.rowCount() > 0: loop.quit()
        search.countChanged.connect(on_count)
        
        # Timeout to avoid hang
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, loop.quit)
        loop.exec()
        
        if search.rowCount() > 0:
            found.append(str(i))
            
    print(f"Found numbers: {', '.join(found)}")
    sys.exit(0)

if __name__ == "__main__":
    test_search()
