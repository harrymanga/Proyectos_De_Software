"""Diálogo de consola de depuración Lua para mods de Factorio.

Provee una interfaz gráfica para:
- Seleccionar un mod de Factorio (carpeta extraída o archivo .zip).
- Iniciar, pausar, reanudar y detener sesiones de depuración.
- Ver la salida de consola (print) del mod en tiempo real.
- Establecer y eliminar puntos de interrupción en archivos Lua.
- Inspeccionar variables globales de Lua.

Diseñado para ser embebido como pestaña en la ventana principal.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.core.debug_adapter import DebugSession
from src.core.i18n import translate
from src.core.logger import get_logger
from src.plugins.factorio_group.factorio_plugin import FactorioPlugin

logger = get_logger(__name__)


class DebugConsoleDialog(QWidget):
    """Widget para depurar mods de Factorio con un adaptador Lua.

    Diseñado para ser embebido como pestaña en la ventana principal.
    """

    session_stopped = Signal(str)

    def __init__(
        self,
        plugin: FactorioPlugin,
        mod_path: Path | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.plugin = plugin
        self.mod_path: Path | None = Path(mod_path) if mod_path else None
        self.session_id: str | None = None
        self.session: DebugSession | None = None
        self._output_lines_shown: int = 0
        self._is_closed: bool = False
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self._safe_refresh_output)
        self._update_timer.setInterval(500)

        self.setMinimumSize(400, 300)
        self._setup_ui()

        # Si se proporcionó un mod, intentar crear la sesión
        if self.mod_path:
            self._select_mod(self.mod_path)

    # ------------------------------------------------------------------
    # Utilidades de seguridad para widgets
    # ------------------------------------------------------------------

    def _widget_alive(self, widget: QWidget) -> bool:
        """Verifica si un widget de Qt todavía existe (no fue destruido)."""
        if self._is_closed:
            return False
        try:
            widget.isVisible()
            return True
        except RuntimeError:
            return False

    def _safe_refresh_output(self) -> None:
        """Wrapper seguro para _refresh_output que captura RuntimeError."""
        if self._is_closed:
            return
        try:
            self._refresh_output()
        except RuntimeError:
            return

    # ------------------------------------------------------------------
    # Configuración de UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # ------------------------------------------------------------------
        # Seleccionar mod
        # ------------------------------------------------------------------
        select_layout = QHBoxLayout()
        select_layout.setContentsMargins(0, 0, 0, 0)
        select_layout.setSpacing(5)

        select_label = QLabel(translate("dialog.debug_console.select_mod"))
        select_label.setMinimumWidth(80)
        select_layout.addWidget(select_label)

        self.mod_path_edit = QLineEdit()
        self.mod_path_edit.setReadOnly(True)
        self.mod_path_edit.setPlaceholderText(
            translate("dialog.debug_console.select_mod_placeholder")
        )
        select_layout.addWidget(self.mod_path_edit)

        self.browse_mod_btn = QPushButton(translate("dialog.create_mod.select_folder"))
        self.browse_mod_btn.setMaximumWidth(100)
        self.browse_mod_btn.clicked.connect(self._browse_mod)
        select_layout.addWidget(self.browse_mod_btn)

        layout.addLayout(select_layout)

        # Barra de información del mod
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-weight: bold; color: #ffaa00;")
        self.info_label.setMaximumHeight(20)
        layout.addWidget(self.info_label)

        # ------------------------------------------------------------------
        # Splitter principal: consola (izquierda) y variables (derecha)
        # ------------------------------------------------------------------
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)

        # --- Panel izquierdo: Consola y controles ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        # Controles de depuración
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(5)

        self.start_btn = QPushButton(translate("dialog.debug_console.start"))
        self.start_btn.clicked.connect(self._start_debug)
        self.start_btn.setEnabled(False)
        self.start_btn.setMaximumWidth(80)
        ctrl_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton(translate("dialog.debug_console.pause"))
        self.pause_btn.clicked.connect(self._pause_debug)
        self.pause_btn.setEnabled(False)
        self.pause_btn.setMaximumWidth(80)
        ctrl_layout.addWidget(self.pause_btn)

        self.resume_btn = QPushButton(translate("dialog.debug_console.resume"))
        self.resume_btn.clicked.connect(self._resume_debug)
        self.resume_btn.setEnabled(False)
        self.resume_btn.setMaximumWidth(80)
        ctrl_layout.addWidget(self.resume_btn)

        self.stop_btn = QPushButton(translate("dialog.debug_console.stop"))
        self.stop_btn.clicked.connect(self._stop_debug)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setMaximumWidth(80)
        ctrl_layout.addWidget(self.stop_btn)

        ctrl_layout.addStretch()
        left_layout.addLayout(ctrl_layout)

        # Área de salida de consola
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet(
            "background-color: #1e1e1e; color: #d4d4d4; font-family: monospace;"
        )
        left_layout.addWidget(self.console_output)

        splitter.addWidget(left_panel)

        # --- Panel derecho: Breakpoints y variables ---
        right_panel = QWidget()
        right_panel.setMinimumWidth(250)
        right_panel.setMaximumWidth(350)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(5)

        # Breakpoints
        bp_label = QLabel(translate("dialog.debug_console.breakpoints"))
        bp_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        right_layout.addWidget(bp_label)

        self.breakpoints_list = QListWidget()
        self.breakpoints_list.setMaximumHeight(120)
        right_layout.addWidget(self.breakpoints_list)

        bp_btn_layout = QHBoxLayout()
        bp_btn_layout.setContentsMargins(0, 0, 0, 0)
        bp_btn_layout.setSpacing(5)

        self.add_bp_btn = QPushButton(
            translate("dialog.debug_console.add_breakpoint")
        )
        self.add_bp_btn.clicked.connect(self._add_breakpoint)
        self.add_bp_btn.setEnabled(False)
        self.add_bp_btn.setMaximumWidth(120)
        bp_btn_layout.addWidget(self.add_bp_btn)

        self.remove_bp_btn = QPushButton(
            translate("dialog.debug_console.remove_breakpoint")
        )
        self.remove_bp_btn.clicked.connect(self._remove_breakpoint)
        self.remove_bp_btn.setEnabled(False)
        self.remove_bp_btn.setMaximumWidth(120)
        bp_btn_layout.addWidget(self.remove_bp_btn)
        right_layout.addLayout(bp_btn_layout)

        # Variables
        var_label = QLabel(translate("dialog.debug_console.variables"))
        var_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        right_layout.addWidget(var_label)

        self.variables_list = QListWidget()
        self.variables_list.setMaximumHeight(150)
        right_layout.addWidget(self.variables_list)

        # Controles para agregar/editar variables
        var_ctrl_layout = QHBoxLayout()
        var_ctrl_layout.setContentsMargins(0, 0, 0, 0)
        var_ctrl_layout.setSpacing(5)

        self.var_name_edit = QLineEdit()
        self.var_name_edit.setPlaceholderText(
            translate("dialog.debug_console.var_name_placeholder")
        )
        self.var_name_edit.setMaximumWidth(120)
        var_ctrl_layout.addWidget(self.var_name_edit)

        self.var_value_edit = QLineEdit()
        self.var_value_edit.setPlaceholderText(
            translate("dialog.debug_console.var_value_placeholder")
        )
        self.var_value_edit.setMaximumWidth(80)
        var_ctrl_layout.addWidget(self.var_value_edit)

        self.add_var_btn = QPushButton(
            translate("dialog.debug_console.add_variable")
        )
        self.add_var_btn.clicked.connect(self._add_variable)
        self.add_var_btn.setEnabled(False)
        self.add_var_btn.setMaximumWidth(80)
        var_ctrl_layout.addWidget(self.add_var_btn)

        self.remove_var_btn = QPushButton(
            translate("dialog.debug_console.remove_variable")
        )
        self.remove_var_btn.clicked.connect(self._remove_variable)
        self.remove_var_btn.setEnabled(False)
        self.remove_var_btn.setMaximumWidth(80)
        var_ctrl_layout.addWidget(self.remove_var_btn)

        right_layout.addLayout(var_ctrl_layout)

        # Seleccionar variable para editar
        self.variables_list.itemSelectionChanged.connect(
            self._on_variable_selected
        )

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([700, 250])

        layout.addWidget(splitter)

    # ------------------------------------------------------------------
    # Selección de mod
    # ------------------------------------------------------------------

    def _browse_mod(self) -> None:
        """Abre un diálogo para seleccionar una carpeta de mod o archivo .zip."""
        if self._is_closed:
            return
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            translate("dialog.debug_console.select_mod_file"),
            str(Path.cwd()),
            "Mods de Factorio (*.zip)",
        )
        if file_path:
            self._select_mod(Path(file_path))

        # Si no se seleccionó un ZIP, intentar seleccionar una carpeta de mod
        if not self.mod_path:
            folder = QFileDialog.getExistingDirectory(
                self,
                translate("dialog.debug_console.select_mod_folder"),
                str(Path.cwd()),
            )
            if folder:
                self._select_mod(Path(folder))

    def _select_mod(self, mod_path: Path) -> None:
        """Selecciona un mod para depurar y crea la sesión si es válida."""
        if self._is_closed:
            return

        self.mod_path = mod_path

        try:
            self.mod_path_edit.setText(str(mod_path))
        except RuntimeError:
            return

        try:
            self.info_label.setText(
                f"{translate('dialog.debug_console.mod')}: {mod_path.name}"
            )
        except RuntimeError:
            return

        # Validar según sea ZIP o carpeta extraída
        is_valid = False
        if mod_path.suffix.lower() == ".zip":
            is_valid = self.plugin.validate(mod_path)
        elif mod_path.is_dir():
            is_valid = self.plugin.validate_folder(mod_path)

        if not is_valid:
            try:
                self.info_label.setStyleSheet(
                    "font-weight: bold; color: #ff6666;"
                )
                self.info_label.setText(
                    f"{translate('dialog.debug_console.mod')}: {mod_path.name} "
                    f"({translate('dialog.debug_console.invalid_mod')})"
                )
            except RuntimeError:
                pass
            try:
                self.start_btn.setEnabled(False)
            except RuntimeError:
                pass
            self.session = None
            self.session_id = None
            self._clear_debug_ui()
            return

        try:
            self.info_label.setStyleSheet(
                "font-weight: bold; color: #aaaa00;"
            )
            self.info_label.setText(
                f"{translate('dialog.debug_console.mod')}: {mod_path.name}"
            )
        except RuntimeError:
            return

        # Crear sesión de depuración
        if self.session_id:
            self.plugin.remove_debug_session(self.session_id)

        self.session_id = f"debug_{mod_path.name}"
        self.session = self.plugin.create_debug_session(
            self.session_id, mod_path
        )

        if self.session is not None:
            try:
                self.start_btn.setEnabled(True)
                self.add_bp_btn.setEnabled(True)
                self.remove_bp_btn.setEnabled(True)
                self.add_var_btn.setEnabled(True)
            except RuntimeError:
                return
            self._refresh_breakpoints_list()
            try:
                self.console_output.append(
                    f"[Debug] Mod seleccionado: {mod_path.name}"
                )
            except RuntimeError:
                pass
        else:
            try:
                self.start_btn.setEnabled(False)
            except RuntimeError:
                pass
            QMessageBox.warning(
                self,
                translate("dialog.debug_console.title"),
                translate("dialog.debug_console.session_error"),
            )

    def _clear_debug_ui(self) -> None:
        """Limpia la interfaz de depuración cuando no hay mod válido."""
        try:
            self.console_output.clear()
        except RuntimeError:
            pass
        try:
            self.variables_list.clear()
        except RuntimeError:
            pass
        try:
            self.breakpoints_list.clear()
        except RuntimeError:
            pass
        for btn in [
            self.start_btn, self.pause_btn, self.resume_btn, self.stop_btn,
            self.add_bp_btn, self.remove_bp_btn, self.add_var_btn,
            self.remove_var_btn,
        ]:
            try:
                btn.setEnabled(False)
            except RuntimeError:
                pass
        self._update_timer.stop()
        try:
            self.var_name_edit.clear()
        except RuntimeError:
            pass
        try:
            self.var_value_edit.clear()
        except RuntimeError:
            pass

    def _refresh_breakpoints_list(self) -> None:
        """Refresca la lista de breakpoints disponibles en los archivos Lua."""
        if self._is_closed:
            return
        try:
            self.breakpoints_list.clear()
        except RuntimeError:
            return

        if not self.mod_path or not self.mod_path.exists():
            return

        lua_files: list[tuple[str, list[int]]] = []

        if self.mod_path.suffix.lower() == ".zip":
            import zipfile as zipfile_mod
            try:
                with zipfile_mod.ZipFile(self.mod_path, "r") as zip_ref:
                    for member in zip_ref.infolist():
                        if member.filename.endswith(".lua") and not member.is_dir():
                            try:
                                content = zip_ref.read(
                                    member.filename
                                ).decode("utf-8", errors="replace")
                                executable_lines = (
                                    self.plugin.debug_adapter.
                                    _get_executable_lines_from_content(content)
                                )
                                if executable_lines:
                                    lua_files.append(
                                        (member.filename, executable_lines)
                                    )
                            except Exception as exc:
                                logger.warning(
                                    "No se pudo leer %s del ZIP: %s",
                                    member.filename, exc,
                                )
                                continue
            except Exception as exc:
                logger.warning("No se pudo leer el ZIP: %s", exc)
        else:
            for lua_file in sorted(self.mod_path.rglob("*.lua")):
                try:
                    content = lua_file.read_text(
                        encoding="utf-8", errors="replace"
                    )
                    executable_lines = (
                        self.plugin.debug_adapter.
                        _get_executable_lines_from_content(content)
                    )
                    if executable_lines:
                        lua_files.append(
                            (str(lua_file), executable_lines)
                        )
                except Exception as exc:
                    logger.warning(
                        "No se pudo leer %s: %s", lua_file, exc
                    )
                    continue

        for file_name, lines in lua_files:
            for line in lines[:10]:
                try:
                    item = QListWidgetItem(f"{file_name}:{line}")
                    item.setData(Qt.ItemDataRole.UserRole, file_name)
                    item.setData(Qt.ItemDataRole.UserRole + 1, line)
                    self.breakpoints_list.addItem(item)
                except RuntimeError:
                    return

    # ------------------------------------------------------------------
    # Operaciones de depuración
    # ------------------------------------------------------------------

    def _refresh_output(self) -> None:
        """Refresca la salida de consola y variables desde la sesión."""
        if self.session is None or self.session_id is None:
            return

        output = self.plugin.get_debug_output(self.session_id)
        new_lines = output[self._output_lines_shown:]
        if new_lines:
            try:
                self.console_output.append("\n".join(new_lines))
                self._output_lines_shown = len(output)
            except RuntimeError:
                return

        variables = self.plugin.get_debug_variables(self.session_id)
        try:
            self.variables_list.clear()
            for name, value in sorted(variables.items()):
                item = QListWidgetItem(f"{name} = {value}")
                self.variables_list.addItem(item)
        except RuntimeError:
            return

    def _start_debug(self) -> None:
        """Inicia la depuración del mod seleccionado."""
        if self._is_closed:
            return
        if self.session is None or self.session_id is None:
            return
        success = self.plugin.start_debug(self.session_id)
        if success:
            try:
                self.start_btn.setEnabled(False)
                self.pause_btn.setEnabled(True)
                self.resume_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self._update_timer.start()
                self.console_output.append(
                    f"[Debug] Sesión iniciada para {self.mod_path.name}"
                )
            except RuntimeError:
                pass
        else:
            QMessageBox.warning(
                self,
                translate("dialog.debug_console.title"),
                translate("dialog.debug_console.start_error"),
            )

    def _pause_debug(self) -> None:
        """Pausa la depuración."""
        if self._is_closed:
            return
        if self.session is None or self.session_id is None:
            return
        success = self.plugin.pause_debug(self.session_id)
        if success:
            try:
                self.pause_btn.setEnabled(False)
                self.resume_btn.setEnabled(True)
                self.console_output.append("[Debug] Pausado")
            except RuntimeError:
                pass

    def _resume_debug(self) -> None:
        """Reanuda la depuración."""
        if self._is_closed:
            return
        if self.session is None or self.session_id is None:
            return
        success = self.plugin.resume_debug(self.session_id)
        if success:
            try:
                self.pause_btn.setEnabled(True)
                self.resume_btn.setEnabled(False)
                self.console_output.append("[Debug] Reanudado")
            except RuntimeError:
                pass

    def _stop_debug(self) -> None:
        """Detiene la depuración."""
        if self._is_closed:
            return
        if self.session is None or self.session_id is None:
            return
        success = self.plugin.stop_debug(self.session_id)
        if success:
            try:
                self.start_btn.setEnabled(True)
                self.pause_btn.setEnabled(False)
                self.resume_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)
                self._update_timer.stop()
                self.console_output.append("[Debug] Detenido")
                self.session_stopped.emit(self.session_id)
            except RuntimeError:
                pass

    def _add_breakpoint(self) -> None:
        """Agrega un punto de interrupción en la línea seleccionada."""
        if self._is_closed:
            return
        try:
            item = self.breakpoints_list.currentItem()
        except RuntimeError:
            return
        if item is None or self.session is None or self.session_id is None:
            return

        file_path = item.data(Qt.ItemDataRole.UserRole)
        line = item.data(Qt.ItemDataRole.UserRole + 1)
        if file_path and line is not None:
            self.plugin.set_debug_breakpoint(
                self.session_id, file_path, int(line)
            )
            try:
                self.console_output.append(
                    f"[Debug] Breakpoint: {item.text()}"
                )
            except RuntimeError:
                pass

    def _remove_breakpoint(self) -> None:
        """Elimina el punto de interrupción seleccionado."""
        if self._is_closed:
            return
        try:
            item = self.breakpoints_list.currentItem()
        except RuntimeError:
            return
        if item is None or self.session is None or self.session_id is None:
            return

        file_path = item.data(Qt.ItemDataRole.UserRole)
        line = item.data(Qt.ItemDataRole.UserRole + 1)
        if file_path and line is not None:
            self.plugin.remove_debug_breakpoint(
                self.session_id, file_path, int(line)
            )
            try:
                self.console_output.append(
                    f"[Debug] Breakpoint eliminado: {item.text()}"
                )
            except RuntimeError:
                pass

    # ------------------------------------------------------------------
    # Gestión de variables
    # ------------------------------------------------------------------

    def _on_variable_selected(self) -> None:
        """Habilita/deshabilita botones según selección de variable."""
        if self._is_closed:
            return
        try:
            has_selection = self.variables_list.currentItem() is not None
            self.remove_var_btn.setEnabled(has_selection)
        except RuntimeError:
            return

    def _add_variable(self) -> None:
        """Agrega o actualiza una variable manualmente en la sesión."""
        if self._is_closed:
            return
        if self.session is None or self.session_id is None:
            return

        try:
            name = self.var_name_edit.text().strip()
            value = self.var_value_edit.text().strip()
        except RuntimeError:
            return

        if not name:
            QMessageBox.warning(
                self,
                translate("dialog.debug_console.title"),
                translate("dialog.debug_console.var_name_required"),
            )
            return

        parsed_value = self._parse_value(value)

        self.plugin.debug_adapter.set_lua_variable(
            self.session_id, name, parsed_value
        )

        try:
            self.console_output.append(
                f"[Debug] Variable agregada: {name} = {parsed_value}"
            )
            self.var_name_edit.clear()
            self.var_value_edit.clear()
        except RuntimeError:
            pass

    def _remove_variable(self) -> None:
        """Elimina la variable seleccionada de la sesión."""
        if self._is_closed:
            return
        try:
            item = self.variables_list.currentItem()
        except RuntimeError:
            return
        if item is None or self.session is None or self.session_id is None:
            return

        try:
            var_text = item.text()
        except RuntimeError:
            return
        var_name = var_text.split(" = ")[0] if " = " in var_text else var_text

        self.plugin.debug_adapter.remove_lua_variable(
            self.session_id, var_name
        )

        try:
            self.console_output.append(
                f"[Debug] Variable eliminada: {var_name}"
            )
        except RuntimeError:
            pass

    def _parse_value(self, value_str: str) -> str | int | float | bool | None:
        """Convierte una cadena de texto al tipo apropiado."""
        if not value_str:
            return None

        if value_str.lower() in ("true", "verdadero"):
            return True
        if value_str.lower() in ("false", "falso"):
            return False

        if value_str.lower() in ("nil", "null", "none", ""):
            return None

        try:
            return int(value_str)
        except ValueError:
            pass

        try:
            return float(value_str)
        except ValueError:
            pass

        return value_str

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Maneja el cierre del widget deteniendo la depuración si está activa."""
        self._is_closed = True
        try:
            self._update_timer.timeout.disconnect()
        except (RuntimeError, TypeError):
            pass
        try:
            self._update_timer.stop()
        except RuntimeError:
            pass
        if self.session is not None and self.session.is_running:
            try:
                self._stop_debug()
            except RuntimeError:
                pass
        super().closeEvent(event)
