"""Temas claro/oscuro (QSS explícitos).

Ambos son explícitos (no el nativo): en sistemas con modo oscuro global,
el estilo nativo ya se ve oscuro y ambos temas resultaban indistinguibles.
"""

DARK_QSS = """
QMainWindow, QWidget { background-color: #2b2b2b; color: #e0e0e0; }
QLineEdit, QTextEdit, QListWidget, QTableWidget {
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
QMenuBar { background-color: #2b2b2b; color: #e0e0e0; }
QMenuBar::item:selected { background-color: #4a7ebb; }
QMenu { background-color: #3a3a3a; color: #e0e0e0; border: 1px solid #555555; }
QMenu::item:selected { background-color: #4a7ebb; color: #ffffff; }
QStatusBar { background-color: #2b2b2b; color: #b0b0b0; }
QLabel { color: #e0e0e0; }
"""


def apply_theme(app, dark):
    """Aplica tema oscuro o claro (ambos QSS explícitos)."""
    app.setStyleSheet(DARK_QSS if dark else LIGHT_QSS)


LIGHT_QSS = """
QMainWindow, QWidget { background-color: #f0f0f0; color: #1a1a1a; }
QGroupBox { border: 1px solid #a0a0a0; border-radius: 4px; margin-top: 1.2em; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
QLineEdit, QTextEdit, QListWidget, QTableWidget {
    background-color: #ffffff; color: #1a1a1a;
    border: 1px solid #a0a0a0; border-radius: 3px;
    selection-background-color: #2f81f7;
}
QListWidget::item:selected, QTableWidget::item:selected { background-color: #2f81f7; color: #ffffff; }
QHeaderView::section { background-color: #e4e4e4; color: #1a1a1a; border: 1px solid #a0a0a0; }
QPushButton { background-color: #ffffff; color: #1a1a1a; border: 1px solid #8a8a8a; border-radius: 4px; padding: 5px 12px; }
QPushButton:hover { background-color: #e4f0ff; border-color: #2f81f7; }
QPushButton:pressed { background-color: #2f81f7; color: #ffffff; }
QPushButton:disabled { background-color: #f0f0f0; color: #999999; }
QProgressBar { background-color: #ffffff; border: 1px solid #a0a0a0; border-radius: 3px; text-align: center; color: #1a1a1a; }
QProgressBar::chunk { background-color: #2f81f7; border-radius: 2px; }
QMenuBar { background-color: #f0f0f0; color: #1a1a1a; }
QMenuBar::item:selected { background-color: #2f81f7; color: #ffffff; }
QMenu { background-color: #ffffff; color: #1a1a1a; border: 1px solid #a0a0a0; }
QMenu::item:selected { background-color: #2f81f7; color: #ffffff; }
QStatusBar { background-color: #f0f0f0; color: #555555; }
QToolTip { background-color: #ffffdc; color: #1a1a1a; border: 1px solid #a0a0a0; }
QCheckBox { color: #1a1a1a; }
QLabel { color: #1a1a1a; }
QScrollBar:vertical { background-color: #f0f0f0; width: 12px; }
QScrollBar::handle:vertical { background-color: #b0b0b0; border-radius: 6px; min-height: 20px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background-color: #f0f0f0; height: 12px; }
QScrollBar::handle:horizontal { background-color: #b0b0b0; border-radius: 6px; min-width: 20px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
"""
