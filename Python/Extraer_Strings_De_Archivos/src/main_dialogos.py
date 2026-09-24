import os
import sys
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.extractor import leer_archivo, procesar_lineas, escribir_json, extraer_strings_con_ast


def main():
    app = QApplication([])

    archivos_seleccionados, _ = QFileDialog.getOpenFileNames(
        None, "Seleccionar archivos", "", "Archivos Python (*.py)"
    )

    if not archivos_seleccionados:
        QMessageBox.information(None, "Mensaje", "No se seleccionaron archivos.")
        sys.exit(0)

    directorio_guardado = QFileDialog.getExistingDirectory(
        None, "Seleccionar directorio para guardar archivos JSON", ""
    )

    if not directorio_guardado:
        QMessageBox.information(None, "Mensaje", "No se seleccionó directorio de guardado.")
        sys.exit(0)

    for archivo_seleccionado in archivos_seleccionados:
        nombre_archivo = os.path.splitext(os.path.basename(archivo_seleccionado))[0]

        try:
            datos = extraer_strings_con_ast(archivo_seleccionado)

            if not datos:
                datos = _extraer_strings_regex(archivo_seleccionado)

            nombre_json = os.path.join(directorio_guardado, f'{nombre_archivo}.ES.json')
            escribir_json(datos, nombre_json)

            QMessageBox.information(
                None, "Mensaje", f"Archivo JSON '{nombre_json}' creado exitosamente."
            )
        except Exception as e:
            QMessageBox.critical(
                None, "Error", f"Error al procesar '{archivo_seleccionado}': {e}"
            )

    QMessageBox.information(
        None, "Mensaje", "Proceso completado para todos los archivos seleccionados."
    )
    print("Proceso completado para todos los archivos seleccionados.")


def _extraer_strings_regex(archivo_seleccionado):
    """Método alternativo usando expresiones regulares como respaldo."""
    lineas = leer_archivo(archivo_seleccionado)
    return procesar_lineas(lineas)


if __name__ == "__main__":
    main()
