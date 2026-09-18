"""Servicio de plantillas - Generación de archivos estándar AppImage."""

from __future__ import annotations

from pathlib import Path
from string import Template

from appimage_builder.core.constants import BuildType
from appimage_builder.core.models import BuildConfig, ProjectConfig


class TemplateService:
    """Genera archivos template para AppDir (.desktop, AppRun, AppStream, etc.)."""

    # Template para AppRun (bash)
    # NOTA: las variables shell van escapadas como $$VAR (string.Template).
    # $launch_binary es el ejecutable real en usr/bin (para Python es el
    # wrapper con el nombre del proyecto; para nativo/genérico, el entry_point).
    # $gui_dispatch es el bloque `AppRun --gui` (vacío si no hay GUI).
    # Solo $version, $build_type, $launch_binary, $gui_dispatch,
    # $project_env_vars y $user_env_vars son placeholders reales.
    APRUN_TEMPLATE = Template("""#!/bin/bash
# AppRun generado por appimage-builder v$version
# Tipo de proyecto: $build_type
set -e

# Determinar directorio de la AppImage
APPDIR="$$(dirname "$$(readlink -f "$$0")")"
export APPDIR

# Configurar variables de entorno base
export PATH="$$APPDIR/usr/bin:$$PATH"
export LD_LIBRARY_PATH="$$APPDIR/usr/lib:$$APPDIR/usr/lib/x86_64-linux-gnu:$$LD_LIBRARY_PATH"
export XDG_DATA_DIRS="$$APPDIR/usr/share:$$XDG_DATA_DIRS"
export QT_PLUGIN_PATH="$$APPDIR/usr/lib/qt6/plugins:$$QT_PLUGIN_PATH"

# Variables específicas por tipo de proyecto
$project_env_vars

# Variables personalizadas del usuario
$user_env_vars

# Fallback para ejecución sin FUSE (extracción manual)
if [ ! -d "$$APPDIR" ] || [ ! -f "$$APPDIR/usr/bin/$launch_binary" ]; then
    # Probablemente ejecutado desde squashfs-root extraído
    APPDIR="$$(pwd)"
    export APPDIR
fi

$gui_dispatch
# Ejecutar la aplicación
exec "$$APPDIR/usr/bin/$launch_binary" "$$@"
""")

    # Template para .desktop (Freedesktop)
    DESKTOP_TEMPLATE = Template("""[Desktop Entry]
Type=Application
Name=$name
GenericName=$generic_name
Comment=$comment
Exec=$launch_binary
Icon=$icon_name
Terminal=false
Categories=$categories
StartupNotify=true
StartupWMClass=$startup_wm_class
Keywords=$keywords
""")

    # Template para AppStream metainfo
    APPSTREAM_TEMPLATE = Template("""<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>$id</id>
  <name>$name</name>
  <summary>$summary</summary>
  <description>
    <p>$description</p>
  </description>
  <project_license>$license</project_license>
  <url type="homepage">$homepage</url>
  <url type="bugtracker">$bugtracker</url>
  <url type="help">$help</url>
  <url type="donation">$donation</url>
  <launchable type="desktop-id">$desktop_id</launchable>
  <provides>
    <binary>$launch_binary</binary>
  </provides>
  <screenshots>
    $screenshots
  </screenshots>
  <releases>
    <release version="$version" date="$date"/>
  </releases>
  <content_rating type="oars-1.1" />
  <categories>
    $categories_xml
  </categories>
  <keywords>
    $keywords_xml
  </keywords>
</component>
""")

    def __init__(self) -> None:
        pass

    @staticmethod
    def launch_binary(project: ProjectConfig) -> str:
        """Binario real en `usr/bin` que lanza la app.

        - Python: wrapper con el nombre del proyecto (el entry_point es
          `modulo:funcion`, no ejecutable). Lo crea `PythonBuilder`.
        - Nativo/genérico: el entry_point (nombre del binario).
        """
        if project.build_type == BuildType.PYTHON:
            return project.name
        return project.entry_point or project.name

    @staticmethod
    def gui_binary(project: ProjectConfig) -> str | None:
        """Binario lanzador del modo GUI (`AppRun --gui`), o None si no hay."""
        if not project.gui_entry_point.strip():
            return None
        if project.build_type == BuildType.PYTHON:
            return f"{project.name}-gui"
        return project.gui_entry_point.strip()

    def _gui_dispatch_block(self, project: ProjectConfig) -> str:
        """Bloque bash `AppRun --gui` (vacío si el proyecto no define GUI)."""
        target = self.gui_binary(project)
        if target is None:
            return ""
        # OJO: es valor de sustitución (no se reparsea): dólares simples.
        return (
            "# Modo GUI: `<AppImage> --gui` (o `gui`) lanza la interfaz gráfica\n"
            'if [ "$1" = "--gui" ] || [ "$1" == "gui" ]; then\n'
            "    shift\n"
            f'    exec "$APPDIR/usr/bin/{target}" "$@"\n'
            "fi\n"
        )

    def generate_apprun(
        self,
        project: ProjectConfig,
        build: BuildConfig,
        version: str = "0.1.0",
    ) -> str:
        """Genera el contenido del script AppRun."""
        project_env = self._get_project_env_vars(project, build)
        user_env = self._format_user_env_vars(build.env)

        return self.APRUN_TEMPLATE.substitute(
            version=version,
            build_type=project.build_type.value,
            launch_binary=self.launch_binary(project),
            gui_dispatch=self._gui_dispatch_block(project),
            project_env_vars=project_env,
            user_env_vars=user_env,
        )

    def _get_project_env_vars(self, project: ProjectConfig, build: BuildConfig) -> str:
        """Variables de entorno específicas por tipo de proyecto."""
        if project.build_type == BuildType.PYTHON:
            # NOTA: se usa el python3 del sistema anfitrión (sin PYTHONHOME,
            # que rompería su stdlib). El glob cubre cualquier versión 3.x
            # instalada por el builder en usr/lib/python*/site-packages.
            return """# Python runtime (intérprete del sistema anfitrión)
for _pydir in "$APPDIR"/usr/lib/python*/site-packages; do
    [ -d "$_pydir" ] && PYTHONPATH="$_pydir:$PYTHONPATH"
done
unset _pydir
export PYTHONPATH
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
"""
        elif project.build_type == BuildType.NATIVE:
            return """# Native runtime
export LD_LIBRARY_PATH="$APPDIR/usr/lib:$APPDIR/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
"""
        return ""

    def _format_user_env_vars(self, env_vars: dict[str, str]) -> str:
        """Formatea variables de entorno del usuario."""
        if not env_vars:
            return "# No custom environment variables"
        lines = ["# Custom environment variables"]
        for key, value in env_vars.items():
            lines.append(f'export {key}="{value}"')
        return "\n".join(lines)

    def generate_desktop_entry(
        self,
        project: ProjectConfig,
        build: BuildConfig,
    ) -> str:
        """Genera el contenido del archivo .desktop."""
        categories = self._get_categories(project.build_type)
        keywords = self._get_keywords(project)
        launch = self.launch_binary(project)
        if self.gui_binary(project) is not None:
            launch = f"{launch} --gui"

        return self.DESKTOP_TEMPLATE.substitute(
            name=project.name,
            generic_name=project.description or project.name,
            comment=project.description,
            launch_binary=launch,
            icon_name=project.name,
            categories=categories,
            startup_wm_class=project.name.replace("-", "").replace("_", ""),
            keywords=keywords,
        )

    def _get_categories(self, build_type: BuildType) -> str:
        """Categoría .desktop principal según tipo de proyecto (solo una)."""
        if build_type == BuildType.PYTHON:
            return "Development;"
        if build_type == BuildType.NATIVE:
            return "System;"
        return "Utility;"

    def _get_keywords(self, project: ProjectConfig) -> str:
        """Palabras clave para .desktop."""
        keywords = [project.name.lower()]
        if project.build_type == BuildType.PYTHON:
            keywords.append("python")
        elif project.build_type == BuildType.NATIVE:
            keywords.append("native")
        if project.description:
            # Extraer palabras clave de la descripción
            words = project.description.lower().split()
            keywords.extend([w for w in words if len(w) > 3][:5])
        return ";".join(keywords) + ";"

    def generate_appstream(
        self,
        project: ProjectConfig,
        build: BuildConfig,
        screenshots: list[str] | None = None,
    ) -> str:
        """Genera el archivo AppStream metainfo."""
        import datetime

        screenshots_xml = ""
        if screenshots:
            for url in screenshots:
                screenshots_xml += f'    <screenshot type="default">\n      <image>{url}</image>\n    </screenshot>\n'

        categories = self._get_appstream_categories(project.build_type)
        keywords = self._get_appstream_keywords(project)

        return self.APPSTREAM_TEMPLATE.substitute(
            id=f"{project.name}.desktop",
            name=project.name,
            summary=project.description[:100] if project.description else project.name,
            description=project.description or project.name,
            license=project.license,
            homepage=project.homepage or "",
            bugtracker="",
            help="",
            donation="",
            desktop_id=f"{project.name}.desktop",
            launch_binary=self.launch_binary(project),
            screenshots=screenshots_xml,
            version=project.version,
            date=datetime.date.today().isoformat(),
            categories_xml=categories,
            keywords_xml=keywords,
        )

    def _get_appstream_categories(self, build_type: BuildType) -> str:
        """Categorías AppStream."""
        if build_type == BuildType.PYTHON:
            return "    <category>Development</category>\n    <category>Utility</category>"
        elif build_type == BuildType.NATIVE:
            return "    <category>System</category>\n    <category>Utility</category>"
        return "    <category>Utility</category>"

    def _get_appstream_keywords(self, project: ProjectConfig) -> str:
        """Palabras clave AppStream."""
        keywords = [project.name.lower(), "appimage"]
        if project.build_type == BuildType.PYTHON:
            keywords.append("python")
        elif project.build_type == BuildType.NATIVE:
            keywords.append("native")
        return "\n".join(f"    <keyword>{k}</keyword>" for k in keywords)

    def write_apprun(self, project: ProjectConfig, build: BuildConfig, dest: Path) -> None:
        """Escribe AppRun a archivo."""
        content = self.generate_apprun(project, build)
        dest.write_text(content)
        dest.chmod(0o755)

    def write_desktop_entry(self, project: ProjectConfig, build: BuildConfig, dest: Path) -> None:
        """Escribe .desktop a archivo."""
        content = self.generate_desktop_entry(project, build)
        dest.write_text(content)

    def write_appstream(self, project: ProjectConfig, build: BuildConfig, dest: Path) -> None:
        """Escribe AppStream metainfo a archivo."""
        content = self.generate_appstream(project, build)
        dest.write_text(content)

    def get_icon_destinations(self, project: ProjectConfig, appdir: Path) -> list[Path]:
        """Retorna las rutas destino para el icono."""
        if not project.icon:
            return []

        icon_name = f"{project.name}.png"
        destinations = [
            appdir / icon_name,  # Raíz AppDir
        ]

        # hicolor sizes
        for size in [16, 24, 32, 48, 64, 128, 256, 512]:
            dest = (
                appdir
                / "usr"
                / "share"
                / "icons"
                / "hicolor"
                / f"{size}x{size}"
                / "apps"
                / icon_name
            )
            destinations.append(dest)

        return destinations
