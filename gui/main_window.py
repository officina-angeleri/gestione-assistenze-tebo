import os
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QSplitter, QDialog, QFormLayout, 
                             QLineEdit, QDoubleSpinBox, QTextEdit, QComboBox, QMessageBox, QGroupBox,
                             QTabWidget, QScrollArea, QFrame, QFileDialog)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QDate, QTimer
import shutil
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
        self.resize(800, 950)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
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
        main_layout.addWidget(info_group)
        
        table_group = QGroupBox("Pezzi Sostituiti")
        table_layout = QVBoxLayout(table_group)
        
        self.btn_open_calibrator = QPushButton("APRI ESPLOSO TECNICO E SELEZIONA PEZZI")
        self.btn_open_calibrator.setMinimumHeight(40)
        self.btn_open_calibrator.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; font-size: 14px; border-radius: 4px; margin-bottom: 10px;")
        self.btn_open_calibrator.clicked.connect(self.open_calibrator)
        table_layout.addWidget(self.btn_open_calibrator)

        self.comp_table = QTableWidget()
        self.comp_table.setColumnCount(5)
        self.comp_table.setHorizontalHeaderLabels(["POS", "CODICE", "DESCRIZIONE", "QTY", "AZIONE"])
        self.comp_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.comp_table.setAlternatingRowColors(True)
        table_layout.addWidget(self.comp_table)
        main_layout.addWidget(table_group)
        
        self.btn_save = QPushButton("SALVA E CHIUDI")
        self.btn_save.clicked.connect(self.accept)
        self.btn_save.setMinimumHeight(60)
        self.btn_save.setStyleSheet("background-color: #007c91; color: white; font-weight: bold; font-size: 18px; border-radius: 4px;")
        main_layout.addWidget(self.btn_save)
        
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
    def open_calibrator(self):
        calib_dialog = QDialog(self)
        calib_dialog.setWindowTitle(f"Esploso Tecnico - {self.product_id}")
        calib_dialog.resize(1300, 800)
        
        # Fix: Assicuriamoci di poter ridimensionare/massimizzare il modale
        calib_dialog.setWindowFlags(calib_dialog.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        layout = QVBoxLayout(calib_dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        from gui.calibrator_widget import DrawingCalibratorWidget
        # Lo usiamo in modalità INTERVENTO
        widget = DrawingCalibratorWidget(self.product_id, mode="INTERVENTION", parent=calib_dialog)
        widget.component_selected.connect(self.on_component_selected_from_map)
        layout.addWidget(widget)
        
        calib_dialog.exec()
        
    def on_component_selected_from_map(self, pos_str, code, desc):
        pos_num = pos_str # string compatibility
        # Update existing if found
        for row in range(self.comp_table.rowCount()):
            if self.comp_table.item(row, 0).text() == pos_str:
                qty_label = self.comp_table.cellWidget(row, 3).findChild(QLabel)
                if qty_label:
                    current_qty = float(qty_label.text())
                    qty_label.setText(str(current_qty + 1.0))
                return

        row = self.comp_table.rowCount()
        self.comp_table.insertRow(row)
        
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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabBar::tab { height: 40px; width: 220px; font-weight: bold; font-size: 14px; background: #e0e0e0; margin: 2px; border-radius: 4px; }
            QTabBar::tab:selected { background: #007c91; color: white; }
            QTabWidget::pane { border: 0px; }
        """)
        main_layout.addWidget(self.tabs)
        
        # TAB 1: Interventi
        tab_interventi = QWidget()
        self.setup_interventi_tab(tab_interventi)
        self.tabs.addTab(tab_interventi, "Rapporti di Intervento")
        
        # TAB 2: Archivio
        tab_archivio = QWidget()
        self.setup_archivio_tab(tab_archivio)
        self.tabs.addTab(tab_archivio, "Archivio Master Disegni")

    def setup_interventi_tab(self, parent_widget):
        main_layout = QVBoxLayout(parent_widget)
        
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

    # --------- NUOVA SEZIONE: ARCHIVIO MASTER ---------
    
    def setup_archivio_tab(self, parent_widget):
        layout = QVBoxLayout(parent_widget)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        title_label = QLabel("ARCHIVIO ESPLOSI E CALIBRAZIONI MASTER")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #007c91;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        btn_upload = QPushButton("CARICA NUOVO DISEGNO MASTER")
        btn_upload.setMinimumHeight(40)
        btn_upload.clicked.connect(self.upload_new_drawing)
        btn_upload.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 0 15px; border-radius: 4px;")
        header_layout.addWidget(btn_upload)
        
        layout.addLayout(header_layout)
        
        # Griglia
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_scroll.setStyleSheet("QScrollArea { border: none; background-color: #f5f5f5; }")
        
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: #f5f5f5;")
        from PySide6.QtWidgets import QGridLayout
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        self.grid_scroll.setWidget(self.grid_container)
        layout.addWidget(self.grid_scroll)
        
        self.refresh_archive_grid()
        
    def refresh_archive_grid(self):
        # Svuota griglia
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        products = self.registry.get_available_products()
        
        cols = 4 # Numero di colonne desiderate
        for i, prod_id in enumerate(products):
            info = self.registry.get_product_info(prod_id)
            card = self.create_drawing_card(prod_id, info)
            self.grid_layout.addWidget(card, i // cols, i % cols)
            
    def create_drawing_card(self, prod_id, info):
        card = QFrame()
        card.setFixedSize(220, 260)
        card.setStyleSheet("""
            QFrame { background-color: white; border: 1px solid #ddd; border-radius: 8px; }
            QFrame:hover { border: 2px solid #007c91; }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_preview = QLabel()
        lbl_preview.setFixedSize(198, 140)
        lbl_preview.setStyleSheet("border: 1px solid #eee; background-color: #fafafa;")
        lbl_preview.setAlignment(Qt.AlignCenter)
        
        png_path = info['drawing_path'].replace('.pdf', '.png')
        if os.path.exists(png_path):
            pix = QPixmap(png_path)
            lbl_preview.setPixmap(pix.scaled(lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            lbl_preview.setText("PDF")
        c_layout.addWidget(lbl_preview)
        
        lbl_title = QLabel(prod_id)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; border: none;")
        lbl_title.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lbl_title)
        
        calib_count = len(self.registry.get_product_coords(prod_id))
        lbl_status = QLabel(f"{calib_count} punti calibrati")
        lbl_status.setStyleSheet("color: #666; font-size: 11px; border: none;")
        lbl_status.setAlignment(Qt.AlignCenter)
        c_layout.addWidget(lbl_status)
        
        btn_edit = QPushButton("MODIFICA MASTER")
        btn_edit.setStyleSheet("background-color: #007c91; color: white; font-weight: bold; border-radius: 4px; padding: 5px;")
        btn_edit.clicked.connect(lambda _, pid=prod_id: self.open_master_calibrator(pid))
        c_layout.addWidget(btn_edit)
        
        return card

    def upload_new_drawing(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleziona Disegno Tecnico", "", "PDF/Immagini (*.pdf *.png *.jpg *.jpeg)")
        if not file_path: return
        
        base_name = os.path.basename(file_path)
        dest_path = os.path.join(self.registry.drawings_dir, base_name)
        
        try:
            shutil.copy2(file_path, dest_path)
            # Il watcher farà l'OCR. Noi aggiorniamo al volo la UI
            QMessageBox.information(self, "Upload Esterno", f"File '{base_name}' caricato con successo. Attendi l'elaborazione se è un PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile copiare: {e}")

    def open_master_calibrator(self, product_id):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Calibrazione Master - {product_id}")
        dialog.resize(1300, 800)
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowMaximizeButtonHint)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        
        from gui.calibrator_widget import DrawingCalibratorWidget
        widget = DrawingCalibratorWidget(product_id, mode="MASTER", parent=dialog)
        layout.addWidget(widget)
        
        dialog.exec()
        
        # Al ritorno aggiorniamo lo status sulla griglia e nei combobox
        self.refresh_archive_grid()
