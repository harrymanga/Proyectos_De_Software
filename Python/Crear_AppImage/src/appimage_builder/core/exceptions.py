"""Excepciones personalizadas del proyecto."""

from pathlib import Path


class AppImageBuilderError(Exception):
    """Excepción base para todos los errores de appimage-builder."""

    def __init__(
        self,
        message: str,
        *,
        hint: str | None = None,
        details: str | None = None,
        exit_code: int = 1,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.details = details
        self.exit_code = exit_code

    def __str__(self) -> str:
        parts = [self.message]
        if self.hint:
            parts.append(f"💡 {self.hint}")
        if self.details:
            parts.append(f"📋 {self.details}")
        return "\n".join(parts)


class ConfigurationError(AppImageBuilderError):
    """Error en la configuración del proyecto."""

    def __init__(
        self,
        message: str,
        *,
        config_path: Path | None = None,
        field: str | None = None,
        hint: str | None = None,
    ) -> None:
        details = None
        if config_path:
            details = f"Archivo de configuración: {config_path}"
            if field:
                details += f" (campo: {field})"
        super().__init__(
            message,
            hint=hint or "Verifica el archivo de configuración y los valores proporcionados",
            details=details,
            exit_code=78,
        )


class ProjectDetectionError(AppImageBuilderError):
    """Error detectando el tipo de proyecto."""

    def __init__(
        self,
        message: str,
        *,
        project_path: Path | None = None,
        hint: str | None = None,
    ) -> None:
        details = f"Directorio del proyecto: {project_path}" if project_path else None
        super().__init__(
            message,
            hint=hint or "Asegúrate de estar en el directorio correcto del proyecto",
            details=details,
            exit_code=79,
        )


class BuildError(AppImageBuilderError):
    """Error durante el proceso de build."""

    def __init__(
        self,
        message: str,
        *,
        stage: str | None = None,
        command: str | None = None,
        output: str | None = None,
        hint: str | None = None,
    ) -> None:
        details_parts = []
        if stage:
            details_parts.append(f"Etapa: {stage}")
        if command:
            details_parts.append(f"Comando: {command}")
        if output:
            details_parts.append(f"Salida:\n{output}")
        details = "\n".join(details_parts) if details_parts else None

        super().__init__(
            message,
            hint=hint or "Revisa los logs detallados para más información",
            details=details,
            exit_code=79,
        )


class ValidationError(AppImageBuilderError):
    """Error de validación de AppDir, .desktop, AppStream, etc."""

    def __init__(
        self,
        message: str,
        *,
        validator: str | None = None,
        file_path: Path | None = None,
        errors: list[str] | None = None,
        hint: str | None = None,
    ) -> None:
        details_parts = []
        if validator:
            details_parts.append(f"Validador: {validator}")
        if file_path:
            details_parts.append(f"Archivo: {file_path}")
        if errors:
            details_parts.append("Errores:\n  - " + "\n  - ".join(errors))
        details = "\n".join(details_parts) if details_parts else None

        super().__init__(
            message,
            hint=hint or "Corrige los errores de validación e intenta de nuevo",
            details=details,
            exit_code=80,
        )


class RuntimeError(AppImageBuilderError):
    """Error con runtimes (linuxdeploy, appimagetool, python-standalone)."""

    def __init__(
        self,
        message: str,
        *,
        tool: str | None = None,
        version: str | None = None,
        hint: str | None = None,
    ) -> None:
        details_parts = []
        if tool:
            details_parts.append(f"Herramienta: {tool}")
        if version:
            details_parts.append(f"Versión: {version}")
        details = "\n".join(details_parts) if details_parts else None

        super().__init__(
            message,
            hint=hint or "Verifica la conexión a internet y permisos de escritura en cache",
            details=details,
            exit_code=81,
        )


class DownloadError(RuntimeError):
    """Error descargando archivos."""

    def __init__(
        self,
        message: str,
        *,
        url: str | None = None,
        destination: Path | None = None,
        status_code: int | None = None,
        hint: str | None = None,
    ) -> None:
        details_parts = []
        if url:
            details_parts.append(f"URL: {url}")
        if destination:
            details_parts.append(f"Destino: {destination}")
        if status_code:
            details_parts.append(f"Código HTTP: {status_code}")
        details = "\n".join(details_parts) if details_parts else None

        super().__init__(
            message,
            tool="downloader",
            hint=hint or "Verifica tu conexión a internet y espacio en disco",
            details=details,
        )


class SigningError(AppImageBuilderError):
    """Error firmando el AppImage."""

    def __init__(
        self,
        message: str,
        *,
        key_id: str | None = None,
        hint: str | None = None,
    ) -> None:
        details = f"Key ID: {key_id}" if key_id else None
        super().__init__(
            message,
            hint=hint or "Verifica que GPG esté configurado y la clave exista",
            details=details,
            exit_code=79,
        )


class CancellationError(AppImageBuilderError):
    """Build cancelado por el usuario."""

    def __init__(self, message: str = "Build cancelado por el usuario") -> None:
        super().__init__(
            message,
            hint="El build fue interrumpido. Los archivos temporales se han limpiado.",
            exit_code=130,
        )


class DependencyError(AppImageBuilderError):
    """Dependencia del sistema no encontrada."""

    def __init__(
        self,
        message: str,
        *,
        dependency: str | None = None,
        install_hint: str | None = None,
    ) -> None:
        hint_parts = []
        if install_hint:
            hint_parts.append(install_hint)
        hint_parts.append("Instala la dependencia faltante e intenta de nuevo")
        super().__init__(
            message,
            hint="; ".join(hint_parts),
            details=f"Dependencia: {dependency}" if dependency else None,
            exit_code=127,
        )
