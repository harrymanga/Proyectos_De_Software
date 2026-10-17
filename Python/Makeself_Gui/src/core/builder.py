"""Construye argv de makeself con paridad CLI. core/builder.py"""
from __future__ import annotations

from .model import MakeselfProject

_COMPRESSORS = {
    "gzip": "--gzip",
    "pigz": "--pigz",
    "zstd": "--zstd",
    "bzip2": "--bzip2",
    "pbzip2": "--pbzip2",
    "bzip3": "--bzip3",
    "xz": "--xz",
    "lzo": "--lzo",
    "lz4": "--lz4",
    "compress": "--compress",
    "nocomp": "--nocomp",
    "base64": "--base64",
}


def build_argv(project: MakeselfProject, makeself_bin: str = "makeself") -> list[str]:
    o = project.options
    argv: list[str] = [makeself_bin]
    if o.compressor in _COMPRESSORS:
        argv.append(_COMPRESSORS[o.compressor])
    if o.compressor not in ("nocomp", "base64"):
        argv += ["--complevel", str(o.complevel)]
    if o.comp_extra:
        argv += ["--comp-extra", o.comp_extra]
    if o.threads:
        argv += ["--threads", o.threads]
    if o.gpg_encrypt:
        argv.append("--gpg-encrypt")
    if o.ssl_encrypt:
        argv.append("--ssl-encrypt")
    if o.notemp or o.current or project.options.target:
        # --current y --target implican --notemp en makeself
        if o.current:
            argv.append("--current")
        elif project.options.target:
            argv += ["--target", project.options.target]
        else:
            argv.append("--notemp")
    if o.nooverwrite:
        argv.append("--nooverwrite")
    if o.needroot or o.needroot_flag:
        argv.append("--needroot")
    if o.copy:
        argv.append("--copy")
    if o.chown:
        argv.append("--chown")
    if o.tar_format:
        argv += ["--tar-format", o.tar_format]
    if o.tar_extra:
        argv += ["--tar-extra", o.tar_extra]
    if o.untar_extra:
        argv += ["--untar-extra", o.untar_extra]
    if o.follow:
        argv.append("--follow")
    if o.nomd5:
        argv.append("--nomd5")
    if o.nocrc:
        argv.append("--nocrc")
    if o.sha256:
        argv.append("--sha256")
    if o.lsm:
        argv += ["--lsm", o.lsm]
    if o.license:
        argv += ["--license", o.license]
    if o.header:
        argv += ["--header", o.header]
    if o.cleanup:
        argv += ["--cleanup", o.cleanup]
    if o.preextract:
        argv += ["--preextract", o.preextract]
    if o.noprogress:
        argv.append("--noprogress")
    if o.nox11:
        argv.append("--nox11")
    if o.quiet:
        argv.append("--quiet")
    if o.keep_umask:
        argv.append("--keep-umask")
    if o.packaging_date:
        argv += ["--packaging-date", o.packaging_date]
    argv += [project.archive_dir, project.file_name, project.label]
    if project.startup_script:
        argv.append(project.startup_script)
        argv.extend(project.script_args)
    return argv
