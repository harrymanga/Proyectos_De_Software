"""Ventana principal. Unica capa con GUI (§54). Tabs: crypto + NVRAM-XML."""
from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QPlainTextEdit, QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget,
)
from PySide6.QtCore import QSettings, Qt

from i18n import I18n
from core import crypto_provider as crypto
from core.egt_format import EgtFile, detect_content_kind, detect_kind
from core.backup_manager import make_backup
from core.exporter import export_json, export_nvram_csv, export_nvram_json, import_plaintext_hex
from core.nvram_xml import NvramDocument, parse_nvram_xml, serialize
from gui import themes
from gui.workers import Worker

log = logging.getLogger("egt-editor")
COLS = ("name", "address", "size", "value", "section")


class MainWindow(QMainWindow):
    def __init__(self, i18n: I18n) -> None:
        super().__init__()
        self.i18n = i18n
        self.eg: EgtFile | None = None
        self.doc: NvramDocument | None = None
        self._worker: Worker | None = None
        self._loading_table = False
        self.settings = QSettings("EGT-Tools", "EGTEditor")
        self._build()
        self.apply_theme(self.settings.value("theme", "light"))
        if self.i18n.language() != (self.settings.value("lang", "es")):
            self.set_lang(self.settings.value("lang", "es"))

    # ---- UI ----
    def _build(self) -> None:
        self.setMinimumSize(1000, 650)
        central = QWidget()
        lay = QVBoxLayout(central)

        top = QHBoxLayout()
        self.lbl_file = QLabel()
        self.lbl_kind = QLabel()
        self.lbl_size = QLabel()
        self.lbl_status = QLabel()
        for w in (self.lbl_file, self.lbl_kind, self.lbl_size, self.lbl_status):
            top.addWidget(w)
        lay.addLayout(top)

        self.tabs = QTabWidget()
        lay.addWidget(self.tabs, 1)

        # Tab crypto (esqueleto previo)
        crypto_w = QWidget()
        clay = QVBoxLayout(crypto_w)
        pwrow = QHBoxLayout()
        self.lbl_pw = QLabel()
        self.inp_pw = QLineEdit()
        self.inp_pw.setEchoMode(QLineEdit.Password)
        self.btn_decrypt = QPushButton()
        self.btn_decrypt.clicked.connect(self.on_decrypt)
        pwrow.addWidget(self.lbl_pw)
        pwrow.addWidget(self.inp_pw, 1)
        pwrow.addWidget(self.btn_decrypt)
        clay.addLayout(pwrow)
        split = QSplitter(Qt.Vertical)
        self.hex_view = QPlainTextEdit()
        self.hex_view.setPlaceholderText("hex …")
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["key", "value"])
        split.addWidget(self.hex_view)
        split.addWidget(self.table)
        clay.addWidget(split, 1)
        self.tabs.addTab(crypto_w, "crypto")

        # Tab NVRAM
        nv_w = QWidget()
        nlay = QVBoxLayout(nv_w)
        frow = QHBoxLayout()
        self.lbl_filter = QLabel()
        self.inp_filter = QLineEdit()
        self.inp_filter.setPlaceholderText("NVRAM_… / address / value")
        self.inp_filter.textChanged.connect(self._apply_filter)
        self.lbl_count = QLabel()
        frow.addWidget(self.lbl_filter)
        frow.addWidget(self.inp_filter, 1)
        frow.addWidget(self.lbl_count)
        nlay.addLayout(frow)
        self.nv_table = QTableWidget(0, 5)
        self.nv_table.cellChanged.connect(self._on_cell_edited)
        nlay.addWidget(self.nv_table, 1)
        self.tabs.addTab(nv_w, "nvram")

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(500)
        lay.addWidget(self.log_view)

        self.setCentralWidget(central)
        self._menus()
        self.statusBar().showMessage("")
        self._retranslate()

    def _menus(self) -> None:
        m = self.menuBar()
        fm = m.addMenu(self.i18n.t("menu.file"))
        fm.addAction(self.i18n.t("act.open_any"), self.on_open)
        fm.addAction(self.i18n.t("act.save"), self.on_save)
        fm.addAction(self.i18n.t("act.save_xml"), self.on_save_xml)
        fm.addAction(self.i18n.t("act.save_as"), self.on_save_as)
        fm.addAction(self.i18n.t("act.export"), self.on_export)
        fm.addAction(self.i18n.t("act.export_csv"), self.on_export_csv)
        fm.addAction(self.i18n.t("act.import"), self.on_import)
        fm.addSeparator()
        fm.addAction(self.i18n.t("act.close"), self.close)

        vm = m.addMenu(self.i18n.t("menu.view"))
        vm.addAction(self.i18n.t("theme.light"), lambda: self.apply_theme("light"))
        vm.addAction(self.i18n.t("theme.dark"), lambda: self.apply_theme("dark"))

        lm = m.addMenu(self.i18n.t("menu.lang"))
        lm.addAction("Español", lambda: self.set_lang("es"))
        lm.addAction("English", lambda: self.set_lang("en"))

        hm = m.addMenu(self.i18n.t("menu.help"))
        hm.addAction(self.i18n.t("act.about"), self.on_about)

    def _retranslate(self) -> None:
        t = self.i18n
        self.setWindowTitle(t.t("app.title"))
        if hasattr(self, "lbl_file"):
            self.lbl_pw.setText(t.t("lbl.password"))
            self.btn_decrypt.setText(t.t("btn.decrypt"))
            self.lbl_filter.setText(t.t("lbl.filter"))
            self.tabs.setTabText(0, t.t("tab.crypto"))
            self.tabs.setTabText(1, t.t("tab.nvram"))
            self.nv_table.setHorizontalHeaderLabels([t.t(f"col.{c}") for c in COLS])
            self._refresh_info()
            self.menuBar().clear()
            self._menus()

    # ---- Estado ----
    def _refresh_info(self) -> None:
        t = self.i18n
        if self.doc is not None:
            self.lbl_file.setText(f"{t.t('lbl.file')}: {self.doc.path.name}")
            self.lbl_kind.setText(f"{t.t('lbl.kind')}: NVRAM_XML ({self.doc.game_version})")
            self.lbl_size.setText(f"{t.t('lbl.size')}: {len(self.doc.parameters)} params")
            self.lbl_status.setText(f"{t.t('lbl.status')}: {t.t('st.xml')}")
            return
        if not self.eg:
            for w, k in ((self.lbl_file, "lbl.file"), (self.lbl_kind, "lbl.kind"),
                         (self.lbl_size, "lbl.size"), (self.lbl_status, "lbl.status")):
                w.setText(f"{t.t(k)}: —")
            return
        st = t.t("st.decrypted") if self.eg.decrypted else t.t("st.encrypted")
        if self.eg.kind in ("NVRAM_DATA", "SS_BIN", "UNKNOWN"):
            st = t.t("st.blob")
        self.lbl_file.setText(f"{t.t('lbl.file')}: {self.eg.path.name}")
        self.lbl_kind.setText(f"{t.t('lbl.kind')}: {self.eg.kind}")
        self.lbl_size.setText(f"{t.t('lbl.size')}: {len(self.eg.encrypted)} B")
        self.lbl_status.setText(f"{t.t('lbl.status')}: {st}")

    def _log(self, msg: str) -> None:
        self.log_view.appendPlainText(msg)
        log.info(msg)

    # ---- Apertura: detecta por contenido ----
    def on_open(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, self.i18n.t("act.open_any"))
        if not path:
            return
        p = Path(path)
        data = p.read_bytes()
        kind = detect_content_kind(data)
        if kind == "NVRAM_XML":
            self._run(lambda: parse_nvram_xml(p), self._xml_ok, self._fail)
        elif kind == "CRYPT_SALTED":
            self.doc = None
            self.eg = EgtFile(p, detect_kind(p.name), data)
            self.hex_view.setPlainText(data[16:64].hex(" "))
            self._refresh_info()
            self.tabs.setCurrentIndex(0)
            self.statusBar().showMessage(path)
            self._log(f"open: {path} kind={self.eg.kind} size={len(data)} salted")
        else:
            self.doc = None
            self.eg = EgtFile(p, detect_kind(p.name), data)
            self.hex_view.setPlainText(data[:64].hex(" "))
            self._refresh_info()
            self.tabs.setCurrentIndex(0)
            self._log(f"open: {path} kind={self.eg.kind} size={len(data)} blob-sin-parser")

    def _xml_ok(self, doc: object) -> None:
        assert isinstance(doc, NvramDocument)
        self.doc = doc
        self.eg = None
        self._fill_nv_table()
        self._refresh_info()
        self.tabs.setCurrentIndex(1)
        self._log(f"open-xml: {doc.path.name} {len(doc.parameters)} {self.i18n.t('msg.xml_loaded')}")
        self.statusBar().showMessage(f"{doc.game_version} CRC={doc.crc}")

    def _fill_nv_table(self) -> None:
        assert self.doc is not None
        t = self.nv_table
        self._loading_table = True
        t.setSortingEnabled(False)
        t.setRowCount(len(self.doc.parameters))
        for i, p in enumerate(self.doc.parameters):
            for j, val in enumerate((p.name, p.address, p.size, p.value, p.section)):
                item = QTableWidgetItem(val)
                if j != 3:  # solo value editable
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                t.setItem(i, j, item)
        t.resizeColumnsToContents()
        self._loading_table = False
        self._apply_filter()

    def _apply_filter(self) -> None:
        if self.doc is None:
            return
        q = self.inp_filter.text().strip().lower()
        shown = 0
        for i in range(self.nv_table.rowCount()):
            if not q:
                self.nv_table.setRowHidden(i, False)
                shown += 1
                continue
            hay = " ".join(self.nv_table.item(i, j).text() for j in range(5)).lower()
            vis = q in hay
            self.nv_table.setRowHidden(i, not vis)
            if vis:
                shown += 1
        self.lbl_count.setText(f"{self.i18n.t('lbl.count')}: {shown}/{self.nv_table.rowCount()}")

    def _on_cell_edited(self, row: int, col: int) -> None:
        if self._loading_table or self.doc is None or col != 3:
            return
        name = self.nv_table.item(row, 0).text()
        new_val = self.nv_table.item(row, 3).text()
        self.doc.set_value(name, new_val)
        self.statusBar().showMessage(f"{name} <- {new_val[:40]}")

    # ---- Crypto (sin cambios) ----
    def on_decrypt(self) -> None:
        if not self.eg:
            return
        pw = self.inp_pw.text()
        if not pw:
            QMessageBox.information(self, self.i18n.t("app.title"), self.i18n.t("msg.need_password"))
            return
        data = self.eg.encrypted
        self._run(lambda: crypto.try_decrypt(pw, data), self._decrypt_ok, self._fail)

    def _decrypt_ok(self, res: object) -> None:
        pt, cipher, kdf = res  # type: ignore[misc]
        assert self.eg is not None
        self.eg.plaintext = pt
        self.eg.cipher = cipher
        self.eg.kdf = kdf
        self.hex_view.setPlainText(pt.hex(" "))
        self._show_analysis()
        self._refresh_info()
        self._log(f"{self.i18n.t('msg.decrypt_ok')} {cipher}/{kdf} plain={len(pt)}")
        self.statusBar().showMessage(f"{cipher}/{kdf}")
        self.inp_pw.clear()

    def _show_analysis(self) -> None:
        assert self.eg is not None
        info = self.eg.analyze()
        self.table.setRowCount(len(info))
        for i, (k, v) in enumerate(info.items()):
            self.table.setItem(i, 0, QTableWidgetItem(str(k)))
            self.table.setItem(i, 1, QTableWidgetItem(str(v)))

    def _fail(self, err: str) -> None:
        self._log(f"error: {err[:300]}")
        QMessageBox.warning(self, self.i18n.t("st.error"), self.i18n.t("msg.decrypt_fail"))

    def _run(self, fn, ok, fail) -> None:
        self._worker = Worker(fn)
        self._worker.done.connect(ok)
        self._worker.failed.connect(fail)
        self._worker.start()

    def _collect_hex(self) -> bytes | None:
        try:
            return bytes.fromhex("".join(self.hex_view.toPlainText().split()))
        except ValueError:
            QMessageBox.warning(self, self.i18n.t("st.error"), "hex-invalido")
            return None

    def on_save(self) -> None:
        if not self.eg or not self.eg.decrypted:
            return
        pt = self._collect_hex()
        if pt is None:
            return
        pw = self.inp_pw.text()
        if not pw:
            QMessageBox.information(self, self.i18n.t("app.title"), self.i18n.t("msg.need_password"))
            return
        bak = make_backup(self.eg.path)
        salt = self.eg.encrypted[8:16]
        out = crypto.encrypt_with(pw, pt, self.eg.cipher or "aes-256-cbc", self.eg.kdf or "pbkdf2", salt)
        self.eg.path.write_bytes(out)
        self.eg.encrypted = out
        self.eg.plaintext = pt
        self.inp_pw.clear()
        self._refresh_info()
        self._log(f"{self.i18n.t('msg.saved')} backup={bak.name}")

    def on_save_xml(self) -> None:
        if self.doc is None:
            return
        errors = self.doc.validate()
        if errors:
            self._log(f"{self.i18n.t('msg.validate_fail')} {len(errors)}")
            for e in errors[:10]:
                self._log(f"  {e}")
            box = QMessageBox.question(self, self.i18n.t("app.title"),
                                       f"{self.i18n.t('msg.validate_fail')} {len(errors)}. ¿Guardar igual?")
            if box != QMessageBox.Yes:
                return
        else:
            self._log(self.i18n.t("msg.validate_ok"))
        bak = make_backup(self.doc.path)
        self.doc.path.write_text(serialize(self.doc), encoding="utf-8")
        self._log(f"{self.i18n.t('msg.xml_saved')} backup={bak.name}")
        self.statusBar().showMessage(str(bak.name))

    def on_save_as(self) -> None:
        if self.doc is not None:
            dest, _ = QFileDialog.getSaveFileName(self, self.i18n.t("act.save_as"), self.doc.path.name)
            if dest:
                Path(dest).write_text(serialize(self.doc), encoding="utf-8")
                self._log(f"save-as: {dest}")
            return
        if not self.eg:
            return
        dest, _ = QFileDialog.getSaveFileName(self, self.i18n.t("act.save_as"), self.eg.path.name)
        if dest:
            Path(dest).write_bytes(self.eg.encrypted)
            self._log(f"save-as: {dest}")

    def on_export(self) -> None:
        if self.doc is not None:
            dest, _ = QFileDialog.getSaveFileName(self, self.i18n.t("act.export"), self.doc.path.stem + ".json")
            if dest:
                export_nvram_json(self.doc, Path(dest))
                self._log(f"{self.i18n.t('msg.xml_exported')} {dest}")
            return
        if not self.eg or not self.eg.decrypted:
            return
        dest, _ = QFileDialog.getSaveFileName(self, self.i18n.t("act.export"), self.eg.path.stem + ".json")
        if dest:
            export_json(self.eg, Path(dest))
            self._log(f"{self.i18n.t('msg.exported')} {dest}")

    def on_export_csv(self) -> None:
        if self.doc is None:
            return
        dest, _ = QFileDialog.getSaveFileName(self, self.i18n.t("act.export_csv"), self.doc.path.stem + ".csv")
        if dest:
            export_nvram_csv(self.doc, Path(dest))
            self._log(f"{self.i18n.t('msg.xml_exported')} {dest}")

    def on_import(self) -> None:
        if not self.eg:
            return
        src, _ = QFileDialog.getOpenFileName(self, self.i18n.t("act.import"), filter="JSON (*.json)")
        if not src:
            return
        pt = import_plaintext_hex(Path(src))
        self.eg.plaintext = pt
        self.hex_view.setPlainText(pt.hex(" "))
        self._show_analysis()
        self._refresh_info()

    def apply_theme(self, name: str) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.instance().setStyleSheet(themes.DARK if name == "dark" else themes.LIGHT)
        self.settings.setValue("theme", name)

    def set_lang(self, code: str) -> None:
        self.i18n.set_language(code)
        self.settings.setValue("lang", code)
        self._retranslate()

    def on_about(self) -> None:
        QMessageBox.information(self, self.i18n.t("act.about"), self.i18n.t("about.text"))
