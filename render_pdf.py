import sys
import os
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage, QPainter
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QApplication

def extract_page(pdf_path, output_path):
    app = QApplication(sys.argv)
    
    doc = QPdfDocument()
    pdf_abs_path = os.path.abspath(pdf_path)
    print(f"Loading: {pdf_abs_path}")
    status = doc.load(pdf_abs_path)
    print(f"Status after load: {status}")
    
    if doc.status() != QPdfDocument.Status.Ready:
        print("Document not ready.")
        return

    page_size = doc.pagePointSize(0)
    # Increase resolution (3x)
    render_size = QSize(page_size.width() * 3, page_size.height() * 3)
    
    image = doc.render(0, render_size)
    if image.save(output_path):
        print(f"Saved {output_path}")
    else:
        print(f"Failed to save {output_path}")

if __name__ == "__main__":
    extract_page("VA50_500 - 1.pdf", "product_map.png")
