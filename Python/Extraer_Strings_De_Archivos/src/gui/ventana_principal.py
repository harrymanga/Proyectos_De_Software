#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Ventana principal: selecciona .py, extrae strings (AST) y guarda JSON.

i18n es/en + tema oscuro, con preferencia persistida en QSettings.
"""

import os
import sys

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, QSettings, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6 import QtWidgets, uic

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UI_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frmMain.ui')

sys.path.insert(0, os.path.join(BASE_DIR, 'src'))
from core.extractor import escribir_json, extraer_strings_con_ast, procesar_lineas
from i18n import Idioma
from themes.tema import apply_theme


def get_ui_path():
    if os.path.exists(UI_FILE):
        return UI_FILE
    return None


class ExtractSignals(QObject):
    archivo_listo = pyqtSignal(str, dict)
    error = pyqtSignal(str, str)
    terminado = pyqtSignal()


class ExtractWorker(QRunnable):
    def __init__(self, archivos, directorio, metodo="ast"):
        super().__init__()
        self.archivos = archivos
        self.directorio = directorio
        self.metodo = metodo
        self.signals = ExtractSignals()

    def run(self):
        try:
            for ruta in self.archivos:
                try:
                    if self.metodo == "regex":
                        with open(ruta, 'r', encoding='utf-8') as f:
                            datos = procesar_lineas(f.readlines())
                    else:
                        datos = extraer_strings_con_ast(ruta)
                    base = os.path.splitext(os.path.basename(ruta))[0]
                    salida = os.path.join(self.directorio, base + '.ES.json')
                    escribir_json(datos, salida)
                    self.signals.archivo_listo.emit(ruta, datos)
                except Exception as e:
                    self.signals.error.emit(ruta, str(e))
        finally:
            self.signals.terminado.emit()


class VentanaPrincipal(QtWidgets.QMainWindow):

    def __init__(self):
        super(VentanaPrincipal, self).__init__()

        ui_path = get_ui_path()
        if ui_path:
            uic.loadUi(ui_path, self)

        self.archivos = []
        self.directorio = ""
        self.resultados = {}
        self.hilos = QThreadPool.globalInstance()

        self.ajustes = QSettings("ExtraerStrings", "ExtraerStrings")
        self.idioma = Idioma(self.ajustes.value("ui/idioma", ""))
        self.oscuro = self.ajustes.value("ui/oscuro", False, type=bool)

        self.listArchivos.setAcceptDrops(True)
        self.listArchivos.dragEnterEvent = self._drag_enter
        self.listArchivos.dropEvent = self._drop_files

        self.btnSeleccionarArchivos.clicked.connect(self.seleccionar_archivos)
        self.btnCarpetaGuardado.clicked.connect(self.seleccionar_carpeta_guardado)
        self.btnExtraer.clicked.connect(self.extraer)
        self.btnVistaPrevia.clicked.connect(self.vista_previa)
        self.btnSalir.clicked.connect(self.salir)
        self.actionSalir.triggered.connect(self.salir)
        self.actionTema.triggered.connect(self._alternar_tema)
        self.actionAcerca.triggered.connect(self._acerca_de)

        self._construir_menu_idioma()
        self._aplicar_tema(self.oscuro)
        self.retraducir()

    # ---------- idioma y tema ----------

    def _construir_menu_idioma(self):
        self.menuIdioma.clear()
        grupo = QActionGroup(self)
        grupo.setExclusive(True)
        for codigo in self.idioma.available():
            accion = QAction(self.idioma.name(codigo), self)
            accion.setCheckable(True)
            accion.setChecked(codigo == self.idioma.current)
            accion.setData(codigo)
            accion.triggered.connect(lambda _c=False, cod=codigo: self._aplicar_idioma(cod))
            grupo.addAction(accion)
            self.menuIdioma.addAction(accion)

    def _aplicar_idioma(self, codigo):
        if self.idioma.set(codigo):
            self.ajustes.setValue("ui/idioma", codigo)
            self._construir_menu_idioma()
            self.retraducir()

    def _alternar_tema(self):
        self._aplicar_tema(self.actionTema.isChecked())

    def _aplicar_tema(self, oscuro):
        self.oscuro = oscuro
        apply_theme(QtWidgets.QApplication.instance(), oscuro)
        self.actionTema.setChecked(oscuro)
        self.ajustes.setValue("ui/oscuro", oscuro)

    def retraducir(self):
        t = self.idioma.tr
        self.menuArchivo.setTitle(t("menu.file"))
        self.menuVer.setTitle(t("menu.view"))
        self.menuIdioma.setTitle(t("menu.language"))
        self.menuAyuda.setTitle(t("menu.help"))
        self.actionSalir.setText(t("action.exit"))
        self.actionTema.setText(t("action.dark"))
        self.actionAcerca.setText(t("action.about"))
        self.btnSeleccionarArchivos.setText(t("btn.files"))
        self.btnCarpetaGuardado.setText(t("btn.dest"))
        self.btnExtraer.setText(t("btn.extract"))
        self.btnVistaPrevia.setText(t("btn.preview"))
        self.btnSalir.setText(t("btn.exit"))
        self.groupLog.setTitle(t("group.log"))
        self._cargar_metodos()
        self.tableResultados.setHorizontalHeaderLabels(
            [t("col.file"), t("col.key"), t("col.value")])
        self._actualizar_estado()

    # ---------- flujo ----------

    def _metodo_actual(self):
        return self.comboMetodo.currentData() or "ast"

    def _cargar_metodos(self):
        t = self.idioma.tr
        actual = self._metodo_actual()
        self.comboMetodo.clear()
        self.comboMetodo.addItem(t("method.ast"), "ast")
        self.comboMetodo.addItem(t("method.regex"), "regex")
        self.comboMetodo.setToolTip(t("method.hint"))
        index = self.comboMetodo.findData(actual)
        self.comboMetodo.setCurrentIndex(index if index >= 0 else 0)

    def _drag_enter(self, event):
        from PyQt6.QtCore import Qt
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def _drop_files(self, event):
        nuevos = [u.toLocalFile() for u in event.mimeData().urls()
                  if u.toLocalFile().endswith(".py")]
        if nuevos:
            self.archivos = sorted(set(self.archivos) | set(nuevos))
            self.listArchivos.clear()
            self.listArchivos.addItems([os.path.basename(a) for a in self.archivos])
            self._log(f"+ {len(nuevos)} archivo(s)")
        self._actualizar_estado()

    def _log(self, mensaje):
        self.txtLog.append(mensaje)

    def _actualizar_estado(self):
        t = self.idioma.tr
        self.btnExtraer.setEnabled(bool(self.archivos and self.directorio))
        dest = self.directorio or t("status.no_dest")
        self.statusBar().showMessage(t("status.files", n=len(self.archivos), dest=dest))

    def seleccionar_archivos(self):
        t = self.idioma.tr
        archivos, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self, t("dlg.files"),
            self.ajustes.value("dirs/abrir", ""),
            t("dlg.filter"),
        )
        if archivos:
            self.archivos = archivos
            self.ajustes.setValue("dirs/abrir", os.path.dirname(archivos[0]))
            self.listArchivos.clear()
            self.listArchivos.addItems([os.path.basename(a) for a in archivos])
            self._log(f"+ {len(archivos)} archivo(s)")
        self._actualizar_estado()

    def seleccionar_carpeta_guardado(self):
        t = self.idioma.tr
        directorio = QtWidgets.QFileDialog.getExistingDirectory(
            self, t("dlg.dest"), self.ajustes.value("dirs/guardar", "")
        )
        if directorio:
            self.directorio = directorio
            self.ajustes.setValue("dirs/guardar", directorio)
            self._log(f"> {directorio}")
        self._actualizar_estado()

    def extraer(self):
        t = self.idioma.tr
        if not self.archivos or not self.directorio:
            QtWidgets.QMessageBox.warning(self, t("msg.attention"), t("msg.need_both"))
            return
        self.tableResultados.setRowCount(0)
        self.resultados = {}
        self.btnExtraer.setEnabled(False)
        self.statusBar().showMessage(t("status.extracting"))
        worker = ExtractWorker(list(self.archivos), self.directorio, self._metodo_actual())
        worker.signals.archivo_listo.connect(self._on_archivo)
        worker.signals.error.connect(self._on_error)
        worker.signals.terminado.connect(self._on_terminado)
        self.hilos.start(worker)

    def _on_archivo(self, ruta, datos):
        t = self.idioma.tr
        base = os.path.basename(ruta)
        self.resultados[ruta] = datos
        for clave, valor in datos.items():
            fila = self.tableResultados.rowCount()
            self.tableResultados.insertRow(fila)
            self.tableResultados.setItem(fila, 0, QtWidgets.QTableWidgetItem(base))
            self.tableResultados.setItem(fila, 1, QtWidgets.QTableWidgetItem(clave))
            self.tableResultados.setItem(fila, 2, QtWidgets.QTableWidgetItem(str(valor)))
        self._log(t("status.extracted", base=base, n=len(datos)))
        self.statusBar().showMessage(t("status.extracted", base=base, n=len(datos)))

    def _on_error(self, ruta, mensaje):
        t = self.idioma.tr
        self._log(f"ERROR: {os.path.basename(ruta)}: {mensaje}")
        QtWidgets.QMessageBox.warning(
            self, t("msg.error"), f"{os.path.basename(ruta)}:\n{mensaje}"
        )

    def _on_terminado(self):
        self._actualizar_estado()
        self._log(self.idioma.tr("msg.done"))
        self.statusBar().showMessage(self.idioma.tr("msg.done"))

    def vista_previa(self):
        t = self.idioma.tr
        item = self.listArchivos.currentItem()
        datos = self.resultados.get(self._ruta_de(item.text()), {}) if item else {}
        if not datos:
            QtWidgets.QMessageBox.information(
                self, t("btn.preview"), t("msg.need_both"))
            return
        import json
        dialogo = QtWidgets.QDialog(self)
        dialogo.setWindowTitle(t("preview.title"))
        dialogo.resize(480, 360)
        texto = QtWidgets.QTextEdit(dialogo)
        texto.setReadOnly(True)
        texto.setPlainText(json.dumps(datos, ensure_ascii=False, indent=2))
        layout = QtWidgets.QVBoxLayout(dialogo)
        layout.addWidget(texto)
        dialogo.exec()

    def _ruta_de(self, base):
        for ruta in self.archivos:
            if os.path.basename(ruta) == base:
                return ruta
        return base

    def _acerca_de(self):
        t = self.idioma.tr
        QtWidgets.QMessageBox.about(
            self, t("msg.about_title"),
            "Extraer Strings v1.0.0\n\n" + t("msg.about_text"),
        )

    def salir(self):
        self.close()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = VentanaPrincipal()
    window.show()
    sys.exit(app.exec())
