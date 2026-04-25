#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import json
import threading
import urllib.parse
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFileDialog, 
                             QMessageBox, QInputDialog, QCheckBox, QDialog, QPushButton, QAction, QComboBox, QLabel)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from ui.frmMainWindow_ui import Ui_MainWindow
from core.scanner import expand_systems
from ui.match_dialog import MatchSelectionDialog
from core.scanner import detect_system
from core.matcher import normalize
from core.matcher_search import search_matches
from core.downloader import download
from core.worker_pool import WorkerPool

def get_resource_path(relative_path):
    """Obtiene la ruta absoluta a un recurso, funciona tanto en desarrollo como en ejecutable PyInstaller"""
    try:
        # PyInstaller crea una carpeta temporal en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # En desarrollo, usar el directorio del script actual
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class DownloadWorker(QThread):
    progress_updated = pyqtSignal(int, int)
    log_message = pyqtSignal(str)
    finished = pyqtSignal(dict)
    request_match_selection = pyqtSignal(str, str, str, list, object)  # file, system, base_name, matches, exact_match
    
    def __init__(self, folders, files, art_type, rename_roms, enable_match_selection=False):
        super().__init__()
        self.folders = folders
        self.files = files  # Lista de archivos individuales
        self.art_type = art_type
        self.rename_roms = rename_roms
        self.enable_match_selection = enable_match_selection
        self.should_stop = False
        self.user_selections = {}  # Almacenar selecciones del usuario
        self.selection_event = threading.Event()  # Evento para sincronización
        self.current_selection = None  # Selección actual del usuario
        
    def run(self):
        results = {"success": 0, "errors": 0, "details": []}
        total_files = 0
        
        # Contar archivos de carpetas
        for folder in self.folders:
            total_files += len(self._find_rom_files(folder))
        
        # Agregar archivos individuales
        total_files += len(self.files)
        
        processed = 0
        
        # Procesar carpetas
        for folder in self.folders:
            files = self._find_rom_files(folder)
            
            for file in files:
                if self.should_stop:
                    break
                    
                processed += 1
                self.progress_updated.emit(processed, total_files)
                
                try:
                    system = detect_system(file)
                    if not system:
                        results["errors"] += 1
                        results["details"].append((file, "Sistema desconocido"))
                        continue

                    name = normalize(file)
                    if not name:
                        results["errors"] += 1
                        results["details"].append((file, "Nombre inválido"))
                        continue

                    url = f"https://thumbnails.libretro.com/{system}/{self.art_type}/{name}.png"
                    result = download(url)

                    if result:
                        # Coincidencia exacta encontrada
                        if self.enable_match_selection:
                            # Mostrar diálogo para permitir selección de carpeta personalizada
                            self.selection_event.clear()
                            self.current_selection = None
                            self.request_match_selection.emit(file, system, name, [(name, url)], (name, url))
                            
                            # Esperar a que el usuario seleccione (con timeout de 30 segundos)
                            if self.selection_event.wait(timeout=30):
                                # Usuario hizo una selección
                                if self.current_selection:
                                    selected_name, selected_url, custom_path = self.current_selection
                                    result = download(selected_url, custom_path)
                                    
                                    if result:
                                        results["success"] += 1
                                        self.log_message.emit(f"✓ {os.path.basename(file)}: Coincidencia seleccionada")
                                        
                                        if self.rename_roms:
                                            self._rename_rom(file, selected_name)
                                    else:
                                        results["errors"] += 1
                                        results["details"].append((file, "Error en descarga"))
                                        self.log_message.emit(f"✗ {os.path.basename(file)}: Error en descarga")
                            else:
                                results["errors"] += 1
                                results["details"].append((file, "Timeout - sin selección"))
                                self.log_message.emit(f"✗ {os.path.basename(file)}: Timeout - sin selección")
                        else:
                            # Descarga directa sin diálogo
                            results["success"] += 1
                            self.log_message.emit(f"✓ {os.path.basename(file)}: OK")
                            
                            if self.rename_roms:
                                self._rename_rom(file, name)
                    else:
                        # No se encontró coincidencia exacta, buscar alternativas
                        if self.enable_match_selection:
                            base_name = os.path.splitext(os.path.basename(file))[0]
                            matches = search_matches(system, base_name, self.art_type)
                            
                            if matches and len(matches) > 0:
                                # Solicitar selección al usuario (sin coincidencia exacta)
                                self.selection_event.clear()
                                self.current_selection = None
                                self.request_match_selection.emit(file, system, base_name, matches, None)
                                
                                # Esperar a que el usuario seleccione (con timeout de 30 segundos)
                                if self.selection_event.wait(timeout=30):
                                    # Usuario hizo una selección
                                    if self.current_selection:
                                        selected_name, selected_url, custom_path = self.current_selection
                                        result = download(selected_url, custom_path)
                                        
                                        if result:
                                            results["success"] += 1
                                            self.log_message.emit(f"✓ {os.path.basename(file)}: Coincidencia seleccionada")
                                            
                                            if self.rename_roms:
                                                self._rename_rom(file, selected_name)
                                        else:
                                            results["errors"] += 1
                                            results["details"].append((file, "Error en coincidencia seleccionada"))
                                            self.log_message.emit(f"✗ {os.path.basename(file)}: Error en coincidencia seleccionada")
                                else:
                                    results["errors"] += 1
                                    results["details"].append((file, "Timeout - sin selección"))
                                    self.log_message.emit(f"✗ {os.path.basename(file)}: Timeout - sin selección")
                            else:
                                results["errors"] += 1
                                results["details"].append((file, "No encontrado - sin coincidencias"))
                                self.log_message.emit(f"✗ {os.path.basename(file)}: No encontrado - sin coincidencias")
                        else:
                            results["errors"] += 1
                            results["details"].append((file, "No encontrado"))
                            self.log_message.emit(f"✗ {os.path.basename(file)}: No encontrado")
                        
                except Exception as e:
                    results["errors"] += 1
                    results["details"].append((file, f"Error: {str(e)}"))
                    self.log_message.emit(f"✗ {os.path.basename(file)}: {str(e)}")
        
        # Procesar archivos individuales
        for file in self.files:
            if self.should_stop:
                break
                
            processed += 1
            self.progress_updated.emit(processed, total_files)
            
            try:
                system = detect_system(file)
                if not system:
                    results["errors"] += 1
                    results["details"].append((file, "Sistema desconocido"))
                    continue

                name = normalize(file)
                if not name:
                    results["errors"] += 1
                    results["details"].append((file, "Nombre inválido"))
                    continue

                url = f"https://thumbnails.libretro.com/{system}/{self.art_type}/{name}.png"
                result = download(url)

                if result:
                    # Coincidencia exacta encontrada
                    if self.enable_match_selection:
                        # Mostrar diálogo para permitir selección de carpeta personalizada
                        self.selection_event.clear()
                        self.current_selection = None
                        self.request_match_selection.emit(file, system, name, [(name, url)], (name, url))
                        
                        # Esperar a que el usuario seleccione (con timeout de 30 segundos)
                        if self.selection_event.wait(timeout=30):
                            # Usuario hizo una selección
                            if self.current_selection:
                                selected_name, selected_url, custom_path = self.current_selection
                                result = download(selected_url, custom_path)
                                
                                if result:
                                    results["success"] += 1
                                    self.log_message.emit(f"✓ {os.path.basename(file)}: Coincidencia seleccionada")
                                    
                                    if self.rename_roms:
                                        self._rename_rom(file, selected_name)
                                else:
                                    results["errors"] += 1
                                    results["details"].append((file, "Error en descarga"))
                                    self.log_message.emit(f"✗ {os.path.basename(file)}: Error en descarga")
                            else:
                                # Usuario omitió el archivo
                                results["errors"] += 1
                                results["details"].append((file, "Omitido por usuario"))
                                self.log_message.emit(f"✗ {os.path.basename(file)}: Omitido por usuario")
                        else:
                            # Timeout - usuario no seleccionó
                            results["errors"] += 1
                            results["details"].append((file, "Timeout - sin selección"))
                            self.log_message.emit(f"✗ {os.path.basename(file)}: Timeout - sin selección")
                    else:
                        # Descarga directa sin diálogo
                        results["success"] += 1
                        self.log_message.emit(f"✓ {os.path.basename(file)}: OK")
                        
                        if self.rename_roms:
                            self._rename_rom(file, name)
                else:
                    # No se encontró coincidencia exacta, buscar alternativas
                    if self.enable_match_selection:
                        base_name = os.path.splitext(os.path.basename(file))[0]
                        matches = search_matches(system, base_name, self.art_type)
                        
                        if matches and len(matches) > 0:
                            # Solicitar selección al usuario (sin coincidencia exacta)
                            self.selection_event.clear()
                            self.current_selection = None
                            self.request_match_selection.emit(file, system, base_name, matches, None)
                            
                            # Esperar a que el usuario seleccione (con timeout de 30 segundos)
                            if self.selection_event.wait(timeout=30):
                                # Usuario hizo una selección
                                if self.current_selection:
                                    selected_name, selected_url, custom_path = self.current_selection
                                    result = download(selected_url, custom_path)
                                    
                                    if result:
                                        results["success"] += 1
                                        self.log_message.emit(f"✓ {os.path.basename(file)}: Coincidencia seleccionada")
                                        
                                        if self.rename_roms:
                                            self._rename_rom(file, selected_name)
                                    else:
                                        results["errors"] += 1
                                        results["details"].append((file, "Error en coincidencia seleccionada"))
                                        self.log_message.emit(f"✗ {os.path.basename(file)}: Error en coincidencia seleccionada")
                                else:
                                    # Usuario omitió el archivo
                                    results["errors"] += 1
                                    results["details"].append((file, "Omitido por usuario"))
                                    self.log_message.emit(f"✗ {os.path.basename(file)}: Omitido por usuario")
                            else:
                                # Timeout - usuario no seleccionó
                                results["errors"] += 1
                                results["details"].append((file, "Timeout - sin selección"))
                                self.log_message.emit(f"✗ {os.path.basename(file)}: Timeout - sin selección")
                        else:
                            results["errors"] += 1
                            results["details"].append((file, "No encontrado - sin coincidencias"))
                            self.log_message.emit(f"✗ {os.path.basename(file)}: No encontrado - sin coincidencias")
                    else:
                        results["errors"] += 1
                        results["details"].append((file, "No encontrado"))
                        self.log_message.emit(f"✗ {os.path.basename(file)}: No encontrado")
                    
            except Exception as e:
                results["errors"] += 1
                results["details"].append((file, f"Error: {str(e)}"))
                self.log_message.emit(f"✗ {os.path.basename(file)}: {str(e)}")
        
        self.finished.emit(results)
    
    def _find_rom_files(self, directory):
        # Leer extensiones desde systems.json
        try:
            systems_path = get_resource_path('data/systems.json')
            with open(systems_path, 'r') as f:
                systems = json.load(f)
                expanded_systems = expand_systems(systems)
                extensions = list(expanded_systems.keys())
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback a extensiones por defecto si no se puede leer el archivo
            extensions = ['.nes', '.sfc', '.smc', '.gba', '.nds', '.iso', '.bin']
        
        files = []
        for ext in extensions:
            pattern = os.path.join(directory, f"*{ext}")
            files.extend(glob.glob(pattern))
            pattern_upper = os.path.join(directory, f"*{ext.upper()}")
            files.extend(glob.glob(pattern_upper))
        return files
    
    def _rename_rom(self, file_path, new_name):
        try:
            directory = os.path.dirname(file_path)
            ext = os.path.splitext(file_path)[1]
            
            # Decodificar el nombre para que sea legible (quitar %20, %28, etc.)
            decoded_name = urllib.parse.unquote(new_name)
            
            new_path = os.path.join(directory, f"{decoded_name}{ext}")
            
            counter = 1
            original_new_path = new_path
            while os.path.exists(new_path):
                name_part = os.path.splitext(original_new_path)[0]
                new_path = os.path.join(directory, f"{name_part}_{counter}{ext}")
                counter += 1
            
            os.rename(file_path, new_path)
            self.log_message.emit(f"→ Renombrado: {os.path.basename(file_path)} → {os.path.basename(new_path)}")
        except Exception as e:
            self.log_message.emit(f"✗ Error renombrando {os.path.basename(file_path)}: {str(e)}")
    
    def stop(self):
        self.should_stop = True

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.folders = []
        self.files = []  # Lista de archivos individuales
        self.worker = None
        self.dark_theme = False  # Estado del tema
        self.current_language = "es"  # Idioma actual
        self.translations = {}  # Diccionario de traducciones
        
        # Cargar traducciones
        self.load_translations()
        
        # Conectar señales
        self.btnAddFolder.clicked.connect(self.add_folder)
        self.btnAddFiles.clicked.connect(self.add_files)
        self.btnStart.clicked.connect(self.start_download)
        
        # Conectar acciones del menubar
        self.actionSalir.triggered.connect(self.close)
        self.actionModoOscuro.triggered.connect(self.toggle_theme_menu)
        self.actionEspanol.triggered.connect(lambda: self.change_language(0))
        self.actionEnglish.triggered.connect(lambda: self.change_language(1))
        self.actionFrancais.triggered.connect(lambda: self.change_language(2))
        
        self.load_systems()
        
        self.btnStart.setEnabled(False)
        self.progressBar.setValue(0)
        self.txtLog.clear()
        
    def load_systems(self):
        try:
            systems_path = get_resource_path('data/systems.json')
            with open(systems_path, 'r') as f:
                systems = json.load(f)
                # Usar los valores directamente (nombres de sistemas) sin duplicados
                system_names = list(dict.fromkeys(systems.values()))
                self.comboSystem.addItems(system_names)
        except (FileNotFoundError, json.JSONDecodeError):
            QMessageBox.warning(self, "Error", "No se pudo cargar la configuración de sistemas")
    
    def load_translations(self):
        try:
            lang_file = get_resource_path(f"locales/{self.current_language}.json")
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback a español si no se puede cargar
            try:
                es_file = get_resource_path('locales/es.json')
                with open(es_file, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
            except:
                self.translations = {}
    
    def change_language(self, index):
        language_map = {0: "es", 1: "en", 2: "fr"}
        self.current_language = language_map.get(index, "es")
        self.load_translations()
        self.apply_translations()
        
        # Actualizar checks exclusivos en menú de idioma
        self.actionEspanol.setChecked(index == 0)
        self.actionEnglish.setChecked(index == 1)
        self.actionFrancais.setChecked(index == 2)
    
    def apply_translations(self):
        t = self.translations
        
        # Aplicar traducciones a los elementos de la UI
        self.setWindowTitle(t.get("window_title", "Retro Thumbnails PRO"))
        self.btnAddFolder.setText(t.get("btn_add_folder", "Añadir carpeta"))
        self.btnAddFiles.setText(t.get("btn_add_files", "Añadir archivos ROM"))
        self.btnStart.setText(t.get("btn_start", "Iniciar"))
        self.chkRename.setText(t.get("chk_rename", "Renombrar ROMs"))
        self.chkMatchSelection.setText(t.get("chk_match_selection", "Buscar coincidencias alternativas"))
        
        # Actualizar menubar
        self.menuArchivo.setTitle(t.get("menu_file", "Archivo"))
        self.menuTema.setTitle(t.get("menu_theme", "Tema"))
        self.menuIdioma.setTitle(t.get("menu_language", "Idioma"))
        self.actionSalir.setText(t.get("action_exit", "Salir"))
        self.actionModoOscuro.setText(t.get("action_dark_mode", "Modo oscuro"))
        self.actionEspanol.setText(t.get("lang_spanish", "Español"))
        self.actionEnglish.setText(t.get("lang_english", "English"))
        self.actionFrancais.setText(t.get("lang_french", "Français"))
    
    def toggle_theme_menu(self, checked):
        if checked:
            self.dark_theme = True
            self.apply_dark_theme()
        else:
            self.dark_theme = False
            self.apply_light_theme()
    
    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:disabled {
                background-color: #303030;
                color: #888888;
            }
            QListWidget {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QComboBox {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
            }
            QProgressBar {
                background-color: #404040;
                border: 1px solid #555555;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
            }
            QTextEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
            }
        """)
    
    def apply_light_theme(self):
        self.setStyleSheet("")
    
    def add_folder(self):
        t = self.translations
        folder = QFileDialog.getExistingDirectory(self, t.get("msg_select_folder", "Seleccionar carpeta de ROMs"))
        if folder and folder not in self.folders:
            # Limpiar archivos individuales al agregar carpeta
            self.files.clear()
            self.listFolders.clear()
            self.folders.clear()
            
            self.folders.append(folder)
            self.listFolders.addItem(f"[{t.get('msg_folder', 'Carpeta')}] {folder}")
            self.btnStart.setEnabled(len(self.folders) > 0 or len(self.files) > 0)
    
    def add_files(self):
        t = self.translations
        # Leer extensiones desde systems.json
        try:
            systems_path = get_resource_path('data/systems.json')
            with open(systems_path, 'r') as f:
                systems = json.load(f)
                expanded_systems = expand_systems(systems)
                extensions_list = list(expanded_systems.keys())
                # Convertir extensiones para el filtro (quitar el punto)
                extensions_str = ' '.join(ext.replace('.', '*.') for ext in extensions_list)
                extensions = [f"{t.get('msg_rom_files', 'ROM files')} ({extensions_str})", f"{t.get('msg_all_files', 'All files')} (*.*)"]
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback a extensiones por defecto si no se puede leer el archivo
            extensions = [f"{t.get('msg_rom_files', 'ROM files')} (*.nes *.sfc *.smc *.gba *.nds *.iso *.bin)", f"{t.get('msg_all_files', 'All files')} (*.*)"]
        
        files, _ = QFileDialog.getOpenFileNames(self, t.get("msg_select_files", "Seleccionar archivos ROM"), "", ";;".join(extensions))
        
        if files:
            # Limpiar carpetas al agregar archivos
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
            QMessageBox.warning(self, "Advertencia", t.get("msg_warning_no_items", "Por favor, añade al menos una carpeta o archivo ROM"))
            return
        
        total_items = len(self.folders) + len(self.files)
        message = t.get("msg_confirm_start", "¿Iniciar descarga para {folders} carpeta(s) y {files} archivo(s)?").format(
            folders=len(self.folders), files=len(self.files)
        )
        
        reply = QMessageBox.question(self, "Confirmar", message, QMessageBox.Yes | QMessageBox.No)
        
        if reply != QMessageBox.Yes:
            return
        
        self.btnStart.setEnabled(False)
        self.btnAddFolder.setEnabled(False)
        self.progressBar.setValue(0)
        self.txtLog.clear()
        
        art_type = self.comboArt.currentText()
        rename_roms = self.chkRename.isChecked()
        enable_match_selection = self.chkMatchSelection.isChecked()
        
        self.worker = DownloadWorker(self.folders, self.files, art_type, rename_roms, enable_match_selection)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.log_message.connect(self.add_log)
        self.worker.finished.connect(self.download_finished)
        self.worker.request_match_selection.connect(self.handle_match_selection)
        
        self.worker.start()
    
    def update_progress(self, current, total):
        if total > 0:
            value = int((current / total) * 100)
            self.progressBar.setValue(value)
    
    def add_log(self, message):
        self.txtLog.append(message)
        scrollbar = self.txtLog.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def handle_match_selection(self, file, system, base_name, matches, exact_match=None):
        """Maneja la solicitud de selección de coincidencias"""
        dialog = MatchSelectionDialog(os.path.basename(file), matches, self, exact_match=exact_match)
        
        if dialog.exec_() == QDialog.Accepted:
            selected_name, selected_url, custom_path = dialog.get_selection()
            if selected_url and selected_url != "CANCEL_ALL":
                # Establecer la selección para que el worker la use
                self.worker.current_selection = (selected_name, selected_url, custom_path)
                self.worker.selection_event.set()
                if custom_path:
                    self.add_log(f"→ Usuario seleccionó: {selected_name} (guardar en: {custom_path})")
                else:
                    self.add_log(f"→ Usuario seleccionó: {selected_name}")
            elif selected_url == "CANCEL_ALL":
                # Cancelar todo el proceso
                self.worker.current_selection = None
                self.worker.selection_event.set()
                self.worker.stop()
                self.add_log("→ Usuario canceló el proceso")
        else:
            # Usuario omitió este archivo
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
        
        if results['errors'] > 0:
            msg += f"\n{t.get('msg_error_details', 'Errores detallados:')}\n"
            for file, error in results['details'][:10]:
                msg += f"• {os.path.basename(file)}: {error}\n"
            if len(results['details']) > 10:
                msg += f"... y {len(results['details']) - 10} errores más"
        
        QMessageBox.information(self, "Proceso completado", msg)
    
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(self, "Confirmar salida", 
                                       "Hay un proceso en ejecución. ¿Deseas cancelarlo y salir?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def process_file(file):
    try:
        system = detect_system(file)
        if not system:
            return (file, "Sistema desconocido")

        name = normalize(file)
        if not name:
            return (file, "Nombre inválido")

        url = f"https://thumbnails.libretro.com/{system}/Named_Boxarts/{name}.png"
        result = download(url)

        if result:
            return (file, "OK")
        else:
            return (file, "No encontrado")
    except Exception as e:
        return (file, f"Error: {str(e)}")

def find_rom_files(directory):
    extensions = ['.nes', '.sfc', '.smc', '.gba', '.nds', '.iso', '.bin']
    files = []
    for ext in extensions:
        pattern = os.path.join(directory, f"*{ext}")
        files.extend(glob.glob(pattern))
        pattern_upper = os.path.join(directory, f"*{ext.upper()}")
        files.extend(glob.glob(pattern_upper))
    return files

def cli_mode():
    if len(sys.argv) != 2:
        print("Uso: python main.py <directorio_de_roms>")
        sys.exit(1)
    
    rom_directory = sys.argv[1]
    if not os.path.exists(rom_directory):
        print(f"Error: El directorio '{rom_directory}' no existe")
        sys.exit(1)
    
    files = find_rom_files(rom_directory)
    if not files:
        print("No se encontraron archivos ROM en el directorio")
        sys.exit(0)
    
    print(f"Procesando {len(files)} archivos...")
    
    pool = WorkerPool(8)
    try:
        results = pool.map(process_file, files)
        
        success_count = sum(1 for _, status in results if status == "OK")
        error_count = len(results) - success_count
        
        print(f"\nResultados:")
        print(f"Exitosos: {success_count}")
        print(f"Con errores: {error_count}")
        
        for file, status in results:
            if status != "OK":
                print(f"  {file}: {status}")
    finally:
        pool.close()

def main():
    if len(sys.argv) > 1:
        cli_mode()
    else:
        app = QApplication(sys.argv)
        app.setApplicationName("RetroArch Thumbnails Downloader")
        
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()
