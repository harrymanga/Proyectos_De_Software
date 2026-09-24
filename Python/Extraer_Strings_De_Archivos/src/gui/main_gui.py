import os
import sys

from PyQt6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ventana_principal import VentanaPrincipal


def main():
    app = QApplication([])

    window = VentanaPrincipal()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
