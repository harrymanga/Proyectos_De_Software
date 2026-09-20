import os
import shutil
from datetime import datetime

from traductor_pro.domain.entities import GlobalReport
from traductor_pro.domain.interfaces import ReportGeneratorPort


class TextReportGenerator(ReportGeneratorPort):
    def generate(self, report: GlobalReport) -> str:
        lines = [
            "===== REPORTE DE TRADUCCIÓN =====",
            f"Fecha: {report.timestamp}",
            "",
        ]
        for r in report.reports:
            lines.extend([
                f"Archivo original: {r.input_path}",
                f"Archivo generado: {r.output_path}",
                f"Motor: {r.engine.value}",
                f"Idioma destino: {r.target_lang}",
                f"Total líneas: {r.total_lines}",
                f"Líneas traducibles: {r.attempted}",
                f"Traducciones exitosas: {r.succeeded}",
                f"Traducciones desde caché: {r.cached}",
                f"Traducciones con fallback: {r.failed}",
            ])
            if r.errors:
                lines.append("Errores:")
                for err in r.errors:
                    lines.append(f"  - {err}")
            lines.append("-----------------------------")
            lines.append("")

        lines.extend([
            "===== RESUMEN GLOBAL =====",
            f"Archivos procesados: {report.total_files}",
            f"Claves traducibles: {report.total_attempted}",
            f"Traducciones exitosas: {report.total_succeeded}",
            f"Desde caché: {report.total_cached}",
            f"Con fallback: {report.total_failed}",
        ])

        return "\n".join(lines)

    def save(self, report: GlobalReport, directory: str) -> None:
        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = os.path.join(directory, f"report_{timestamp}.txt")
        content = self.generate(report)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        latest = os.path.join(directory, "latest_report.txt")
        if os.path.islink(latest) or os.path.isfile(latest):
            os.remove(latest)
        # Copia (no symlink): funciona en Windows sin privilegios.
        shutil.copy2(path, latest)
