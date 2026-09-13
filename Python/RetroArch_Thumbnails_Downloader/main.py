#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RetroArch Thumbnails Downloader — GUI + CLI."""
from __future__ import annotations

import json
import os
import sys
import threading
import urllib.parse
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from core.downloader import download
from core.matcher import normalize
from core.matcher_search import search_matches
from core.processor import (
    find_rom_files,
    rename_rom_for_thumbnail,
    resolve_file,
)
from core.resources import get_resource_path
from core.systems import detect_system, list_extensions, list_system_names, validate_system_extension
from core.worker_pool import WorkerPool
from ui.frmMainWindow_ui import Ui_MainWindow
from ui.match_dialog import MatchSelectionDialog


class DownloadWorker(QThread):
    progress_updated = pyqtSignal(int, int)
    log_message = pyqtSignal(str)
    finished = pyqtSignal(dict)
    request_match_selection = pyqtSignal(str, str, str, list, object)

    def __init__(self, folders, files, art_type, rename_roms,
                 enable_match_selection=False, selected_system=None):
        super().__init__()
        self.folders = list(folders)
        self.files = list(files)
        self.art_type = art_type
        self.rename_roms = rename_roms
        self.enable_match_selection = enable_match_selection
        self.selected_system = selected_system
        self.should_stop = False
        self.selection_event = threading.Event()
        self.current_selection = None

    def run(self):
        results: dict = {"success": 0, "errors": 0, "details": []}
        all_files: list[str] = list(self.files)
        for folder in self.folders:
            all_files.extend(self._find_rom_files(folder))
        total = len(all_files)
        for i, file in enumerate(all_files, start=1):
            if self.should_stop:
                break
            self.progress_updated.emit(i, total)
            try:
                self._process_one(file, results)
            except Exception as e:  # noqa: BLE001 - no tumbar el lote
                results["errors"] += 1
                results["details"].append((file, f"Error: {e}"))
                self.log_message.emit(f"✗ {os.path.basename(file)}: {e}")
        self.finished.emit(results)

    def _process_one(self, file: str, results: dict) -> None:
        resolved = resolve_file(file, self.art_type, self.selected_system)
        if resolved.status == "bad_extension":
            return self._fail(file, results, f"Extensión no compatible con {self.selected_system}")
        if resolved.status == "unknown_system":
            return self._fail(file, results, "Sistema desconocido")
        if resolved.status == "invalid_name" or not resolved.url or not resolved.name:
            return self._fail(file, results, "Nombre inválido")

        system, name, url = resolved.system or "", resolved.name, resolved.url
        result = download(url)
        if result:
            if not self.enable_match_selection:
                results["success"] += 1
                self.log_message.emit(f"✓ {os.path.basename(file)}: OK")
                if self.rename_roms:
                    self._rename_rom(file, name)
                return
            # Con diálogo: confirmar destino (coincidencia exacta)
            if self._ask_and_download(file, system, name, [(name, url)], (name, url)):
                results["success"] += 1
            else:
                self._fail(file, results, "Omitido / timeout en selección")
            return

        # Sin coincidencia exacta
        if not self.enable_match_selection:
            return self._fail(file, results, "No encontrado")
        base_name = os.path.splitext(os.path.basename(file))[0]
        matches = search_matches(system, base_name, self.art_type)
        if not matches:
            return self._fail(file, results, "No encontrado - sin coincidencias")
        if self._ask_and_download(file, system, base_name, matches, None):
            results["success"] += 1
        else:
            self._fail(file, results, "Omitido / timeout en selección")

    def _ask_and_download(self, file, system, base_name, matches, exact_match) -> bool:
        self.selection_event.clear()
        self.current_selection = None
        self.request_match_selection.emit(file, system, base_name, matches, exact_match)
        if not self.selection_event.wait(timeout=30):
            self.log_message.emit(f"✗ {os.path.basename(file)}: Timeout - sin selección")
            return False
        if not self.current_selection:
            self.log_message.emit(f"✗ {os.path.basename(file)}: Omitido por usuario")
            return False
        selected_name, selected_url, custom_path = self.current_selection
        result = download(selected_url, custom_path)
        if not result:
            self.log_message.emit(f"✗ {os.path.basename(file)}: Error en descarga")
            return False
        self.log_message.emit(f"✓ {os.path.basename(file)}: Coincidencia seleccionada")
        if self.rename_roms:
            self._rename_rom(file, selected_name)
        return True

    def _fail(self, file: str, results: dict, msg: str) -> None:
        results["errors"] += 1
        results["details"].append((file, msg))
        self.log_message.emit(f"✗ {os.path.basename(file)}: {msg}")

    def _find_rom_files(self, directory):
        return find_rom_files(directory, recursive=True)

    def _rename_rom(self, file_path, new_name):
        try:
            new_path = rename_rom_for_thumbnail(file_path, new_name)
            self.log_message.emit(
                f"→ Renombrado: {os.path.basename(file_path)} → {os.path.basename(new_path)}"
            )
        except Exception as e:  # noqa: BLE001
            self.log_message.emit(f"✗ Error renombrando {os.path.basename(file_path)}: {e}")

    def stop(self):
        self.should_stop = True


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self._apply_window_icon()
        self.folders = []
        self.files = []
        self.worker = None
        self.dark_theme = False
        self.current_language = "es"
        self.translations = {}

        self.load_translations()

        self.btnAddFolder.clicked.connect(self.add_folder)
        self.btnAddFiles.clicked.connect(self.add_files)
        self.btnStart.clicked.connect(self.start_download)

        self.actionSalir.triggered.connect(self.close)
        self.actionModoOscuro.triggered.connect(self.toggle_theme_menu)
        self.actionEspanol.triggered.connect(lambda: self.change_language(0))
        self.actionEnglish.triggered.connect(lambda: self.change_language(1))
        self.actionFrancais.triggered.connect(lambda: self.change_language(2))

        self.load_systems()

        self.btnStart.setEnabled(False)
        self.progressBar.setValue(0)
        self.txtLog.clear()

    def _apply_window_icon(self) -> None:
        """Icono de ventana (icons/retro-thumbnails.png); silencioso si falta."""
        try:
            icon_path = get_resource_path("icons/retro-thumbnails.png")
            if os.path.isfile(str(icon_path)):
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass

    def load_systems(self):
        try:
            names = list_system_names()
            if not names:
                raise FileNotFoundError("systems.json vacío")
            self.comboSystem.addItems(names)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            QMessageBox.warning(self, "Error", "No se pudo cargar la configuración de sistemas")

    def load_translations(self):
        try:
            lang_file = get_resource_path(f"locales/{self.current_language}.json")
            with open(str(lang_file), encoding="utf-8") as f:
                self.translations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            try:
                es_file = get_resource_path("locales/es.json")
                with open(str(es_file), encoding="utf-8") as f:
                    self.translations = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                self.translations = {}

    def change_language(self, index):
        language_map = {0: "es", 1: "en", 2: "fr"}
        self.current_language = language_map.get(index, "es")
        self.load_translations()
        self.apply_translations()

        self.actionEspanol.setChecked(index == 0)
        self.actionEnglish.setChecked(index == 1)
        self.actionFrancais.setChecked(index == 2)

    def apply_translations(self):
        t = self.translations
        self.setWindowTitle(t.get("window_title", "Retro Thumbnails PRO"))
        self.btnAddFolder.setText(t.get("btn_add_folder", "Añadir carpeta"))
        self.btnAddFiles.setText(t.get("btn_add_files", "Añadir archivos ROM"))
        self.btnStart.setText(t.get("btn_start", "Iniciar"))
        self.chkRename.setText(t.get("chk_rename", "Renombrar ROMs"))
        self.chkMatchSelection.setText(t.get("chk_match_selection", "Buscar coincidencias alternativas"))
        self.menuArchivo.setTitle(t.get("menu_file", "Archivo"))
        self.menuTema.setTitle(t.get("menu_theme", "Tema"))
        self.menuIdioma.setTitle(t.get("menu_language", "Idioma"))
        self.actionSalir.setText(t.get("action_exit", "Salir"))
        self.actionModoOscuro.setText(t.get("action_dark_mode", "Modo oscuro"))
        self.actionEspanol.setText(t.get("lang_spanish", "Español"))
        self.actionEnglish.setText(t.get("lang_english", "English"))
        self.actionFrancais.setText(t.get("lang_french", "Français"))

    def toggle_theme_menu(self, checked):
        self.dark_theme = bool(checked)
        self.apply_dark_theme() if self.dark_theme else self.apply_light_theme()

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; }
            QWidget { background-color: #2b2b2b; color: #ffffff; }
            QPushButton { background-color: #404040; color: #ffffff; border: 1px solid #555555; padding: 5px; }
            QPushButton:hover { background-color: #505050; }
            QPushButton:disabled { background-color: #303030; color: #888888; }
            QListWidget { background-color: #404040; color: #ffffff; border: 1px solid #555555; }
            QComboBox { background-color: #404040; color: #ffffff; border: 1px solid #555555; }
            QComboBox QAbstractItemView { background-color: #404040; color: #ffffff; }
            QCheckBox { color: #ffffff; }
            QProgressBar { background-color: #404040; border: 1px solid #555555; }
            QProgressBar::chunk { background-color: #4CAF50; }
            QTextEdit { background-color: #404040; color: #ffffff; border: 1px solid #555555; }
        """)

    def apply_light_theme(self):
        self.setStyleSheet("")

    def add_folder(self):
        t = self.translations
        folder = QFileDialog.getExistingDirectory(self, t.get("msg_select_folder", "Seleccionar carpeta de ROMs"))
        if folder and folder not in self.folders:
            self.files.clear()
            self.listFolders.clear()
            self.folders.clear()
            self.folders.append(folder)
            self.listFolders.addItem(f"[{t.get('msg_folder', 'Carpeta')}] {folder}")
            self.btnStart.setEnabled(len(self.folders) > 0 or len(self.files) > 0)

    def add_files(self):
        t = self.translations
        extensions_list = list_extensions()
        extensions_str = " ".join(ext.replace(".", "*.") for ext in extensions_list)
        extensions = [
            f"{t.get('msg_rom_files', 'ROM files')} ({extensions_str})",
            f"{t.get('msg_all_files', 'All files')} (*.*)",
        ]
        files, _ = QFileDialog.getOpenFileNames(
            self, t.get("msg_select_files", "Seleccionar archivos ROM"), "", ";;".join(extensions)
        )
        if files:
            self.folders.clear()
            self.listFolders.clear()
            self.files.clear()
            for file in files:
                if file and file not in self.files:
                    self.files.append(file)
                    self.listFolders.addItem(f"[{t.get('msg_file', 'Archivo')}] {os.path.basename(file)}")
            self.btnStart.setEnabled(len(self.folders) > 0 or len(self.files) > 0)

    def start_download(self):
        t = self.translations
        if not self.folders and not self.files:
            QMessageBox.warning(self, "Advertencia", t.get("msg_warning_no_items", "Añade carpeta o archivo ROM"))
            return
        message = t.get(
            "msg_confirm_start", "¿Iniciar descarga para {folders} carpeta(s) y {files} archivo(s)?"
        ).format(folders=len(self.folders), files=len(self.files))
        if QMessageBox.question(self, "Confirmar", message, QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return
        self.btnStart.setEnabled(False)
        self.btnAddFolder.setEnabled(False)
        self.progressBar.setValue(0)
        self.txtLog.clear()

        art_type = self.comboArt.currentText()
        rename_roms = self.chkRename.isChecked()
        enable_match_selection = self.chkMatchSelection.isChecked()
        selected_system = self.comboSystem.currentText() if self.comboSystem.currentIndex() > 0 else None

        self.worker = DownloadWorker(
            self.folders, self.files, art_type, rename_roms, enable_match_selection, selected_system
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_message.connect(self.add_log)
        self.worker.finished.connect(self.download_finished)
        self.worker.request_match_selection.connect(self.handle_match_selection)
        self.worker.start()

    def update_progress(self, current, total):
        if total > 0:
            self.progressBar.setValue(int((current / total) * 100))

    def add_log(self, message):
        self.txtLog.append(message)
        scrollbar = self.txtLog.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def handle_match_selection(self, file, system, base_name, matches, exact_match=None):
        dialog = MatchSelectionDialog(os.path.basename(file), matches, self, exact_match=exact_match)
        if dialog.exec_() == QDialog.Accepted:
            selected_name, selected_url, custom_path = dialog.get_selection()
            if selected_url and selected_url != "CANCEL_ALL":
                self.worker.current_selection = (selected_name, selected_url, custom_path)
                self.worker.selection_event.set()
                if custom_path:
                    self.add_log(f"→ Usuario seleccionó: {selected_name} (guardar en: {custom_path})")
                else:
                    self.add_log(f"→ Usuario seleccionó: {selected_name}")
            elif selected_url == "CANCEL_ALL":
                self.worker.current_selection = None
                self.worker.selection_event.set()
                self.worker.stop()
                self.add_log("→ Usuario canceló el proceso")
        else:
            self.worker.current_selection = None
            self.worker.selection_event.set()
            self.add_log(f"→ Usuario omitió: {os.path.basename(file)}")

    def download_finished(self, results):
        t = self.translations
        self.btnStart.setEnabled(True)
        self.btnAddFolder.setEnabled(True)
        msg = f"{t.get('msg_download_complete', 'Descarga completada:')}\n\n"
        msg += f"{t.get('msg_successful', 'Exitosos:')}: {results['success']}\n"
        msg += f"{t.get('msg_errors', 'Con errores:')}: {results['errors']}\n"
        if results["errors"] > 0:
            msg += f"\n{t.get('msg_error_details', 'Errores detallados:')}\n"
            for file, error in results["details"][:10]:
                msg += f"• {os.path.basename(file)}: {error}\n"
            if len(results["details"]) > 10:
                msg += f"... y {len(results['details']) - 10} errores más"
        QMessageBox.information(self, "Proceso completado", msg)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Confirmar salida",
                "Hay un proceso en ejecución. ¿Deseas cancelarlo y salir?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def process_file(file):
    """Compat CLI: (file, status)."""
    from core.processor import process_file as _pf
    r = _pf(file, "Named_Boxarts", None)
    mapping = {
        "ok": "OK", "not_found": "No encontrado",
        "unknown_system": "Sistema desconocido", "invalid_name": "Nombre inválido",
        "bad_extension": "Sistema desconocido",
    }
    return (file, mapping.get(r.status, r.message))


def cli_mode():
    if len(sys.argv) != 2:
        print("Uso: python main.py <directorio_de_roms>")
        sys.exit(1)
    rom_directory = sys.argv[1]
    if not os.path.exists(rom_directory):
        print(f"Error: El directorio '{rom_directory}' no existe")
        sys.exit(1)
    files = find_rom_files(rom_directory, recursive=True)
    if not files:
        print("No se encontraron archivos ROM en el directorio")
        sys.exit(0)
    print(f"Procesando {len(files)} archivos...")
    with WorkerPool(8) as pool:
        results = pool.map(process_file, files)
        success_count = sum(1 for _, status in results if status == "OK")
        print("\nResultados:")
        print(f"Exitosos: {success_count}")
        print(f"Con errores: {len(results) - success_count}")
        for file, status in results:
            if status != "OK":
                print(f"  {file}: {status}")


def main():
    if len(sys.argv) > 1:
        cli_mode()
    else:
        app = QApplication(sys.argv)
        app.setApplicationName("RetroArch Thumbnails Downloader")
        # Asocia la ventana con retro-thumbnails.desktop (icono en dock/Wayland).
        try:
            app.setDesktopFileName("retro-thumbnails")
        except Exception:
            pass
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())


if __name__ == "__main__":
    main()
