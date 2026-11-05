"""Completador automático para Lua en el editor de mods de Factorio.

Proporciona autocompletado de:
- Funciones de la API de Factorio (data.extractor, game.print, etc.)
- Eventos de Factorio (on_init, on_tick, etc.)
- Tipos de datos (LuaEntity, LuaPlayer, etc.)
- Funciones globales de Lua (print, table.insert, etc.)
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QListWidget, QPlainTextEdit

from src.core.lua_api import get_event_matches, get_prefix_matches, get_type_matches


class LuaCompleter:
    """Completador automático para Lua en el editor de mods de Factorio."""

    def __init__(self, editor: QPlainTextEdit) -> None:
        self.editor = editor
        self.list_widget: QListWidget | None = None
        self._popup_visible = False
        self._enabled = True

    def setEnabled(self, enabled: bool) -> None:
        """Habilita o deshabilita el autocompletado."""
        self._enabled = enabled
        if not enabled:
            self._hide_popup()

    def attach(self, text_edit: QPlainTextEdit) -> None:
        """Conecta el completador a un QPlainTextEdit."""
        self.editor = text_edit
        text_edit.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self) -> None:
        """Maneja cambios de texto para mostrar autocompletado."""
        if not self._enabled:
            return

        cursor = self.editor.textCursor()
        pos = cursor.position()
        text = self.editor.toPlainText()

        # Buscar el inicio de la palabra actual
        start = pos - 1
        while start >= 0 and text[start] and (text[start].isalnum() or text[start] in "_."):
            start -= 1
        start += 1

        current_word = text[start:pos]

        if len(current_word) < 2:
            self._hide_popup()
            return

        # Determinar contexto para completar
        matches = self._get_completions(current_word, text[:pos])

        if not matches:
            self._hide_popup()
            return

        self._show_popup(matches, current_word)

    def _get_completions(self, word: str, context: str) -> list[str]:
        """Obtiene coincidencias de autocompletado."""
        matches = []

        # Determinar contexto para filtrar resultados
        word_lower = word.lower()

        # Búsqueda general en funciones, eventos y tipos
        matches.extend(get_prefix_matches(word_lower, max_results=30))

        # Si parece un evento (empieza con on_), filtrar eventos
        if word_lower.startswith("on_"):
            matches.extend(get_event_matches(word_lower))

        # Si parece un tipo (empieza con mayúscula), filtrar tipos
        if word_lower and word[0].isupper():
            matches.extend(get_type_matches(word_lower))

        # Eliminar duplicados manteniendo orden
        seen = set()
        unique_matches = []
        for m in matches:
            if m.lower() not in seen:
                seen.add(m.lower())
                unique_matches.append(m)

        return unique_matches[:30]

    def _show_popup(self, matches: list[str], current_word: str) -> None:
        """Muestra el popup de autocompletado sin bloquear el editor."""
        if self._popup_visible:
            self._update_popup(matches, current_word)
            return

        from PySide6.QtWidgets import QListWidget

        self.list_widget = QListWidget(self.editor)
        # Configurar para que no robe el foco del editor
        self.list_widget.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.Tool)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setMaximumHeight(200)
        self.list_widget.addItems(matches)
        self.list_widget.itemActivated.connect(self._insert_match)

        # Posicionar debajo del cursor (abajo de la línea de edición)
        cursor_rect = self.editor.cursorRect()
        editor_pos = self.editor.mapToGlobal(cursor_rect.bottomLeft())
        # Ajustar ligeramente para que no se superponga exactamente con el texto
        editor_pos.setY(editor_pos.y() + 2)
        self.list_widget.move(editor_pos)
        self.list_widget.show()
        self._popup_visible = True

    def _update_popup(self, matches: list[str], current_word: str) -> None:
        """Actualiza el popup con nuevas coincidencias."""
        if not self.list_widget:
            return
        self.list_widget.clear()
        self.list_widget.addItems(matches)
        if matches:
            self.list_widget.setCurrentRow(0)

    def _hide_popup(self) -> None:
        """Oculta el popup de autocompletado."""
        if self.list_widget:
            self.list_widget.hide()
            self.list_widget.deleteLater()
            self.list_widget = None
        self._popup_visible = False

    def _insert_match(self, item) -> None:
        """Inserta el match seleccionado en el editor."""
        if not item:
            return

        match_text = item.text()
        cursor = self.editor.textCursor()

        # Buscar el inicio de la palabra actual para reemplazarla
        pos = cursor.position()
        text = self.editor.toPlainText()
        start = pos - 1
        while start >= 0 and text[start] and (text[start].isalnum() or text[start] in "_."):
            start -= 1
        start += 1

        cursor.setPosition(start)
        cursor.setPosition(pos, QTextCursor.KeepAnchor)
        cursor.insertText(match_text)

        self._hide_popup()
        # Devolver el foco al editor para seguir escribiendo
        self.editor.setFocus()
        self.editor.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _on_popup_focus_out(self, event) -> None:
        """Maneja cuando el popup pierde el foco sin cerrarlo inmediatamente."""
        # No cerrar el popup automáticamente para permitir interacción
        # El popup solo se cierra al hacer clic en un elemento o al escribir
