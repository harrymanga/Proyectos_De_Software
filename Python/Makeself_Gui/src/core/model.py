"""Modelo de datos del proyecto Makeself GUI."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MakeselfOptions:
    compressor: str = "gzip"  # gzip|bzip2|bzip3|pbzip2|xz|zstd|lzo|lz4|pigz|compress|nocomp|base64
    complevel: int = 9
    comp_extra: str = ""
    threads: str = ""
    # extraccion
    notemp: bool = False
    current: bool = False
    target: str = ""
    nooverwrite: bool = False
    needroot: bool = False
    copy: bool = False
    # integridad / meta
    nomd5: bool = False
    nocrc: bool = False
    sha256: bool = True
    lsm: str = ""
    license: str = ""
    header: str = ""
    cleanup: str = ""
    preextract: str = ""
    # tar
    tar_format: str = ""
    tar_extra: str = ""
    untar_extra: str = ""
    follow: bool = False
    # cifrado
    gpg_encrypt: bool = False
    ssl_encrypt: bool = False
    # misc
    noprogress: bool = False
    quiet: bool = False
    nox11: bool = True
    keep_umask: bool = False
    needroot_flag: bool = False
    chown: bool = False
    packaging_date: str = ""


@dataclass
class MakeselfProject:
    archive_dir: str = ""
    file_name: str = ""
    label: str = ""
    startup_script: str = ""
    script_args: list[str] = field(default_factory=list)
    options: MakeselfOptions = field(default_factory=MakeselfOptions)
    reconstructed: bool = False  # True si viene de --info + extraccion
