#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QListWidget, QPushButton, QCheckBox, 
                             QMessageBox, QProgressBar, QLineEdit, 
                             QFileDialog)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap

class MatchSelectionDialog(QDialog):
    def __init__(self, file_name, matches, parent=None, exact_match=None):
        super().__init__(parent)
        self.file_name = file_name
        self.matches = matches
        self.exact_match = exact_match  # (name, url) si es coincidencia exacta, None si no
        self.selected_url = None
        self.selected_name = None
        self.custom_path = None
        self.setup_ui()
    
    def setup_ui(self):
        if self.exact_match:
            self.setWindowTitle("Coincidencia Exacta")
            self.setMinimumSize(500, 200)
        else:
            self.setWindowTitle("Seleccionar Coincidencia")
            self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Información del archivo
        info_label = QLabel(f"Archivo: {self.file_name}")
        info_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(info_label)
        
        if self.exact_match:
            # Modo de coincidencia exacta
            name, url = self.exact_match
            match_label = QLabel(f"Coincidencia exacta encontrada: {name}")
            match_label.setStyleSheet("color: green; font-weight: bold;")
            layout.addWidget(match_label)
            
            # Vista previa de la coincidencia exacta
            self.preview_label = QLabel()
            self.preview_label.setAlignment(Qt.AlignCenter)
            self.preview_label.setMinimumHeight(150)
            self.preview_label.setStyleSheet("border: 1px solid gray; background: #f0f0f0;")
            layout.addWidget(self.preview_label)
            
            # Cargar vista previa
            self.load_preview(url)
        else:
            # Modo de múltiples coincidencias
            # Label de coincidencias
            matches_label = QLabel(f"Se encontraron {len(self.matches)} coincidencias:")
            layout.addWidget(matches_label)
            
            # Lista de coincidencias
            self.list_widget = QListWidget()
            for name, url in self.matches:
                self.list_widget.addItem(name)
            
            self.list_widget.itemDoubleClicked.connect(self.accept_selection)
            layout.addWidget(self.list_widget)
            
            # Checkbox para vista previa
            self.preview_checkbox = QCheckBox("Mostrar vista previa de imágenes")
            self.preview_checkbox.setChecked(False)
            self.preview_checkbox.stateChanged.connect(self.toggle_preview)
            layout.addWidget(self.preview_checkbox)
            
            # Label para vista previa
            self.preview_label = QLabel()
            self.preview_label.setAlignment(Qt.AlignCenter)
            self.preview_label.setMinimumHeight(150)
            self.preview_label.setStyleSheet("border: 1px solid gray; background: #f0f0f0;")
            layout.addWidget(self.preview_label)
            
            self.preview_label.hide()
            
            # Conectar selección para vista previa
            self.list_widget.currentRowChanged.connect(self.show_preview)
        
        # Selector de ruta de destino
        path_layout = QHBoxLayout()
        path_label = QLabel("Ruta de destino (opcional):")
        path_layout.addWidget(path_label)
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Dejar vacío para usar ruta por defecto")
        path_layout.addWidget(self.path_input)
        
        btn_browse = QPushButton("Examinar")
        btn_browse.clicked.connect(self.browse_directory)
        path_layout.addWidget(btn_browse)
        
        layout.addLayout(path_layout)
        
        # Botones
        button_layout = QHBoxLayout()
        
        if self.exact_match:
            self.btn_select = QPushButton("Descargar")
            self.btn_select.clicked.connect(self.accept_exact_match)
        else:
            self.btn_select = QPushButton("Seleccionar")
            self.btn_select.clicked.connect(self.accept_selection)
        button_layout.addWidget(self.btn_select)
        
        self.btn_skip = QPushButton("Omitir este archivo")
        self.btn_skip.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_skip)
        
        self.btn_cancel = QPushButton("Cancelar todo")
        self.btn_cancel.clicked.connect(self.cancel_all)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def toggle_preview(self, state):
        if state == Qt.Checked:
            self.preview_label.show()
            self.show_preview(self.list_widget.currentRow())
        else:
            self.preview_label.hide()
    
    def show_preview(self, row):
        if row >= 0 and self.preview_checkbox.isChecked():
            import requests
            from io import BytesIO
            from PyQt5.QtGui import QPixmap
            
            try:
                name, url = self.matches[row]
                self.load_preview(url)
            except Exception as e:
                self.preview_label.setText(f"Error: {str(e)}")
    
    def load_preview(self, url):
        import requests
        from PyQt5.QtGui import QPixmap
        
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                
                # Escalar imagen manteniendo aspecto
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.width(), 
                    self.preview_label.height(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
                self.preview_label.setText("")
            else:
                self.preview_label.setText("No se pudo cargar la vista previa")
        except Exception as e:
            self.preview_label.setText(f"Error: {str(e)}")
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Seleccionar directorio de destino")
        if directory:
            self.path_input.setText(directory)
    
    def accept_selection(self):
        row = self.list_widget.currentRow()
        if row >= 0:
            self.selected_name, self.selected_url = self.matches[row]
            # Obtener ruta personalizada si se especificó
            custom_path = self.path_input.text().strip()
            if custom_path:
                self.custom_path = custom_path
            self.accept()
        else:
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona una coincidencia")
    
    def accept_exact_match(self):
        if self.exact_match:
            self.selected_name, self.selected_url = self.exact_match
            # Obtener ruta personalizada si se especificó
            custom_path = self.path_input.text().strip()
            if custom_path:
                self.custom_path = custom_path
            self.accept()
    
    def reject(self):
        self.selected_url = None
        self.selected_name = None
        super().reject()
    
    def cancel_all(self):
        # Usamos un valor especial para indicar cancelación total
        self.selected_url = "CANCEL_ALL"
        super().reject()
    
    def get_selection(self):
        return self.selected_name, self.selected_url, self.custom_path
