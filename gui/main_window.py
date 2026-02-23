import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QDialog, QFormLayout, 
                             QLineEdit, QDoubleSpinBox, QTextEdit, QComboBox, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, QDate, QTimer
from .map_viewer import ProductMapView
from database import DatabaseManager
from registry import ProductRegistry

class NewInterventionDialog(QDialog):
    def __init__(self, parent=None, product_id="VA50", existing_id=None):
        super().__init__(parent)
        self.registry = ProductRegistry()
        self.db = DatabaseManager()
        self.product_id = product_id
        self.existing_id = existing_id
        
        # Make dialog resizable and maximizable
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        self.product_info = self.registry.get_product_info(product_id)
        self.product_data = self.registry.get_product_data(product_id)
        
        self.setWindowTitle("TEBO - Rapporto Tecnico" if existing_id else f"TEBO - Nuovo Rapporto {product_id}")
        self.resize(1600, 950)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        
        # MAIN SPLITTER
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setStyleSheet("QSplitter::handle { background-color: #eee; width: 6px; }")
        
        # LEFT PANEL: Title + Form + Table
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        title_text = "MODIFICA RAPPORTO" if existing_id else f"NUOVO RAPPORTO: {product_id}"
        title = QLabel(title_text)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #007c91; margin-bottom: 10px;")
        left_layout.addWidget(title)
        
        info_group = QGroupBox("Dati Generali")
        form_layout = QFormLayout(info_group)
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Oggetto dell'intervento...")
        form_layout.addRow("Oggetto:", self.txt_desc)
        
        self.spin_hours = QDoubleSpinBox()
        self.spin_hours.setRange(0, 100)
        self.spin_hours.setSuffix(" h")
        self.spin_hours.setSingleStep(0.5)
        self.spin_hours.setDecimals(2)
        
        time_layout = QHBoxLayout()
        btn_time_minus = QPushButton("-")
        btn_time_minus.setFixedSize(30, 30)
        btn_time_minus.clicked.connect(lambda: self.spin_hours.setValue(max(0, self.spin_hours.value() - 0.5)))
        
        btn_time_plus = QPushButton("+")
        btn_time_plus.setFixedSize(30, 30)
        btn_time_plus.clicked.connect(lambda: self.spin_hours.setValue(self.spin_hours.value() + 0.5))
        
        time_layout.addWidget(btn_time_minus)
        time_layout.addWidget(self.spin_hours)
        time_layout.addWidget(btn_time_plus)
        
        form_layout.addRow("Tempo:", time_layout)
        
        self.txt_notes = QTextEdit()
        self.txt_notes.setPlaceholderText("Dettagli tecnici...")
        self.txt_notes.setMaximumHeight(80)
        form_layout.addRow("Note:", self.txt_notes)
        left_layout.addWidget(info_group)
        
        table_group = QGroupBox("Pezzi Sostituiti")
        table_layout = QVBoxLayout(table_group)
        self.comp_table = QTableWidget()
        self.comp_table.setColumnCount(5)
        self.comp_table.setHorizontalHeaderLabels(["POS", "CODICE", "DESCRIZIONE", "QTY", "AZIONE"])
        self.comp_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.comp_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.comp_table)
        left_layout.addWidget(table_group)
        
        self.btn_save = QPushButton("SALVA E CHIUDI")
        self.btn_save.clicked.connect(self.accept)
        self.btn_save.setMinimumHeight(60)
        self.btn_save.setStyleSheet("background-color: #007c91; color: white; font-weight: bold; font-size: 18px; border-radius: 4px;")
        left_layout.addWidget(self.btn_save)
        
        self.main_splitter.addWidget(left_panel)
        
        # RIGHT PANEL: Toolbar + Map Area (with Nested Splitter for Calib List)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Modern Compact Toolbar
        toolbar = QWidget()
        toolbar.setStyleSheet("background-color: #f8f9fa; border-bottom: 1px solid #ddd;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        toolbar_layout.addWidget(QLabel("<b>ESPLOSO TECNICO</b>"))
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
        
        right_layout.addWidget(toolbar)
        
        # NESTED SPLITTER for Map and Calibration List
        self.map_splitter = QSplitter(Qt.Horizontal)
        self.map_splitter.setStyleSheet("QSplitter::handle { background-color: #ddd; width: 4px; }")
        
        self.map_view = ProductMapView()
        png_path = self.product_info['drawing_path'].replace('.pdf', '.png')
        if os.path.exists(png_path): self.map_view.load_image(png_path)
        else: self.map_view.load_image(self.product_info['drawing_path'])
        
        self.map_view.componentSelected.connect(self.add_component_row)
        self.map_view.pointAddedManually.connect(self.on_point_added_manually)
        self.map_view.pointDeletedManually.connect(self.on_point_deleted_manually)
        self.map_splitter.addWidget(self.map_view)
        
        self.calib_list = QTableWidget()
        self.calib_list.setColumnCount(3)
        self.calib_list.setHorizontalHeaderLabels(["ID", "Codice", "Descrizione"])
        # Evita che l'utente editi l'ID
        self.calib_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.calib_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.calib_list.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.calib_list.setVisible(False)
        self.calib_list.itemChanged.connect(self.on_calib_data_changed)
        self.map_splitter.addWidget(self.calib_list)
        
        # Set map as much larger by default
        self.map_splitter.setStretchFactor(0, 4)
        self.map_splitter.setStretchFactor(1, 1)
        
        # IMPORTANT: Add splitter with stretch factor high (1) to fill the parent layout
        right_layout.addWidget(self.map_splitter, 1)
        self.main_splitter.addWidget(right_panel)
        
        # Proportions: 30% left, 70% right
        self.main_splitter.setStretchFactor(0, 2)
        self.main_splitter.setStretchFactor(1, 5)
        
        main_layout.addWidget(self.main_splitter)
        
        # UI Tweak for visibility
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 15px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
                background-color: transparent;
            }
        """)
        
        self.setup_map_points()
        self.populate_calib_list()
        
        if existing_id:
            self.load_existing_data(existing_id)

    def load_existing_data(self, existing_id):
        interventi = self.db.get_interventi(self.product_id)
        report = next((r for r in interventi if r.id == existing_id), None)
        if report:
            self.txt_desc.setText(report.descrizione or "")
            self.spin_hours.setValue(report.ore_lavoro)
            self.txt_notes.setPlainText(report.note_tecniche or "")
            for c in report.componenti:
                self.add_component_row(c.numero_componente, c.quantita)

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
            
            # ID
            item_id = QTableWidgetItem(pos_str)
            item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable) # Readonly
            self.calib_list.setItem(i, 0, item_id)
            
            # Codice e Descrizione (Editabili)
            self.calib_list.setItem(i, 1, QTableWidgetItem(code))
            self.calib_list.setItem(i, 2, QTableWidgetItem(desc))
            
        self.calib_list.blockSignals(False)

    def on_calib_data_changed(self, item):
        row = item.row()
        pos_id = self.calib_list.item(row, 0).text()
        
        # Recupera i nuovi dati inseriti
        new_code = self.calib_list.item(row, 1).text() if self.calib_list.item(row, 1) else ""
        new_desc = self.calib_list.item(row, 2).text() if self.calib_list.item(row, 2) else ""
        
        # Aggiorna il dizionario
        if pos_id in self.product_data:
            self.product_data[pos_id] = [new_code, new_desc]
            # Salva attivamente nei file JSON
            self.registry.save_product_data(self.product_id, self.product_data)
            
            # Se siamo fortunati, aggiornamemto anche sul tooltip visuale
            coords = self.map_view.get_all_points()
            for x, y, map_id in coords:
                if str(map_id) == pos_id:
                    # In teoria potremmo aggiornare iterando la scena,
                    # ma per evitare rallentamenti ricarichiamo i map_points solo se servisse.
                    pass

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
        """ Aggiunge dinamicamente il pezzo alla product_data e ricarica la lista di destra """
        self.product_data[code] = ["", ""]
        self.registry.save_product_data(self.product_id, self.product_data)
        coords = self.map_view.get_all_points()
        self.registry.save_product_coords(self.product_id, coords)
        self.populate_calib_list()
        
        # Scorre la lista per selezionare e focalizzare la nuova riga
        for r in range(self.calib_list.rowCount()):
            if self.calib_list.item(r, 0).text() == code:
                self.calib_list.selectRow(r)
                self.calib_list.scrollToItem(self.calib_list.item(r, 0))
                # Entra in modalità editing sulla cella del codice
                self.calib_list.editItem(self.calib_list.item(r, 1))
                break

    def on_point_deleted_manually(self, pos_id):
        """ Rimuove dinamicamente il pezzo eliminato dalla mappa e dal data json """
        if pos_id in self.product_data:
            del self.product_data[pos_id]
            self.registry.save_product_data(self.product_id, self.product_data)
            
        # Salviamo la lista coordinate aggiornata senza il punto
        coords = self.map_view.get_all_points()
        self.registry.save_product_coords(self.product_id, coords)
        
        # Aggiorna UI
        self.populate_calib_list()

    def add_component_row(self, pos_num, qty=1.0):
        pos_str = str(pos_num)
        # Update existing if found
        for row in range(self.comp_table.rowCount()):
            if self.comp_table.item(row, 0).text() == pos_str:
                qty_label = self.comp_table.cellWidget(row, 3).findChild(QLabel)
                if qty_label:
                    current_qty = float(qty_label.text())
                    qty_label.setText(str(current_qty + qty))
                return

        row = self.comp_table.rowCount()
        self.comp_table.insertRow(row)
        code, desc = self.product_data.get(pos_str, ("-", "Componente Muto"))
        
        self.comp_table.setItem(row, 0, QTableWidgetItem(pos_str))
        self.comp_table.setItem(row, 1, QTableWidgetItem(code))
        self.comp_table.setItem(row, 2, QTableWidgetItem(desc))
        
        # Quantity Widget with +/-
        qty_widget = QWidget()
        qty_layout = QHBoxLayout(qty_widget)
        qty_layout.setContentsMargins(5, 2, 5, 2)
        qty_layout.setSpacing(8)
        
        btn_minus = QPushButton("-")
        btn_minus.setFixedSize(22, 22)
        btn_minus.setStyleSheet("font-weight: bold;")
        
        label_qty = QLabel(str(float(qty)))
        label_qty.setAlignment(Qt.AlignCenter)
        label_qty.setFixedWidth(30)
        
        btn_plus = QPushButton("+")
        btn_plus.setFixedSize(22, 22)
        btn_plus.setStyleSheet("font-weight: bold;")
        
        btn_minus.clicked.connect(lambda: label_qty.setText(str(max(0.0, float(label_qty.text()) - 1))))
        btn_plus.clicked.connect(lambda: label_qty.setText(str(float(label_qty.text()) + 1)))
        
        qty_layout.addWidget(btn_minus)
        qty_layout.addWidget(label_qty)
        qty_layout.addWidget(btn_plus)
        self.comp_table.setCellWidget(row, 3, qty_widget)
        
        # Delete Button (CANC)
        btn_del = QPushButton("X")
        btn_del.setFixedSize(40, 25)
        btn_del.setStyleSheet("color: white; background-color: #d32f2f; font-weight: bold; border-radius: 4px;")
        btn_del.clicked.connect(lambda: self.delete_row_by_button(btn_del))
        self.comp_table.setCellWidget(row, 4, btn_del)

    def delete_row_by_button(self, button):
        point = button.mapToParent(button.rect().center())
        index = self.comp_table.indexAt(button.pos() + button.parent().pos() if button.parent() else button.pos())
        # Simplest way: find index by cell widget
        for r in range(self.comp_table.rowCount()):
            if self.comp_table.cellWidget(r, 4) == button:
                self.comp_table.removeRow(r)
                break

    def get_data(self):
        components = []
        for row in range(self.comp_table.rowCount()):
            pos_str = self.comp_table.item(row, 0).text()
            code = self.comp_table.item(row, 1).text()
            desc = self.comp_table.item(row, 2).text()
            qty_label = self.comp_table.cellWidget(row, 3).layout().itemAt(1).widget()
            qty = float(qty_label.text())
            components.append({'numero': pos_str, 'codice': code, 'descrizione': desc, 'quantita': qty})
            
        return {
            'prodotto': self.product_id,
            'ore': self.spin_hours.value(),
            'descrizione': self.txt_desc.text(),
            'note': self.txt_notes.toPlainText(),
            'componenti': components
        }


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestione Assistenze Tebo - Sistema V5 Dinamico")
        self.setBaseSize(1000, 700)
        self.resize(1000, 700)
        
        self.db = DatabaseManager()
        self.registry = ProductRegistry()
        
        self.setup_ui()
        self.load_interventi()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        header_layout = QHBoxLayout()
        label_title = QLabel("Cronologia Interventi Tecnici")
        # Header with Product Selection
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #f0f4f5; border-bottom: 2px solid #007c91;")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel("GESTIONE ASSISTENZE TEBO")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #007c91;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        header_layout.addWidget(QLabel("Seleziona Prodotto:"))
        self.combo_products = QComboBox()
        self.combo_products.setFixedWidth(250)
        self.combo_products.addItems(self.registry.get_available_products())
        self.combo_products.currentTextChanged.connect(self.load_interventi)
        header_layout.addWidget(self.combo_products)
        
        main_layout.addWidget(header_widget)

        # History Table Section
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(15, 15, 15, 5)
        
        table_layout.addWidget(QLabel("<b>Cronologia Interventi</b>"))
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Data", "Ore", "Descrizione Attività", "Componenti"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self.edit_intervention)
        table_layout.addWidget(self.table)
        
        main_layout.addWidget(table_container, 1) # Give table stretch
        
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 10, 0, 0)
        
        self.btn_edit = QPushButton("MODIFICA INTERVENTO SELEZIONATO")
        self.btn_edit.clicked.connect(self.edit_intervention)
        self.btn_edit.setMinimumHeight(50)
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #333; }
        """)
        action_layout.addWidget(self.btn_edit, 1)
        
        self.btn_delete = QPushButton("ELIMINA INTERVENTO")
        self.btn_delete.clicked.connect(self.delete_selected_intervention)
        self.btn_delete.setMinimumHeight(50)
        self.btn_edit.setMinimumHeight(50) # Just in case it was missed
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #b71c1c; }
        """)
        action_layout.addWidget(self.btn_delete, 1)
        
        action_layout.addSpacing(20)
        
        btn_new = QPushButton("CREA NUOVO RAPPORTO DI ASSISTENZA")
        btn_new.clicked.connect(self.open_new_intervention)
        btn_new.setMinimumHeight(60)
        btn_new.setStyleSheet("""
            QPushButton {
                background-color: #007c91;
                color: white;
                font-weight: bold;
                font-size: 18px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #005662; }
        """)
        action_layout.addWidget(btn_new, 2)
        
        main_layout.addLayout(action_layout)

    def open_new_intervention(self):
        product_id = self.combo_products.currentText()
        if not product_id: return
            
        dialog = NewInterventionDialog(self, product_id=product_id)
        if dialog.exec():
            data = dialog.get_data()
            self.db.add_intervento(
                data['prodotto'],
                data['ore'],
                data['note'],
                data['descrizione'],
                data['componenti']
            )
            self.load_interventi()

    def on_new_product_ready(self, base_name):
        """ Riceve l'evento dal Watcher di sfondo quando un PDF è stato analizzato """
        # Ricarichiamo i prodotti interni dal registry
        self.registry.scan_products()
        
        # Aggiorniamo la combo mantenendo l'attuale selezione se possibile
        current = self.combo_products.currentText()
        self.combo_products.blockSignals(True)
        self.combo_products.clear()
        self.combo_products.addItems(self.registry.get_available_products())
        self.combo_products.blockSignals(False)
        
        if current in self.registry.get_available_products():
            self.combo_products.setCurrentText(current)

    def edit_intervention(self):
        row = self.table.currentRow()
        if row < 0: return
        
        # Get ID from data if stored or find by index
        try:
            interventi = self.db.get_interventi(self.combo_products.currentText())
            report = interventi[row]
            
            dialog = NewInterventionDialog(self, product_id=self.combo_products.currentText(), existing_id=report.id)
            if dialog.exec():
                data = dialog.get_data()
                self.db.update_intervento(
                    report.id,
                    data['ore'],
                    data['note'],
                    data['descrizione'],
                    data['componenti']
                )
                self.load_interventi()
        except Exception as e:
            print(f"Error editing: {e}")

    def delete_selected_intervention(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Attenzione", "Seleziona un intervento da eliminare.")
            return
            
        try:
            interventi = self.db.get_interventi(self.combo_products.currentText())
            report = interventi[row]
            
            confirm = QMessageBox.question(
                self, "Conferma Eliminazione",
                f"Sei sicuro di voler eliminare l'intervento del {report.data.strftime('%d/%m/%Y')}?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                if self.db.delete_intervento(report.id):
                    QMessageBox.information(self, "Eliminato", "Intervento eliminato con successo.")
                    self.load_interventi()
                else:
                    QMessageBox.critical(self, "Errore", "Impossibile eliminare l'intervento.")
        except Exception as e:
            print(f"Error deleting: {e}")

    def load_interventi(self):
        try:
            cur_product = self.combo_products.currentText()
            interventi = self.db.get_interventi(cur_product)
            self.table.setRowCount(len(interventi))
            for i, inv in enumerate(interventi):
                self.table.setItem(i, 0, QTableWidgetItem(inv.data.strftime("%d/%m/%Y %H:%M")))
                self.table.setItem(i, 1, QTableWidgetItem(f"{inv.ore_lavoro} h"))
                self.table.setItem(i, 2, QTableWidgetItem(inv.descrizione or ""))
                
                details = [f"{c.numero_componente} x{c.quantita}" for c in inv.componenti]
                self.table.setItem(i, 3, QTableWidgetItem(", ".join(details) if details else "-"))
        except Exception as e:
            print(f"Error loading history: {e}")
