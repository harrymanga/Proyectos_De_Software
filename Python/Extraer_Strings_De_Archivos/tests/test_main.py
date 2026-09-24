#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from core.extractor import (
    leer_archivo,
    procesar_lineas,
    escribir_json,
    extraer_strings_con_ast,
)


class TestLeerArchivo(unittest.TestCase):

    def test_leer_archivo_existente(self):
        contenido = "print('Hola Mundo')\n"
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(contenido)
            ruta = f.name
        try:
            lineas = leer_archivo(ruta)
            self.assertEqual(lineas, [contenido])
        finally:
            os.unlink(ruta)

    def test_leer_archivo_codificacion_utf8(self):
        contenido = "mensaje = 'Hola, 世界'\n"
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(contenido)
            ruta = f.name
        try:
            lineas = leer_archivo(ruta)
            self.assertEqual(lineas, [contenido])
        finally:
            os.unlink(ruta)


class TestProcesarLineas(unittest.TestCase):

    def test_extraer_print_simple(self):
        lineas = ["print('Hola Mundo')\n"]
        datos = procesar_lineas(lineas)
        self.assertIn('str_print_line_1', datos)
        self.assertEqual(datos['str_print_line_1'], "'Hola Mundo'")

    def test_extraer_variable_string(self):
        lineas = ["mensaje = 'Hola Mundo'\n"]
        datos = procesar_lineas(lineas)
        self.assertIn('str_mensaje', datos)
        self.assertEqual(datos['str_mensaje'], "'Hola Mundo'")

    def test_extraer_input(self):
        lineas = ['nombre = input("Ingrese su nombre: ")\n']
        datos = procesar_lineas(lineas)
        self.assertIn('str_nombre', datos)

    def test_extraer_f_string(self):
        lineas = ['print(f"Resultado: {valor}")\n']
        datos = procesar_lineas(lineas)
        self.assertIn('str_print_line_1', datos)

    def test_extraer_multiples_lineas(self):
        lineas = [
            "print('Primer mensaje')\n",
            "nombre = 'Juan'\n",
            "print(f'Hola {nombre}')\n",
        ]
        datos = procesar_lineas(lineas)
        self.assertEqual(len(datos), 3)

    def test_linea_sin_strings(self):
        lineas = ["x = 5\n"]
        datos = procesar_lineas(lineas)
        self.assertEqual(datos, {})


class TestExtraerStringsConAst(unittest.TestCase):

    def test_extraer_print_constante(self):
        contenido = "print('Hola Mundo')\n"
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(contenido)
            ruta = f.name
        try:
            datos = extraer_strings_con_ast(ruta)
            claves_print = [k for k in datos if k.startswith('str_print_')]
            self.assertTrue(len(claves_print) > 0)
            self.assertIn('Hola Mundo', datos.values())
        finally:
            os.unlink(ruta)

    def test_extraer_asignacion_variable(self):
        contenido = "mensaje = 'Hola Mundo'\n"
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(contenido)
            ruta = f.name
        try:
            datos = extraer_strings_con_ast(ruta)
            self.assertIn('str_mensaje', datos)
            self.assertEqual(datos['str_mensaje'], 'Hola Mundo')
        finally:
            os.unlink(ruta)

    def test_extraer_input(self):
        contenido = 'nombre = input("Ingrese nombre: ")\n'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(contenido)
            ruta = f.name
        try:
            datos = extraer_strings_con_ast(ruta)
            claves_input = [k for k in datos if k.startswith('str_input_')]
            self.assertTrue(len(claves_input) > 0)
        finally:
            os.unlink(ruta)

    def test_extraer_f_string(self):
        contenido = 'print(f"Hola {nombre}")\n'
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(contenido)
            ruta = f.name
        try:
            datos = extraer_strings_con_ast(ruta)
            claves_print = [k for k in datos if k.startswith('str_print_')]
            self.assertTrue(len(claves_print) > 0)
        finally:
            os.unlink(ruta)

    def test_extraer_multiples_strings(self):
        contenido = (
            "print('Primer mensaje')\n"
            "nombre = 'Juan'\n"
            "print(f'Hola {nombre}')\n"
            "input('Presione Enter')\n"
        )
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(contenido)
            ruta = f.name
        try:
            datos = extraer_strings_con_ast(ruta)
            claves_print = [k for k in datos if k.startswith('str_print_')]
            claves_input = [k for k in datos if k.startswith('str_input_')]
            self.assertEqual(len(claves_print), 2)
            self.assertEqual(len(claves_input), 1)
            self.assertIn('str_nombre', datos)
        finally:
            os.unlink(ruta)

    def test_archivo_sin_strings(self):
        contenido = "x = 5\ny = x + 3\n"
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False, encoding='utf-8'
        ) as f:
            f.write(contenido)
            ruta = f.name
        try:
            datos = extraer_strings_con_ast(ruta)
            self.assertEqual(datos, {})
        finally:
            os.unlink(ruta)


class TestEscribirJson(unittest.TestCase):

    def test_escritura_json(self):
        datos = {"str_print_line_1": "Hola Mundo", "str_nombre": "Juan"}
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta_json = os.path.join(tmpdir, 'test_output.json')
            escribir_json(datos, ruta_json)

            with open(ruta_json, 'r', encoding='utf-8') as f:
                contenido = json.load(f)

            self.assertEqual(contenido, datos)

    def test_escritura_json_unicode(self):
        datos = {"str_saludo": "Hola, 世界"}
        with tempfile.TemporaryDirectory() as tmpdir:
            ruta_json = os.path.join(tmpdir, 'test_unicode.json')
            escribir_json(datos, ruta_json)

            with open(ruta_json, 'r', encoding='utf-8') as f:
                contenido = json.load(f)

            self.assertEqual(contenido, datos)
            self.assertEqual(contenido['str_saludo'], 'Hola, 世界')


if __name__ == '__main__':
    unittest.main()
