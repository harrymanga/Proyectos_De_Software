import logging
import locale
import os
import sys
from typing import Dict, List, Optional

from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt, QSettings
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QInputDialog,
    QProgressBar,
)

from traductor_pro.application.use_cases import (
    ManageApiKeysUseCase,
    TranslateBatchUseCase,
    TranslateFileUseCase,
)
from traductor_pro.domain.entities import (
    FileTranslationJob,
    FileType,
    GlobalReport,
    TranslationEngine,
    TranslationReport,
)
from traductor_pro.domain.interfaces import ProgressCallback
from traductor_pro.infrastructure.localization.manager import LanguageManager
from traductor_pro.infrastructure.ui.themes import apply_theme

logger = logging.getLogger(__name__)


def _system_language(available) -> str:
    try:
        code = (locale.getdefaultlocale()[0] or "es")[:2].lower()
    except Exception:
        code = "es"
    return code if code in available else "es"

LANG_CODES = {
    "Auto-detectar": None,
    "es - Español": "es",
    "en - Inglés": "en",
    "fr - Francés": "fr",
    "de - Alemán": "de",
    "pt - Portugués": "pt",
    "it - Italiano": "it",
    "ja - Japonés": "ja",
    "ko - Coreano": "ko",
    "zh - Chino": "zh",
    "ru - Ruso": "ru",
}

ENGINE_MAP = {
    "Google Translate": TranslationEngine.GOOGLE,
    "DeepL": TranslationEngine.DEEPL,
    "OpenAI": TranslationEngine.OPENAI,
    "trans-shell (gratis)": TranslationEngine.TRANSSHELL,
}

EXT_TYPE_MAP = {
    ".cfg": FileType.CFG,
    ".lang": FileType.LANG,
    ".txt": FileType.TXT,
    ".properties": FileType.PROPERTIES,
    ".json": FileType.JSON,
}


class QtProgressCallback(ProgressCallback):
    def __init__(self, signals: "WorkerSignals") -> None:
        self._signals = signals

    def on_progress(self, current: int, total: int, message: str) -> None:
        self._signals.progress.emit(current, total, message)

    def on_file_complete(self, report: TranslationReport) -> None:
        self._signals.file_complete.emit(report)

    def on_error(self, error: str) -> None:
        self._signals.error.emit(error)


class WorkerSignals(QObject):
    progress = pyqtSignal(int, int, str)
    file_complete = pyqtSignal(object)
    error = pyqtSignal(str)
    finished = pyqtSignal(object)


class TranslationWorker(QThread):
    def __init__(
        self,
        batch_use_case: TranslateBatchUseCase,
        jobs: List[FileTranslationJob],
    ) -> None:
        super().__init__()
        self.signals = WorkerSignals()
        self._batch_use_case = batch_use_case
        self._jobs = jobs
        self._cancelled = False

    def run(self) -> None:
        callback = QtProgressCallback(self.signals)
        report = self._batch_use_case.execute(self._jobs, callback)
        self.signals.finished.emit(report)

    def cancel(self) -> None:
        self._cancelled = True


class ApiKeyDialog:
    @staticmethod
    def show(parent: QMainWindow, key_use_case: ManageApiKeysUseCase, tr=None) -> None:
        tr = tr or (lambda key, **kw: key)
        services = ["deepl", "openai"]
        items = [f"{s} ({tr('dlg.configured') if key_use_case.get(s) else tr('dlg.unconfigured')})" for s in services]
        item, ok = QInputDialog.getItem(
            parent, tr("msg.api_title"), tr("dlg.api_service"), items, 0, False
        )
        if not ok:
            return
        idx = items.index(item)
        service = services[idx]
        existing = key_use_case.get(service) or ""
        api_key, ok = QInputDialog.getText(
            parent,
            tr("dlg.api_key_title", service=service.upper()),
            tr("dlg.api_key_text", service=service),
            text=existing,
        )
        if ok and api_key.strip():
            key_use_case.set(service, api_key.strip())
            QMessageBox.information(parent, tr("msg.api_title"), tr("msg.api_saved", service=service))
        elif ok and not api_key.strip():
            key_use_case.delete(service)
            QMessageBox.information(parent, tr("msg.api_title"), tr("msg.api_deleted", service=service))


class MainWindowController(QMainWindow):
    def __init__(
        self,
        translate_file_use_case: TranslateFileUseCase,
        batch_use_case: TranslateBatchUseCase,
        key_use_case: ManageApiKeysUseCase,
        cache_port,
        report_generator,
    ) -> None:
        super().__init__()
        self._translate_file = translate_file_use_case
        self._batch = batch_use_case
        self._keys = key_use_case
        self._cache = cache_port
        self._report_gen = report_generator
        self._worker: Optional[TranslationWorker] = None

        self._settings = QSettings("TraductorPro", "TraductorPro")
        self._lang = LanguageManager()
        saved_lang = self._settings.value("ui/language", "")
        self._lang.set_language(
            saved_lang if saved_lang in self._lang.available()
            else _system_language(self._lang.available())
        )
        self._dark = self._settings.value("ui/dark_theme", False, type=bool)

        self._load_ui()
        self._connect_signals()
        self._build_language_menu()
        self._apply_theme(self._dark)
        self.retranslate_ui()

    def _load_ui(self) -> None:
        from PyQt5 import uic

        ui_path = ""
        try:
            from importlib.resources import files
            candidate = files("traductor_pro") / "ui" / "main_window.ui"
            if candidate.is_file():
                ui_path = str(candidate)
        except Exception:
            ui_path = ""
        if not ui_path:
            ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "main_window.ui")
            ui_path = os.path.abspath(ui_path)

        if not os.path.isfile(ui_path):
            alt_path = os.path.join(os.path.dirname(sys.argv[0]), "ui", "main_window.ui")
            alt_path = os.path.abspath(alt_path)
            if os.path.isfile(alt_path):
                ui_path = alt_path
            else:
                raise FileNotFoundError(f"No se encontró main_window.ui (buscado en: {ui_path} y {alt_path})")

        uic.loadUi(ui_path, self)
        self.setWindowTitle("TraductorPro")
        # La lista de archivos y el registro absorben el espacio vertical
        # (0=archivos, 1=salida+motor+opciones, 2=reemplazos, 3=progreso,
        #  4=registro, 5=botones). Sin esto la altura mínima se dispara.
        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(4, 2)

    def _connect_signals(self) -> None:
        self.btnAddFiles.clicked.connect(self._on_add_files)
        self.btnRemoveFile.clicked.connect(self._on_remove_file)
        self.btnClearFiles.clicked.connect(self._on_clear_files)
        self.btnBrowseOutput.clicked.connect(self._on_browse_output)
        self.btnTranslate.clicked.connect(self._on_translate)
        self.btnCancel.clicked.connect(self._on_cancel)
        self.btnAddReplacement.clicked.connect(self._on_add_replacement)
        self.btnRemoveReplacement.clicked.connect(self._on_remove_replacement)
        self.btnClearCache.clicked.connect(self._on_clear_cache)
        self.actionExit.triggered.connect(self.close)
        self.actionApiKeys.triggered.connect(self._on_api_keys)
        self.actionClearCache.triggered.connect(self._on_clear_cache)
        self.actionAbout.triggered.connect(self._on_about)
        self.actionDarkTheme.triggered.connect(self._on_toggle_theme)

    # ---------- Idioma y tema ----------

    def _build_language_menu(self) -> None:
        self.menuLanguage.clear()
        group = QActionGroup(self)
        group.setExclusive(True)
        for code in self._lang.available():
            action = QAction(self._lang.language_name(code), self)
            action.setCheckable(True)
            action.setChecked(code == self._lang.current)
            action.setData(code)
            action.triggered.connect(lambda _checked=False, c=code: self._apply_language(c))
            group.addAction(action)
            self.menuLanguage.addAction(action)

    def _apply_language(self, code: str) -> None:
        if self._lang.set_language(code):
            self._settings.setValue("ui/language", code)
            self._build_language_menu()
            self.retranslate_ui()

    def _on_toggle_theme(self) -> None:
        self._apply_theme(self.actionDarkTheme.isChecked())

    def _apply_theme(self, dark: bool) -> None:
        from PyQt5.QtWidgets import QApplication
        self._dark = dark
        apply_theme(QApplication.instance(), dark)
        self.actionDarkTheme.setChecked(dark)
        self._settings.setValue("ui/dark_theme", dark)

    def retranslate_ui(self) -> None:
        t = self._lang.tr
        self.menuFile.setTitle(t("menu.file"))
        self.menuConfig.setTitle(t("menu.config"))
        self.menuHelp.setTitle(t("menu.help"))
        self.menuLanguage.setTitle(t("menu.language"))
        self.actionExit.setText(t("action.exit"))
        self.actionApiKeys.setText(t("action.api_keys"))
        self.actionClearCache.setText(t("action.clear_cache"))
        self.actionAbout.setText(t("action.about"))
        self.actionDarkTheme.setText(t("action.dark_theme"))
        self.groupFiles.setTitle(t("group.files"))
        self.btnAddFiles.setText(t("btn.add_files"))
        self.btnRemoveFile.setText(t("btn.remove_file"))
        self.btnClearFiles.setText(t("btn.clear_list"))
        self.groupOutput.setTitle(t("group.output"))
        self.btnBrowseOutput.setText(t("btn.browse"))
        self.groupEngine.setTitle(t("group.engine"))
        self.labelEngine.setText(t("lbl.engine"))
        self.labelSourceLang.setText(t("lbl.source_lang"))
        self.labelTargetLang.setText(t("lbl.target_lang"))
        self.groupOptions.setTitle(t("group.options"))
        self.chkProtectPlaceholders.setText(t("chk.protect"))
        self.chkProtectPlaceholders.setToolTip(t("chk.protect.hint"))
        self.chkBackup.setText(t("chk.backup"))
        self.chkCache.setText(t("chk.cache"))
        self.btnClearCache.setText(t("btn.clear_cache"))
        self.groupReplacements.setTitle(t("group.replacements"))
        self.tableReplacements.setHorizontalHeaderLabels([t("col.search"), t("col.replace")])
        self.btnAddReplacement.setText(t("btn.add"))
        self.btnRemoveReplacement.setText(t("btn.delete"))
        self.groupProgress.setTitle(t("group.progress"))
        self.groupLog.setTitle(t("group.log"))
        self.btnTranslate.setText(t("btn.translate"))
        self.btnCancel.setText(t("btn.cancel"))
        self._retranslate_source_combo()
        self.lblStatus.setText(t("status.ready"))

    def _retranslate_source_combo(self) -> None:
        current = self.comboSourceLang.currentData()
        self.comboSourceLang.clear()
        for display, code in LANG_CODES.items():
            text = self._lang.tr("source.auto") if code is None else display
            self.comboSourceLang.addItem(text, code)
        index = self.comboSourceLang.findData(current)
        self.comboSourceLang.setCurrentIndex(index if index >= 0 else 0)

    def _on_add_files(self) -> None:
        t = self._lang.tr
        files, _ = QFileDialog.getOpenFileNames(
            self,
            t("dlg.select_files"),
            "",
            t("dlg.file_filter"),
        )
        for f in files:
            if len(self.listFiles.findItems(f, Qt.MatchExactly)) == 0:
                self.listFiles.addItem(f)

    def _on_remove_file(self) -> None:
        row = self.listFiles.currentRow()
        if row >= 0:
            self.listFiles.takeItem(row)

    def _on_clear_files(self) -> None:
        self.listFiles.clear()

    def _on_browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, self._lang.tr("dlg.out_dir"))
        if directory:
            self.txtOutputDir.setText(directory)

    def _on_translate(self) -> None:
        t = self._lang.tr
        if self.listFiles.count() == 0:
            QMessageBox.warning(self, t("msg.attention"), t("msg.no_files"))
            return

        jobs = self._build_jobs()
        if not jobs:
            QMessageBox.warning(self, t("msg.attention"), t("msg.no_tasks"))
            return

        self._worker = TranslationWorker(self._batch, jobs)
        self._worker.signals.progress.connect(self._on_progress)
        self._worker.signals.file_complete.connect(self._on_file_complete)
        self._worker.signals.error.connect(self._on_error_msg)
        self._worker.signals.finished.connect(self._on_finished)
        self._worker.start()

        self.btnTranslate.setEnabled(False)
        self.btnCancel.setEnabled(True)
        self.lblStatus.setText(t("status.translating"))

    def _on_cancel(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.quit()
            self._worker.wait(3000)
        self._reset_ui()

    def _build_jobs(self) -> List[FileTranslationJob]:
        engine = ENGINE_MAP.get(self.comboEngine.currentText(), TranslationEngine.GOOGLE)
        target_lang = LANG_CODES.get(self.comboTargetLang.currentText(), "en")
        source_lang = self.comboSourceLang.currentData()
        output_dir = self.txtOutputDir.text().strip() or None
        protect = self.chkProtectPlaceholders.isChecked()
        backup = self.chkBackup.isChecked()
        replacements = self._get_replacements()

        jobs: List[FileTranslationJob] = []
        for i in range(self.listFiles.count()):
            path = self.listFiles.item(i).text()
            ext = os.path.splitext(path)[1].lower()
            file_type = EXT_TYPE_MAP.get(ext)
            if file_type is None:
                self._log(self._lang.tr("log.unsupported", path=path))
                continue

            if output_dir:
                base = os.path.basename(path)
                name, _ = os.path.splitext(base)
                out_path = os.path.join(output_dir, f"{name}_{target_lang}{ext}")
            else:
                directory = os.path.dirname(path)
                base = os.path.basename(path)
                name, _ = os.path.splitext(base)
                translations_dir = os.path.join(directory, "translations")
                os.makedirs(translations_dir, exist_ok=True)
                out_path = os.path.join(translations_dir, f"{name}_{target_lang}{ext}")

            jobs.append(FileTranslationJob(
                input_path=path,
                output_path=out_path,
                file_type=file_type,
                target_lang=target_lang,
                engine=engine,
                source_lang=source_lang,
                custom_replacements=replacements,
                protect_placeholders=protect,
                backup_original=backup,
            ))
        return jobs

    def _get_replacements(self) -> Dict[str, str]:
        replacements: Dict[str, str] = {}
        for row in range(self.tableReplacements.rowCount()):
            search_item = self.tableReplacements.item(row, 0)
            replace_item = self.tableReplacements.item(row, 1)
            if search_item and replace_item:
                s = search_item.text().strip()
                r = replace_item.text().strip()
                if s:
                    replacements[s] = r
        return replacements

    def _on_add_replacement(self) -> None:
        self.tableReplacements.insertRow(self.tableReplacements.rowCount())

    def _on_remove_replacement(self) -> None:
        row = self.tableReplacements.currentRow()
        if row >= 0:
            self.tableReplacements.removeRow(row)

    def _on_clear_cache(self) -> None:
        t = self._lang.tr
        self._cache.clear()
        self._log(t("msg.cache_log"))
        QMessageBox.information(self, t("msg.cache_title"), t("msg.cache_cleared"))

    def _on_api_keys(self) -> None:
        ApiKeyDialog.show(self, self._keys, self._lang.tr)

    def _on_about(self) -> None:
        t = self._lang.tr
        QMessageBox.about(
            self,
            t("msg.about_title"),
            "TraductorPro v1.0.0\n\n"
            + t("msg.about_text") +
            "Motores: Google Translate, DeepL, OpenAI\n\n"
            "Arquitectura: Clean Architecture\n"
            "GUI: PyQt5 + Qt Designer",
        )

    def _on_progress(self, current: int, total: int, message: str) -> None:
        if total > 0:
            self.progressBar.setMaximum(total)
            self.progressBar.setValue(current)
        self.lblStatus.setText(message)

    def _on_file_complete(self, report: TranslationReport) -> None:
        t = self._lang.tr
        self._log(t(
            "log.file_line",
            name=os.path.basename(report.input_path),
            ok=report.succeeded,
            cached=report.cached,
            failed=report.failed,
        ))

    def _on_error_msg(self, error: str) -> None:
        self._log(f"{self._lang.tr('msg.error_prefix')}{error}")

    def _on_finished(self, report: GlobalReport) -> None:
        t = self._lang.tr
        self._log(t("msg.done_log"))
        self._log(t("msg.files_done", total=report.total_files))
        self._log(t(
            "msg.stats",
            ok=report.total_succeeded,
            cached=report.total_cached,
            failed=report.total_failed,
        ))

        if report.reports:
            from traductor_pro.infrastructure.system.app_paths import reports_dir
            out_dir = reports_dir()
            self._report_gen.save(report, out_dir)
            self._log(t("log.report_saved", path=out_dir))

        self._reset_ui()
        QMessageBox.information(
            self,
            t("msg.done_title"),
            t(
                "msg.done_text",
                files=report.total_files,
                ok=report.total_succeeded,
                cached=report.total_cached,
                failed=report.total_failed,
            ),
        )

    def _reset_ui(self) -> None:
        self.btnTranslate.setEnabled(True)
        self.btnCancel.setEnabled(False)
        self.progressBar.setValue(0)
        self.lblStatus.setText(self._lang.tr("status.ready"))

    def _log(self, message: str) -> None:
        self.txtLog.append(message)
        logger.info(message)
