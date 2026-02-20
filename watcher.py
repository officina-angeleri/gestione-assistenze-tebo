import os
from PySide6.QtCore import QObject, QFileSystemWatcher, Signal, Slot, QThread
from ocr_engine import OcrEngine

class OcrWorker(QObject):
    finished = Signal(str, bool)

    def __init__(self, file_path, output_dir):
        super().__init__()
        self.file_path = file_path
        self.output_dir = output_dir
        self.engine = OcrEngine()

    @Slot()
    def run(self):
        success = self.engine.process_drawing(self.file_path, self.output_dir)
        self.finished.emit(self.file_path, success)

class DrawingsWatcher(QObject):
    new_product_ready = Signal(str)

    def __init__(self, drawings_dir='disegni', parent=None):
        super().__init__(parent)
        self.drawings_dir = os.path.abspath(drawings_dir)
        if not os.path.exists(self.drawings_dir):
            os.makedirs(self.drawings_dir)
            
        self.watcher = QFileSystemWatcher([self.drawings_dir], self)
        self.watcher.directoryChanged.connect(self.on_directory_changed)
        
        self.active_threads = []
        self._processed_files = set()
        
        # Scansione arretrati all'avvio
        self.scan_existing()

    def scan_existing(self):
        for f in os.listdir(self.drawings_dir):
            if f.lower().endswith('.pdf'):
                self.check_and_process(os.path.join(self.drawings_dir, f))

    def on_directory_changed(self, path):
        for f in os.listdir(self.drawings_dir):
            if f.lower().endswith('.pdf'):
                self.check_and_process(os.path.join(self.drawings_dir, f))

    def check_and_process(self, file_path):
        if file_path in self._processed_files:
            return
            
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        coords_path = os.path.join(self.drawings_dir, f"{base_name}.coords.json")
        
        if not os.path.exists(coords_path):
            print(f"[WATCHER] Rilevato file non processato: {base_name}")
            self._processed_files.add(file_path)
            self._start_worker(file_path)

    def _start_worker(self, file_path):
        thread = QThread()
        worker = OcrWorker(file_path, self.drawings_dir)
        worker.moveToThread(thread)
        
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        worker.finished.connect(self._on_worker_finished)
        
        self.active_threads.append(thread)
        thread.start()

    @Slot(str, bool)
    def _on_worker_finished(self, file_path, success):
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        if success:
            print(f"[WATCHER] Elaborazione completata per {base_name}")
            self.new_product_ready.emit(base_name)
        else:
            print(f"[WATCHER] Elaborazione fallita per {base_name}")
            # Rimuoviamo dal set così ci riprova in futuro se modificato
            if file_path in self._processed_files:
                self._processed_files.remove(file_path)
                
        # Clean up dead threads
        self.active_threads = [t for t in self.active_threads if t.isRunning()]
