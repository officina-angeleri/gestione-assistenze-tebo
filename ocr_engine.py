import os
import json
import traceback
from pypdf import PdfReader
from PySide6.QtCore import QSize
from PySide6.QtGui import QImage, QPainter
from PySide6.QtPdf import QPdfDocument
from PySide6.QtWidgets import QApplication
import sys

# Per i fallback OCR (richiedono Tesseract e Poppler installati a sistema)
try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

class OcrEngine:
    def __init__(self, tesseract_cmd=None):
        if tesseract_cmd and OCR_AVAILABLE:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def render_to_png(self, pdf_path, output_png_path, scale_factor=3):
        """ Renderizza il PDF in un file PNG ad alta risoluzione (usando PySide6 QtPdf) """
        
        # Ensure QApplication exists (since QPdfDocument needs it)
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
            
        doc = QPdfDocument()
        status = doc.load(pdf_path)
        
        if doc.status() != QPdfDocument.Status.Ready:
            print(f"[OCR] Impossibile caricare il PDF per render: {pdf_path}")
            return False, 0
            
        page_size = doc.pagePointSize(0)
        original_height = page_size.height()
        
        render_size = QSize(page_size.width() * scale_factor, original_height * scale_factor)
        
        image = doc.render(0, render_size)
        if image.save(output_png_path):
            print(f"[OCR] Renderizzato con successo: {output_png_path}")
            return True, original_height
        else:
            print(f"[OCR] Fallito salvataggio render: {output_png_path}")
            return False, 0

    def extract_vector_coords(self, pdf_path, original_height, scale_factor=3):
        """ Estrae le coordinate matematiche dei testi dal PDF (Fast Path) """
        reader = PdfReader(pdf_path)
        page = reader.pages[0]
        
        positions = {}
        
        def visitor_body(text, cm, tm, font_dict, font_size):
            clean_text = text.strip()
            if not clean_text: return
            
            # Non ci limitiamo solo ai numeri interi o alfanumerici puri. 
            # Molti codici contengono punti, virgole, trattini ecc (es. "OR 7,5x1", "ø 3.4").
            val = clean_text.replace(" ", "")
            
            # Filtro visivo: Se il testo è lungo 1-25 caratteri e contiene almeno una lettera/numero
            if 1 <= len(val) <= 25 and any(c.isalnum() for c in val):
                # Rimuoviamo il ritorno a capo o la spaziatura estrema per tenerla pulita nel JSON
                key = clean_text.replace('\n', ' ')
                if key not in positions:
                    positions[key] = []
                # tm[4] è X, tm[5] è Y (dal basso)
                positions[key].append((tm[4], tm[5]))

        try:
            page.extract_text(visitor_text=visitor_body)
        except Exception as e:
            print(f"[OCR] Errore nell'estrazione vettoriale: {e}")
            return [], {}
            
        final_points = []
        for key, coords in positions.items():
            # Facciamo la media se ci sono più pezzi di testo sovrapposti
            avg_x = sum(c[0] for c in coords) / len(coords)
            avg_y = sum(c[1] for c in coords) / len(coords)
            
            # Trasformazione da coordinata PDF (bottom-left) a coordinata immagine (top-left) scalata
            img_x = round(avg_x * scale_factor)
            img_y = round((original_height - avg_y) * scale_factor)
            
            # Struttura temporanea
            final_points.append((img_x, img_y, key))
            
        # Ordiniamo prima di tutto per posizione Y visiva per assegnare ID logici (top to bottom)
        final_points.sort(key=lambda t: (t[1], t[0]))
        
        final_coords = []
        initial_data_map = {}
        progressive_id = 1
        
        for (x, y, original_code) in final_points:
            final_coords.append([x, y, progressive_id])
            # [Codice, Descrizione Predefinita]
            initial_data_map[str(progressive_id)] = [original_code, f"Componente {original_code}"]
            progressive_id += 1
            
        return final_coords, initial_data_map

    def extract_ocr_image(self, pdf_path):
        """ Fallback visivo completo usando Tesseract. Molto più lento, ma trova testo rasterizzato.
            Al momento implementa solo uno sketch di base da ampliare in futuro se necessario. 
        """
        if not OCR_AVAILABLE:
            print("[OCR] Librerie OCR (pytesseract/pdf2image) non installate. Salto fallback visivo.")
            return [], {}
            
        print("[OCR] Fallback OCR Image in partenza (LENTO)...")
        # DA IMPLEMENTARE SE NECESSARIO
        # pages = convert_from_path(pdf_path, 300)
        # data = pytesseract.image_to_data(pages[0], output_type=pytesseract.Output.DICT)
        return [], {}

    def process_drawing(self, pdf_path, output_dir):
        """ Processa un PDF: genera PNG e tenta di estrarre e salvare le coordinate JSON """
        try:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            png_path = os.path.join(output_dir, f"{base_name}.png")
            coords_path = os.path.join(output_dir, f"{base_name}.coords.json")
            data_path = os.path.join(output_dir, f"{base_name}.data.json")
            
            # 1. Rendering visuale (Necessario per UI)
            success, org_h = self.render_to_png(pdf_path, png_path)
            if not success:
                return False
                
            # 2. Se ho generato le coordinate, ho finito
            if os.path.exists(coords_path) and os.path.exists(data_path):
                print(f"[OCR] File coordinate d data già presenti per {base_name}")
                return True
                
            # 3. Tento Estrazione Vettoriale
            points, data_map = self.extract_vector_coords(pdf_path, org_h)
            
            # 4. Fallback se vettoriale fallisce (<= 2 punti trovati assumiamo sia muto o raster)
            if len(points) <= 2:
                print("[OCR] Estrazione vettoriale ha trovato poco testo. Tento Fallback OCR Image...")
                ocr_points, ocr_data = self.extract_ocr_image(pdf_path)
                if ocr_points: 
                    points = ocr_points
                    data_map = ocr_data
            
            # 5. Salva Mappe
            with open(coords_path, 'w', encoding='utf-8') as f:
                json.dump(points, f, indent=4)
                
            # Salva i Dati Dizionario solo se non esistono già (per non sovrascriverli se l'utente li ha modificati)
            if not os.path.exists(data_path) and data_map:
                with open(data_path, 'w', encoding='utf-8') as f:
                    json.dump(data_map, f, indent=4)
                
            print(f"[OCR] Creata mappa con {len(points)} coordinate per {base_name}")
            return True
            
        except Exception as e:
            print(f"[OCR] Errore irreversibile nel processamento del PDF: {traceback.format_exc()}")
            return False

if __name__ == '__main__':
    # Test esecuzione stand-alone
    engine = OcrEngine()
    test_pdf = os.path.abspath("Disegni/VA50_500 - 1.pdf")
    if os.path.exists(test_pdf):
        engine.process_drawing(test_pdf, "Disegni")
