# Extraer Strings De Archivos

Herramienta de extracción de strings desde archivos Python, diseñada para generar archivos JSON que facilitan la traducción de mensajes de una aplicación.

## Descripción

Esta aplicación (GUI con PyQt6) permite seleccionar uno o varios archivos Python y extrae automáticamente todos los mensajes de texto (strings) utilizados en:

- Llamadas a `print()`
- Llamadas a `input()` (prompts)
- Asignaciones de strings a variables
- F-strings (cadenas con formato)

Los strings extraídos se guardan en archivos JSON con codificación UTF-8, listos para ser traducidos y posteriormente reutilizados en la aplicación.

## Características

- Extracción robusta usando el módulo `ast` de Python
- Soporte para strings con caracteres Unicode (UTF-8)
- Generación de claves únicas basadas en el número de línea y contexto
- Interfaz gráfica intuitiva con PyQt6
- Método alternativo con expresiones regulares como respaldo

## Estructura del proyecto

```
Extraer_Strings_De_Archivos/
├── gui/
│   ├── frmMain.ui          # Diseño Qt (carga dinámica)
│   ├── main_gui.py         # Entrada GUI completa
│   └── ventana_principal.py # Clase VentanaPrincipal (hilos, i18n, temas)
├── src/
│   ├── __init__.py
│   ├── main_dialogos.py    # Entrada por diálogos sueltos
│   ├── i18n.py             # Cargador (locales en lang/)
│   ├── lang/               # lang_es.json, lang_en.json
│   ├── themes/             # tema.py (claro/oscuro explícitos)
│   └── core/               # extractor.py (regex + AST)
├── tests/
│   ├── __init__.py
│   └── test_main.py     # Tests unitarios
├── requirements.txt
└── README.md
```

## Requisitos

- Python 3.8+
- PyQt6

Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Uso

Ejecución recomendada (crea `.venv` e instala dependencias solo):

```bash
./run.sh        # GUI completa src/gui/main_gui.py (Linux/macOS)
```

En Windows: `run.bat`.

### Interfaz gráfica

```bash
python src/gui/main_gui.py
```

Ventana redimensionable (640×480, mínimo 480×320) con layout real:
lista de archivos, tabla de resultados (Archivo/Clave/Valor), extracción
en segundo plano (sin congelar) y estado en la barra inferior.

- **Arrastrar y soltar** `.py` sobre la lista.
- **Método**: AST (preciso) o Regex (rápido), conmutable.
- **Vista previa**: JSON del archivo seleccionado.
- Carpetas recientes recordadas; idioma y tema persistidos.

Menús: Archivo (Salir), Ver (Tema oscuro), Idioma (Español/English),
Ayuda (Acerca de...). Idioma y tema persistidos (QSettings); grupo
Registro con log de operaciones. Agregar idioma = copiar
`src/i18n_es.py` como `src/i18n_xx.py`.

1. Haz clic en "Seleccionar Archivos" y elige uno o más archivos `.py`.
2. Haz clic en "Seleccionar Carpeta de Guardado" y elige el directorio donde se guardarán los JSON.
3. Los archivos JSON `<nombre>.ES.json` se generarán automáticamente.
4. Haz clic en "SALIR" para cerrar la aplicación.

### Script sin interfaz gráfica (diálogos)

```bash
python src/main_dialogos.py
```

Muestra diálogos para seleccionar archivos y directorio de guardado.

### Usar como módulo

```python
from src.procesamiento import extraer_strings_con_ast, escribir_json

datos = extraer_strings_con_ast('archivo.py')
escribir_json(datos, 'archivo.ES.json')
```

## Formato de salida JSON

```json
{
    "str_print_line_1": "Hola Mundo",
    "str_nombre": "Juan",
    "str_input_line_5": "Ingrese su nombre: "
}
```

### Convenciones de claves

| Prefijo           | Descripción                              |
|-------------------|------------------------------------------|
| `str_print_line_N`| String encontrado en un `print()`        |
| `str_input_line_N`| String encontrado en un `input()`        |
| `str_<variable>`  | String asignado a una variable           |

## Tests

Ejecutar los tests unitarios:

```bash
python -m pytest tests/test_main.py -v
```

O con unittest:

```bash
python -m unittest tests.test_main -v
```
