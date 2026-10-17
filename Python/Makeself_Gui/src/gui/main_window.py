"""Ventana principal. Ningún otro módulo fuera de src/gui/ contiene widgets."""
from __future__ import annotations

import logging
import os

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.builder import build_argv
from core.deps import check_deps, find_makeself
from core.inspector import parse_info, run_info, suggest_extract_dir
from core.model import MakeselfProject
from core.project import from_info, place_startup, save
from core.space import check_space, fmt_size, uncompressed_kb
from core.templates import TEMPLATES, generate_scaffold
from core.validator import validate
from gui.workers import AppendWorker, CheckWorker, CreateWorker, ExtractWorker, InfoWorker
from i18n import available_languages, translate

log = logging.getLogger("makeself_gui")


class MainWindow(QMainWindow):
    def __init__(self, lang: str = "es", theme: str = "light") -> None:
        super().__init__()
        self.lang = lang
        self.theme_name = theme
        self.last_info: dict = {}
        self.worker = None
        self.setWindowTitle(translate(lang, "app.title"))
        self.resize(780, 620)
        tabs = QTabWidget()
        tabs.addTab(self._create_tab(), translate(lang, "tab.create"))
        tabs.addTab(self._inspect_tab(), translate(lang, "tab.inspect"))
        tabs.addTab(self._templates_tab(), translate(lang, "tab.templates"))
        self.setCentralWidget(tabs)
        self.tabs = tabs
        self.statusBar().showMessage(translate(lang, "status.ready"))
        self.phase_label = QLabel()
        self.statusBar().addPermanentWidget(self.phase_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.hide()
        self.statusBar().addPermanentWidget(self.progress_bar)
        self._build_menus()
        missing = [k for k, v in check_deps().items() if not v and not k.startswith("comp:")]
        if missing:
            QMessageBox.warning(self, translate(lang, "msg.deps_missing"), ", ".join(missing))

    def _t(self, key: str) -> str:
        return translate(self.lang, key)

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu(self._t("menu.file"))
        file_menu.addAction(self._t("menu.open_run"), self._open_run_dialog)
        file_menu.addAction(self._t("menu.quit"), self.close)
        view_menu = self.menuBar().addMenu(self._t("menu.view"))
        view_menu.addAction(self._t("theme.light"), lambda: self._apply_theme("light"))
        view_menu.addAction(self._t("theme.dark"), lambda: self._apply_theme("dark"))
        for code in available_languages():
            view_menu.addAction(f"{self._t('lang.label')}: {code}",
                                lambda c=code: self._apply_lang(c))
        help_menu = self.menuBar().addMenu(self._t("menu.help"))
        help_menu.addAction(self._t("menu.about"),
                            lambda: QMessageBox.about(self, self._t("menu.about"), self._t("about.text")))

    def _apply_theme(self, name: str) -> None:
        self.theme_name = name
        path = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             "..", "themes", f"{name}.qss"))
        try:
            with open(path, encoding="utf-8") as f:
                QApplication.instance().setStyleSheet(f.read())
        except FileNotFoundError:
            log.warning("theme not found: %s", name)

    def _apply_lang(self, code: str) -> None:
        QMessageBox.information(self, self._t("lang.label"), f"{code}: reinicia la app")

    def _browse_row(self, field: QLineEdit, dialog_fn) -> QWidget:
        row = QHBoxLayout()
        row.addWidget(field)
        btn = QPushButton(self._t("btn.browse"))
        btn.clicked.connect(lambda: dialog_fn(field))
        row.addWidget(btn)
        container = QWidget()
        container.setLayout(row)
        return container

    def _create_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.archive_edit = QLineEdit()
        self.output_edit = QLineEdit("/tmp/miapp.run")
        self.label_edit = QLineEdit("Mi App 1.0")
        self.startup_edit = QLineEdit("./setup.sh")
        self.compressor_combo = QComboBox()
        self.compressor_combo.addItems(["gzip", "xz", "zstd", "bzip2", "nocomp", "base64"])
        form.addRow(self._t("field.archive_dir"),
                    self._browse_row(self.archive_edit, self._pick_dir))
        form.addRow(self._t("field.file_name"),
                    self._browse_row(self.output_edit, self._pick_save))
        form.addRow(self._t("field.label"), self.label_edit)
        form.addRow(self._t("field.startup"),
                    self._browse_row(self.startup_edit, self._pick_script))
        form.addRow(self._t("field.compressor"), self.compressor_combo)
        self.temp_edit = QLineEdit(
            QSettings().value("tmpdir", os.environ.get("TMPDIR", "/tmp")))
        form.addRow(self._t("field.temp_dir"),
                    self._browse_row(self.temp_edit, self._pick_dir))
        create_btn = QPushButton(self._t("btn.create"))
        create_btn.clicked.connect(self._start_create)
        form.addRow(create_btn)
        form.addRow(QLabel(self._t("log.title")))
        self.create_log = QTextEdit(readOnly=True)
        form.addRow(self.create_log)
        return widget

    def _inspect_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.run_edit = QLineEdit()
        layout.addWidget(self._browse_row(self.run_edit, self._pick_open))
        buttons = QHBoxLayout()
        info_btn = QPushButton(self._t("btn.info"))
        info_btn.clicked.connect(self._start_info)
        extract_btn = QPushButton(self._t("btn.extract"))
        extract_btn.clicked.connect(self._start_extract)
        check_btn = QPushButton(self._t("btn.check"))
        check_btn.clicked.connect(self._start_check)
        buttons.addWidget(info_btn)
        buttons.addWidget(extract_btn)
        buttons.addWidget(check_btn)
        layout.addLayout(buttons)
        self.inspect_log = QTextEdit(readOnly=True)
        layout.addWidget(self.inspect_log)
        return widget

    def _templates_tab(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.template_combo = QComboBox()
        self.template_combo.addItems(list(TEMPLATES))
        self.scaffold_dest = QLineEdit("/tmp/mijuego")
        self.scaffold_label = QLineEdit("Mi Juego 1.0")
        form.addRow(self._t("field.template"), self.template_combo)
        form.addRow(self._t("field.dest_dir"), self._browse_row(self.scaffold_dest, self._pick_dir))
        form.addRow(self._t("field.label"), self.scaffold_label)
        gen_btn = QPushButton(self._t("btn.generate"))
        gen_btn.clicked.connect(self._generate_scaffold)
        form.addRow(gen_btn)
        self.extra_edit = QLineEdit("/tmp/extra")
        self.append_target = QLineEdit("/tmp/miapp.run")
        form.addRow(self._t("field.extra_dir"), self._browse_row(self.extra_edit, self._pick_dir))
        form.addRow(self._t("field.run_file"), self._browse_row(self.append_target, self._pick_open))
        append_btn = QPushButton(self._t("btn.append"))
        append_btn.clicked.connect(self._start_append)
        form.addRow(append_btn)
        form.addRow(QLabel(self._t("log.title")))
        self.template_log = QTextEdit(readOnly=True)
        form.addRow(self.template_log)
        return widget

    def _on_progress(self, value: int) -> None:
        if value < 0:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(value)
        self.progress_bar.show()

    def _progress_done(self) -> None:
        self.progress_bar.hide()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.phase_label.clear()

    def _on_phase(self, tag: str) -> None:
        self.phase_label.setText(self._t(f"phase.{tag}"))

    def _track(self, worker) -> None:
        self.worker = worker
        worker.progress.connect(self._on_progress)
        worker.phase.connect(self._on_phase)
        worker.failed.connect(self._on_worker_error)

    def _pick_dir(self, field: QLineEdit) -> None:
        selected = QFileDialog.getExistingDirectory(self, self._t("field.archive_dir"))
        if selected:
            field.setText(selected)

    def _pick_save(self, field: QLineEdit) -> None:
        path, _ = QFileDialog.getSaveFileName(self, self._t("field.file_name"), field.text(), "*.run *.sh")
        if path:
            field.setText(path)

    def _pick_open(self, field: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(self, self._t("field.run_file"), "", "*.run *.sh")
        if path:
            field.setText(path)

    def _pick_script(self, field: QLineEdit) -> None:
        start = self.archive_edit.text().strip() or os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(self, self._t("field.startup"), start,
                                              "Shell (*.sh);;Todos (*)")
        if path:
            field.setText(path)

    def _open_run_dialog(self) -> None:
        self._pick_open(self.run_edit)
        self.tabs.setCurrentIndex(1)

    def _form_project(self) -> MakeselfProject:
        project = MakeselfProject(
            archive_dir=self.archive_edit.text().strip(),
            file_name=self.output_edit.text().strip(),
            label=self.label_edit.text().strip(),
            startup_script=self.startup_edit.text().strip(),
        )
        project.options.compressor = self.compressor_combo.currentText()
        return project

    def _start_create(self) -> None:
        project = self._form_project()
        if project.startup_script and os.path.isabs(project.startup_script):
            try:
                outside = os.path.commonpath(
                    [os.path.abspath(project.archive_dir),
                     os.path.abspath(project.startup_script)]
                ) != os.path.abspath(project.archive_dir)
            except ValueError:
                outside = True
            if outside:
                answer = QMessageBox.question(
                    self, self._t("field.startup"),
                    f"{project.startup_script}\n→ {os.path.abspath(project.archive_dir)}/",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
                rel, _ = place_startup(project.archive_dir, project.startup_script)
                project.startup_script = rel
                self.startup_edit.setText(rel)
        errors = validate(project)
        if errors:
            QMessageBox.warning(self, self._t("msg.validation"), "\n".join(errors))
            return
        tmpdir = self.temp_edit.text().strip()
        QSettings().setValue("tmpdir", tmpdir)
        space_warnings = check_space(project.archive_dir, project.file_name, tmpdir)
        if space_warnings:
            answer = QMessageBox.question(
                self, self._t("msg.validation"),
                "\n".join(space_warnings),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
        makeself_bin = find_makeself() or "makeself"
        self.create_log.setText("$ " + " ".join(build_argv(project, makeself_bin)))
        self.statusBar().showMessage(self._t("status.working"))
        self._track(CreateWorker(project, makeself_bin, tmpdir))
        self.worker.finished_ok.connect(self._on_create_done)
        self.worker.start()

    def _on_create_done(self, code: int, out: str, err: str) -> None:
        self._progress_done()
        self.create_log.append((out + err)[-6000:])
        if code == 0:
            needed = uncompressed_kb(out + err)
            if needed:
                self.create_log.append(
                    self._t("msg.install_space").replace(
                        "{size}", fmt_size(needed * 1024)))
        self.statusBar().showMessage(self._t("status.done") if code == 0 else self._t("status.error"))

    def _start_info(self) -> None:
        path = self.run_edit.text().strip()
        if not path:
            return
        self.statusBar().showMessage(self._t("status.working"))
        self._track(InfoWorker(path))
        self.worker.finished_ok.connect(self._on_info_done)
        self.worker.start()

    def _on_info_done(self, text: str) -> None:
        self._progress_done()
        self.last_info = parse_info(text)
        self.inspect_log.setText(text + "\n\n" + str(self.last_info))
        self.statusBar().showMessage(self._t("status.ready"))

    def _start_extract(self) -> None:
        path = self.run_edit.text().strip()
        if not path:
            return
        suggested = suggest_extract_dir(path)
        parent = QFileDialog.getExistingDirectory(
            self, self._t("btn.extract"), os.path.dirname(suggested)
        )
        if parent:
            # Crea la carpeta con el nombre del .sh dentro del directorio elegido.
            name = os.path.basename(suggested)
            dest = os.path.join(parent, name)
            index = 1
            while os.path.exists(dest):
                index += 1
                dest = os.path.join(parent, f"{name}-{index}")
        else:
            dest = suggested
        os.makedirs(dest, exist_ok=True)
        self.statusBar().showMessage(self._t("status.working"))
        self._track(ExtractWorker(path, dest))
        self.worker.finished_ok.connect(lambda c, o, e: self._on_extract_done(path, dest, c, o, e))
        self.worker.start()

    def _on_extract_done(self, path: str, dest: str, code: int, out: str, err: str) -> None:
        self._progress_done()
        self.inspect_log.append(f"\n[extract rc={code}] {(out + err)[-2000:]}")
        info = self.last_info or parse_info(run_info(path))
        project = from_info(info, archive_dir=dest, file_name=path + ".rebuilt.run")
        save(project, os.path.join(dest, "proyecto.msgui.json"))
        self.inspect_log.append(f"{self._t('msg.project_saved')}: proyecto.msgui.json")
        self.statusBar().showMessage(self._t("status.ready"))

    def _start_check(self) -> None:
        path = self.run_edit.text().strip()
        if not path:
            return
        self.statusBar().showMessage(self._t("status.working"))
        self._track(CheckWorker(path))
        self.worker.finished_ok.connect(
            lambda c, o, e: (self._progress_done(),
                             self.inspect_log.append(f"\n[check rc={c}] {(o + e)[-3000:]}"),
                             self.statusBar().showMessage(self._t("status.ready"))))
        self.worker.start()

    def _generate_scaffold(self) -> None:
        try:
            created = generate_scaffold(self.template_combo.currentText(),
                                        self.scaffold_dest.text().strip(),
                                        self.scaffold_label.text().strip())
            self.template_log.setText(f"{self._t('msg.scaffold_done')}: {', '.join(created)}")
            self.archive_edit.setText(self.scaffold_dest.text().strip())
            self.label_edit.setText(self.scaffold_label.text().strip())
            if self.template_combo.currentText() == "mojosetup":
                self.startup_edit.setText("./startmojo.sh")
            else:
                self.startup_edit.setText("./setup.sh")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, self._t("status.error"), str(exc))

    def _start_append(self) -> None:
        extra = self.extra_edit.text().strip()
        target = self.append_target.text().strip()
        if not extra or not target:
            return
        self.statusBar().showMessage(self._t("status.working"))
        self._track(AppendWorker(extra, target, find_makeself() or "makeself"))
        self.worker.finished_ok.connect(self._on_append_done)
        self.worker.start()

    def _on_append_done(self, code: int, out: str, err: str) -> None:
        self._progress_done()
        self.template_log.append(f"\n[append rc={code}] {(out + err)[-3000:]}")
        self.statusBar().showMessage(self._t("status.done") if code == 0 else self._t("status.error"))

    def _on_worker_error(self, message: str) -> None:
        self._progress_done()
        log.error("worker error: %s", message)
        QMessageBox.critical(self, self._t("status.error"), message)
        self.statusBar().showMessage(self._t("status.error"))
