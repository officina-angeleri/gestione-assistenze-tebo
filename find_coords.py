from pypdf import PdfReader
import os

def find_text_coordinates(pdf_path):
    reader = PdfReader(pdf_path)
    page = reader.pages[0]
    
    positions = {}
    
    def visitor_body(text, cm, tm, font_dict, font_size):
        clean_text = text.strip()
        if not clean_text: return
        
        # If it's a number 1-39
        if clean_text.isdigit():
            num = int(clean_text)
            if 1 <= num <= 39:
                if num not in positions:
                    positions[num] = []
                positions[num].append((tm[4], tm[5]))
        elif clean_text.startswith(" ") or clean_text.endswith(" "):
            # Some PDFs split numbers with spaces
            val = clean_text.strip()
            if val.isdigit():
                num = int(val)
                if 1 <= num <= 39:
                    if num not in positions:
                        positions[num] = []
                    positions[num].append((tm[4], tm[5]))

    page.extract_text(visitor_text=visitor_body)
    
    bbox = page.mediabox
    height = bbox.upper_right[1]
    
    # Scale factor 3 (matching render_pdf.py)
    final_points = {}
    for num, coords in positions.items():
        # Use the first coordinate or average
        avg_x = sum(c[0] for c in coords) / len(coords)
        avg_y = sum(c[1] for c in coords) / len(coords)
        
        # Flip Y and Scale
        img_x = round(avg_x * 3)
        img_y = round((height - avg_y) * 3)
        
        final_points[num] = (img_x, img_y)
        
    return final_points

if __name__ == "__main__":
    pdf_file = "VA50_500 - 1.pdf"
    if os.path.exists(pdf_file):
        pts = find_text_coordinates(pdf_file)
        print("MAPPING = {")
        for n in sorted(pts.keys()):
            print(f"    {n}: {pts[n]},")
        print("}")
