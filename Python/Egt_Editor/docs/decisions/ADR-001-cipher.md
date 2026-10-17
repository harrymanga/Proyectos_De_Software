# ADR-001 — Cipher y compatibilidad de recifrado

## Contexto

Archivos EGT Exciter 3 (`E3_G_GREEN_R8.2_431_PE`, kit `34PE`) con cabecera `Salted__` estilo `openssl enc`. `nvram_impexp.txt` no es contrasena valida para AES-256/128-CBC + pbkdf2/md5 (verificado 14/10/2026).

## Problema

Recifrar con parametros distintos puede dejar la maquina inoperativa.

## Opciones consideradas

1. Solo `openssl` CLI externo — simple pero sin control de salt/KDF.
2. `cryptography` en Python con candidatos ordenados — elegido.
3. Congelar un unico cipher — rechazado hasta Fase 1 de laboratorio.

## Decisión

`CryptoProvider` abstracto con candidatos `aes-256-cbc/pbkdf2`, `aes-128-cbc/pbkdf2`, `aes-256-cbc/md5`, `aes-128-cbc/md5`. Al guardar se reutiliza el `salt` original y el `cipher/kdf` detectado.

## Consecuencias

Round-trip byte-compatible salvo plaintext editado. Fase 1 debe confirmar KDF real contra muestra con contrasena conocida.

## Estado

Aceptado (esqueleto).
