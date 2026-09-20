# TraductorPro — canónico oficial del grupo Traducciones

Aplicación multiplataforma de traducción de archivos con interfaz gráfica Qt.

## Cobertura (verificada B3)

| Formato | Handler | Placeholders |
|---|---|---|
| `.cfg` | `CfgFileHandler` | `<tag>`, `%s/%d`, `{var}` |
| `.lang` | `LangFileHandler` | `<tag>`, `%s/%d`, `{var}` (Minecraft OK) |
| `.txt` | `TxtFileHandler` | — |
| `.properties` | `PropertiesFileHandler` | `{0}`, `%s`, `${var}`, `[…]` (+ comentarios `#!/!` preservados) |
| `.json` | `JsonFileHandler` | `{0}`, `%s`, `${var}`, `[…]` (anidados y arreglos; números/bool/null intactos) |

Motores: Google (googletrans, sin key), trans-shell (gratis, CLI), DeepL, OpenAI.
Caché MD5, backups, reportes, keyring. Suite: 68 tests (`pytest`).

> Protege escapes `\n`/`\t`/etc. (antes el motor los corrompía: `\n\n` → `\en\`) y preserva CRLF de origen.

> Nota anti-eco: si un motor gratuito devuelve el texto idéntico
> (throttling), se marca como fallo visible en vez de cachear basura.

## Idiomas de la interfaz (es/en + extensible)

- Menú **Idioma**: Español/English conmutables en caliente (se recuerda
  en QSettings; por defecto el `locale` del sistema, fallback español).
- **Agregar un idioma**: copiar `src/traductor_pro/infrastructure/localization/locales/es.py`
  como `xx.py` con `LANGUAGE_CODE`, `LANGUAGE_NAME` y el diccionario
  traducido. Aparece solo en el menú (sin tocar código).

## Tema oscuro

- Menú **Configuración → Tema oscuro** (QSS propio; el claro es el nativo).
  Se recuerda entre sesiones.

## Artefactos (temporales del SO, sin aglomerar)

- Reportes: `<temp>/traductor_pro/reports/` (`report_*.txt` + copia `latest_report.txt`, sin symlinks para Windows).
- Backups: `<temp>/traductor_pro/backups/` (con hash del origen anti-colisiones).
- Caché persistente: `~/.traductor_pro/cache` (se conserva: acelera repeticiones).

## Características

- **Multi-formato**: Traduce archivos `.cfg`, `.lang`, `.txt`, `.properties` y `.json`
- **Multi-motor**: Google Translate, DeepL, OpenAI
- **Multi-idioma**: Selección flexible de idioma origen y destino
- **Protección de placeholders**: Preserva marcadores como `<tag>`, `%s`, `%d`, `{var}`
- **Caché inteligente**: Evita traducciones duplicadas con hash MD5
- **Reemplazos personalizados**: Correcciones post-traducción
- **Reportes detallados**: Log de operaciones por archivo
- **Backups automáticos**: Respaldo de archivos originales
- **Gestión segura de API keys**: Usa keyring del sistema operativo

## Arquitectura

Clean Architecture con 4 capas:

```
Domain → Application → Infrastructure → Presentation
```

- **Domain**: Entidades y puertos (interfaces abstractas)
- **Application**: Casos de uso (orquestación de reglas de negocio)
- **Infrastructure**: Adaptadores (traductores, handlers de archivo, caché, seguridad)
- **Presentation**: GUI Qt (carga .ui de Qt Designer)

## Instalación y uso (recomendado)

```bash
./run.sh        # crea .venv, instala dependencias y ejecuta (Linux/macOS)
```

En Windows: `run.bat`. El lanzador hace todo solo; la instalación manual
siguiente solo es necesaria si trabajas sin él:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"
```

## Uso manual

```bash
python main.py
```

## Desarrollo

### Ejecutar pruebas

```bash
pytest
```

### Linting

```bash
flake8 src/ tests/
mypy src/
black --check src/ tests/
```

### Editar la UI

Abrir `src/traductor_pro/ui/main_window.ui` con Qt Designer (vive dentro del
paquete para que viaje en el AppImage):

```bash
designer src/traductor_pro/ui/main_window.ui
```

## Licencia

MIT
