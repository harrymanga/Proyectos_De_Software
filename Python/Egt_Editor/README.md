# Editor EGT Exciter 3

Editor para archivos de configuración de tragamonedas EGT (Exciter 3/4):
`Salted__` (`34PE_*`, `FROM*`, `E3_G_*CONFIG/SETTINGS`), NVRAM-XML en claro
(`E3_C_GOLD-HD~*`, 4762 parámetros) y blobs `NVRAM_DATA` solo-lectura.

## Requisitos

* Linux con `python3-venv` (ver `system-packages.txt` si falla).
* Sin instalación manual: `run.sh` crea `.venv` e instala todo.

## Uso paso a paso (comandos copiables)

```bash
cd egt-editor
chmod +x run.sh
./run.sh
# Abrir EGT/XML → auto-detecta por contenido
# XML: filtra (nombre/address), edita columna value, Guardar XML (crea .bak, CRC preservado), Exportar CSV/JSON
# Salted__: introduce contraseña → Descifrar → edita hex → Guardar recifrado
```

Tests:

```bash
.venv/bin/python -m pytest tests/ -v
```

## Qué esperar

* Apertura auto-detecta por contenido: `NVRAM_XML` / `CRYPT_SALTED` / `BLOB`.
* XML: tabla de 4762 parámetros con filtro, solo `value` editable, validación size-vs-bytes antes de guardar.
* Descifrado `Salted__` prueba `aes-256/128-cbc` + `pbkdf2/md5` en hilo, muestra cipher en statusbar.
* Guardar reutiliza `salt` original (crypto) o preserva `nvram_CRC` (XML) + backup `.YYYYMMDD-HHMMSS.bak`.
* Exportar: JSON/CSV de parámetros o JSON con `plaintext_hex/b64`.

## Si algo falla

* `bad decrypt` → contraseña/cipher incorrectos. El laboratorio Fase 1 aún debe confirmar KDF real (ver `docs/decisions/ADR-001-cipher.md`).
* `no-salted-header` → archivo no es EGT cifrado.
* `hex-invalido` → revisa edición hex.
* Falta `libGL` en Qt → instala paquete del sistema indicado por el error.

## Punto de entrada documentado

`src/main.py` → `MainWindow` en `src/gui/main_window.py`. Núcleo sin GUI en `src/core/`.

## Estructura

```text
src/main.py src/i18n.py src/lang/lang_es.json src/lang/lang_en.json
src/core/crypto_provider.py src/core/egt_format.py src/core/nvram_xml.py
src/core/backup_manager.py src/core/exporter.py
src/gui/main_window.py src/gui/workers.py src/gui/themes.py
tests/test_roundtrip.py tests/test_nvram_xml.py docs/decisions/
```

Idiomas: español por defecto con fallback (§57). Tema claro/oscuro explícito.
