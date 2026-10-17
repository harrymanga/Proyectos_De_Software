"""Temas claro/oscuro (QSS). El claro es el estilo nativo (sin QSS)."""

DARK_QSS = """
QMainWindow, QWidget { background-color: #2b2b2b; color: #e0e0e0; }
QGroupBox { border: 1px solid #555555; border-radius: 4px; margin-top: 1.2em; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QLineEdit, QTextEdit, QListWidget, QTableWidget, QComboBox {
    background-color: #3a3a3a; color: #e0e0e0;
    border: 1px solid #555555; border-radius: 3px;
    selection-background-color: #4a7ebb;
}
QListWidget::item:selected, QTableWidget::item:selected { background-color: #4a7ebb; color: #ffffff; }
QHeaderView::section { background-color: #3a3a3a; color: #e0e0e0; border: 1px solid #555555; }
QPushButton { background-color: #3d3d3d; color: #e0e0e0; border: 1px solid #5a5a5a; border-radius: 4px; padding: 5px 12px; }
QPushButton:hover { background-color: #4a4a4a; border-color: #4a7ebb; }
QPushButton:pressed { background-color: #4a7ebb; color: #ffffff; }
QPushButton:disabled { background-color: #2b2b2b; color: #777777; }
QProgressBar { background-color: #3a3a3a; border: 1px solid #555555; border-radius: 3px; text-align: center; color: #e0e0e0; }
QProgressBar::chunk { background-color: #4a7ebb; border-radius: 2px; }
QMenuBar { background-color: #2b2b2b; color: #e0e0e0; }
QMenuBar::item:selected { background-color: #4a7ebb; }
QMenu { background-color: #3a3a3a; color: #e0e0e0; border: 1px solid #555555; }
QMenu::item:selected { background-color: #4a7ebb; color: #ffffff; }
QStatusBar { background-color: #2b2b2b; color: #b0b0b0; }
QToolTip { background-color: #3a3a3a; color: #e0e0e0; border: 1px solid #555555; }
QCheckBox { color: #e0e0e0; }
QLabel { color: #e0e0e0; }
QScrollBar:vertical { background-color: #2b2b2b; width: 12px; }
QScrollBar::handle:vertical { background-color: #5a5a5a; border-radius: 6px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background-color: #2b2b2b; height: 12px; }
QScrollBar::handle:horizontal { background-color: #5a5a5a; border-radius: 6px; min-width: 20px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""


def apply_theme(app, dark: bool) -> None:
    """Aplica tema oscuro (QSS) o claro (nativo)."""
    app.setStyleSheet(DARK_QSS if dark else "")
