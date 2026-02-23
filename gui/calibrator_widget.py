import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QSplitter, QMessageBox)
from PySide6.QtCore import Qt, Signal
from .map_viewer import ProductMapView
from registry import ProductRegistry

class DrawingCalibratorWidget(QWidget):
    # Signals per l'interazione esterna
    # Emesso in INTERVENTION_MODE o in generale quando si seleziona un componente
    component_selected = Signal(str, str, str) # id, codice, descrizione

    def __init__(self, product_id, mode="MASTER", parent=None):
        super().__init__(parent)
        self.registry = ProductRegistry()
        self.product_id = product_id
        self.mode = mode # "MASTER" o "INTERVENTION"
        
        self.product_info = self.registry.get_product_info(product_id)
        self.product_data = self.registry.get_product_data(product_id)
        
        self.setup_ui()
        self.setup_map_points()
        self.populate_calib_list()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #ddd;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        mode_text = "<b>MASTER ESPLOSO</b>" if self.mode == "MASTER" else "<b>SELEZIONE INTERVENTO</b>"
        toolbar_layout.addWidget(QLabel(mode_text))
        toolbar_layout.addStretch()
        
        self.btn_mode_toggle = QPushButton("ABILITA CALIBRAZIONE")
        self.btn_mode_toggle.setCheckable(True)
        self.btn_mode_toggle.setFixedWidth(180)
        self.btn_mode_toggle.setStyleSheet("""
            QPushButton { background-color: #eee; border: 1px solid #ccc; padding: 5px; font-weight: bold; }
            QPushButton:checked { background-color: #ff9800; color: white; border-color: #e68a00; }
        """)
        self.btn_mode_toggle.toggled.connect(self.toggle_calibration_mode)
        toolbar_layout.addWidget(self.btn_mode_toggle)
        
        self.btn_save_coords = QPushButton("SALVA CALIB.")
        self.btn_save_coords.setFixedWidth(120)
        self.btn_save_coords.setStyleSheet("background-color: #4caf50; color: white; font-weight: bold; padding: 5px;")
        self.btn_save_coords.clicked.connect(self.save_calibration)
        self.btn_save_coords.setVisible(False)
        toolbar_layout.addWidget(self.btn_save_coords)
        
        btn_reset = QPushButton("Adatta Vista")
        btn_reset.setFixedWidth(100)
        btn_reset.clicked.connect(lambda: self.map_view.reset_view())
        toolbar_layout.addWidget(btn_reset)
        
        main_layout.addWidget(toolbar)
        
        # Splitter (Mappa | Lista)
        self.map_splitter = QSplitter(Qt.Horizontal)
        self.map_splitter.setStyleSheet("QSplitter::handle { background-color: #ddd; width: 4px; }")
        
        # Map View
        self.map_view = ProductMapView()
        png_path = self.product_info['drawing_path'].replace('.pdf', '.png')
        if os.path.exists(png_path):
            self.map_view.load_image(png_path)
        else:
            self.map_view.load_image(self.product_info['drawing_path'])
            
        self.map_view.componentSelected.connect(self.on_component_clicked)
        self.map_view.pointAddedManually.connect(self.on_point_added_manually)
        self.map_view.pointDeletedManually.connect(self.on_point_deleted_manually)
        self.map_splitter.addWidget(self.map_view)
        
        # List
        self.calib_list = QTableWidget()
        self.calib_list.setColumnCount(3)
        self.calib_list.setHorizontalHeaderLabels(["ID", "Codice", "Descrizione"])
        self.calib_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.calib_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.calib_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.calib_list.setVisible(False)
        self.calib_list.itemChanged.connect(self.on_calib_data_changed)
        self.map_splitter.addWidget(self.calib_list)
        
        self.map_splitter.setStretchFactor(0, 4)
        self.map_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.map_splitter, 1)

    def toggle_calibration_mode(self, checked):
        self.map_view.set_calibration_mode(checked)
        self.btn_save_coords.setVisible(checked)
        self.calib_list.setVisible(checked)
        self.btn_mode_toggle.setText("MODO OPERAZIONE" if checked else "MODO CALIBRAZIONE")

    def populate_calib_list(self):
        self.calib_list.blockSignals(True)
        self.calib_list.setRowCount(len(self.product_data))
        for i, pos in enumerate(sorted(self.product_data.keys(), key=lambda x: (0, int(x)) if str(x).isdigit() else (1, str(x)))):
            pos_str = str(pos)
            code, desc = self.product_data[pos_str]
            
            item_id = QTableWidgetItem(pos_str)
            item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)
            self.calib_list.setItem(i, 0, item_id)
            self.calib_list.setItem(i, 1, QTableWidgetItem(code))
            self.calib_list.setItem(i, 2, QTableWidgetItem(desc))
            
        self.calib_list.blockSignals(False)

    def on_calib_data_changed(self, item):
        row = item.row()
        pos_id = self.calib_list.item(row, 0).text()
        new_code = self.calib_list.item(row, 1).text() if self.calib_list.item(row, 1) else ""
        new_desc = self.calib_list.item(row, 2).text() if self.calib_list.item(row, 2) else ""
        
        if pos_id in self.product_data:
            self.product_data[pos_id] = [new_code, new_desc]
            # Salva sempre nel master json
            self.registry.save_product_data(self.product_id, self.product_data)
            
            # Opzionale: emettere un segnale che i dati sono cambiati se qualcuno fosse in ascolto
            
    def setup_map_points(self):
        coords = self.registry.get_product_coords(self.product_id)
        for x, y, num in coords:
            pos_str = str(num)
            code, desc = self.product_data.get(pos_str, ("-", "???"))
            full_desc = f"[{code}] {desc}"
            self.map_view.add_point(x, y, pos_str, full_desc)

    def save_calibration(self):
        coords = self.map_view.get_all_points()
        if self.registry.save_product_coords(self.product_id, coords):
            QMessageBox.information(self, "OK", "Posizioni salvate.")
            self.btn_mode_toggle.setChecked(False)

    def on_point_added_manually(self, code):
        self.product_data[code] = ["", ""]
        self.registry.save_product_data(self.product_id, self.product_data)
        coords = self.map_view.get_all_points()
        self.registry.save_product_coords(self.product_id, coords)
        self.populate_calib_list()
        
        for r in range(self.calib_list.rowCount()):
            if self.calib_list.item(r, 0).text() == code:
                self.calib_list.selectRow(r)
                self.calib_list.scrollToItem(self.calib_list.item(r, 0))
                self.calib_list.editItem(self.calib_list.item(r, 1))
                break

    def on_point_deleted_manually(self, pos_id):
        if pos_id in self.product_data:
            del self.product_data[pos_id]
            self.registry.save_product_data(self.product_id, self.product_data)
            
        coords = self.map_view.get_all_points()
        self.registry.save_product_coords(self.product_id, coords)
        self.populate_calib_list()

    def on_component_clicked(self, pos_num):
        pos_str = str(pos_num)
        code, desc = self.product_data.get(pos_str, ("-", "Componente Muto"))
        # Emit signal con le tre info vitali per la distinta d'intervento
        self.component_selected.emit(pos_str, code, desc)
