from pypdf import PdfReader
import json

def dump_coords(pdf_path):
    reader = PdfReader(pdf_path)
    page = reader.pages[0]
    
    text_data = []
    
    def visitor_body(text, cm, tm, font_dict, font_size):
        clean = text.strip()
        if clean:
            text_data.append({
                "text": clean,
                "x": tm[4],
                "y": tm[5],
                "size": font_size
            })

    page.extract_text(visitor_text=visitor_body)
    
    with open("dumped_coords.json", "w") as f:
        json.dump(text_data, f, indent=2)
        
    print(f"Dumped {len(text_data)} text items to dumped_coords.json")

if __name__ == "__main__":
    dump_coords("disegni/Valvola VA50.pdf")
