import sys
from PySide6.QtPdf import QPdfDocument, QPdfSearchModel
from PySide6.QtCore import QCoreApplication, QEventLoop, Qt

def test_search():
    app = QCoreApplication(sys.argv)
    doc = QPdfDocument()
    if doc.load("VA50_500 - 1.pdf") != QPdfDocument.Status.Ready:
        print("Failed to load PDF")
        return

    search = QPdfSearchModel()
    search.setDocument(doc)
    
    # Search for "1"
    search.setSearchString("1")
    
    # Wait for search to finish (it's async)
    loop = QEventLoop()
    search.countChanged.connect(lambda: loop.quit())
    # If already found, countChanged might not trigger?
    if search.rowCount() > 0:
        pass
    else:
        loop.exec()
    
    print(f"Found {search.rowCount()} matches for '1'")
    for i in range(search.rowCount()):
        index = search.index(i, 0)
        # In newer PySide6, we can get page and rect
        # search.resultAtIndex(i)
        pass

if __name__ == "__main__":
    test_search()
