import os
import json

class ProductRegistry:
    def __init__(self, drawings_dir='disegni'):
        self.drawings_dir = drawings_dir
        self.products = {}
        self.scan_products()

    def scan_products(self):
        """Scans the drawings directory for PDF files and their metadata."""
        if not os.path.exists(self.drawings_dir):
            os.makedirs(self.drawings_dir)
            
        for filename in os.listdir(self.drawings_dir):
            if filename.endswith('.pdf'):
                product_id = os.path.splitext(filename)[0]
                # Default entry
                self.products[product_id] = {
                    'name': product_id,
                    'drawing_path': os.path.join(self.drawings_dir, filename),
                    'coords_path': os.path.join(self.drawings_dir, f"{product_id}.coords.json"),
                    'data_path': os.path.join(self.drawings_dir, f"{product_id}.data.json")
                }

    def get_available_products(self):
        return list(self.products.keys())

    def get_product_info(self, product_id):
        return self.products.get(product_id)

    def get_product_coords(self, product_id):
        info = self.get_product_info(product_id)
        if not info: return []
        
        path = info['coords_path']
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return []

    def save_product_coords(self, product_id, coords):
        info = self.get_product_info(product_id)
        if not info: return False
        
        path = info['coords_path']
        with open(path, 'w') as f:
            json.dump(coords, f, indent=4)
        print(f"Saved {len(coords)} points to {path}")
        return True

    def get_product_data(self, product_id):
        """Returns component dictionary {pos: (code, desc)}"""
        info = self.get_product_info(product_id)
        if not info: return {}
        
        path = info['data_path']
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                return {str(k): v for k, v in raw_data.items()}
        else:
            # Fallback auto-generation from coords if data doesn't exist
            coords = self.get_product_coords(product_id)
            if coords:
                return {str(c[2]): ["-", f"Componente {c[2]}"] for c in coords}
                
        return {}

    def save_product_data(self, product_id, data_dict):
        """Saves the data dictionary to the product's data.json"""
        if product_id not in self.products:
            self.products[product_id] = {
                'name': product_id,
                'drawing_path': os.path.join(self.drawings_dir, f"{product_id}.pdf"),
                'coords_path': os.path.join(self.drawings_dir, f"{product_id}.coords.json"),
                'data_path': os.path.join(self.drawings_dir, f"{product_id}.data.json")
            }
        
        path = self.products[product_id]['data_path']
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data_dict, f, indent=4)
            return True
        except Exception as e:
            print(f"Errore salvataggio data: {e}")
            return False
