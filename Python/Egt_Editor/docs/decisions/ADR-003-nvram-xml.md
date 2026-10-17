# ADR-003 — Editor NVRAM-XML (plaintext real)

## Contexto

Carpeta EGT con 799 archivos: 339 `Salted__`, 2 XML en claro (~750KB,
4762 parámetros), 449 blobs grandes sin `Salted__`. El XML contiene
`machine_parameters` + `nvram/area MAIN,GAMES + NVRAMByAttributes` +
`nvram_CRC`. No es XML de raíz única.

## Decisión

Nuevo `src/core/nvram_xml.py`: parse por envoltura `<root>`, edición
`name/address/size/value`, validación size-vs-bytes, serializado que
preserva las 3 secciones y el CRC original. GUI con tab NVRAM
(filtro + tabla editable + guardar con backup + export JSON/CSV).
`detect_kind` ampliado por nombre y `detect_content_kind` por contenido.

## Consecuencias

Ambos XML de referencia comparten CRC pese a valores distintos: el CRC
no cubre valores editables; se preserva y se documenta, no se recalcula
a ciegas. Blobs grandes quedan como `BLOB` solo-lectura (Fase 2).

## Estado

Aceptado e implementado.
