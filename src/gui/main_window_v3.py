from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QThread, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.gui.worker import GuiRunRequest, ProcessingWorker


class MainWindowV3(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DOCX 處理工具 GUI（V3）")
        self.resize(920, 700)

        self._thread: QThread | None = None
        self._worker: ProcessingWorker | None = None
        self._last_output_dir: Path | None = None
        self._last_report_path: Path | None = None

        self._build_ui()
        self._bind_events()
        self._apply_mode_state()
        self._update_open_buttons()

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)

        mode_box = QGroupBox("執行模式")
        mode_row = QHBoxLayout(mode_box)
        self.single_mode_radio = QRadioButton("單檔模式")
        self.batch_mode_radio = QRadioButton("資料夾批次模式")
        self.single_mode_radio.setChecked(True)
        mode_row.addWidget(self.single_mode_radio)
        mode_row.addWidget(self.batch_mode_radio)
        mode_row.addStretch(1)
        layout.addWidget(mode_box)

        form = QGridLayout()
        row = 0

        self.single_input_edit = QLineEdit()
        self.single_input_button = QPushButton("選擇單檔")
        form.addWidget(QLabel("輸入檔案（.docx）"), row, 0)
        form.addWidget(self.single_input_edit, row, 1)
        form.addWidget(self.single_input_button, row, 2)
        row += 1

        self.input_dir_edit = QLineEdit()
        self.input_dir_button = QPushButton("選擇資料夾")
        form.addWidget(QLabel("輸入資料夾"), row, 0)
        form.addWidget(self.input_dir_edit, row, 1)
        form.addWidget(self.input_dir_button, row, 2)
        row += 1

        self.output_dir_edit = QLineEdit()
        self.output_dir_button = QPushButton("選擇輸出資料夾")
        form.addWidget(QLabel("輸出資料夾"), row, 0)
        form.addWidget(self.output_dir_edit, row, 1)
        form.addWidget(self.output_dir_button, row, 2)
        row += 1

        self.recursive_checkbox = QCheckBox("遞迴掃描子資料夾（recursive）")
        form.addWidget(self.recursive_checkbox, row, 1, 1, 2)
        row += 1

        self.config_edit = QLineEdit()
        self.config_button = QPushButton("選擇設定檔")
        form.addWidget(QLabel("設定檔（可選）"), row, 0)
        form.addWidget(self.config_edit, row, 1)
        form.addWidget(self.config_button, row, 2)
        row += 1

        self.term_dict_edit = QLineEdit()
        self.term_dict_button = QPushButton("選擇詞庫")
        form.addWidget(QLabel("低風險詞庫（可選）"), row, 0)
        form.addWidget(self.term_dict_edit, row, 1)
        form.addWidget(self.term_dict_button, row, 2)
        row += 1

        self.report_name_edit = QLineEdit("report.xlsx")
        form.addWidget(QLabel("報告檔名（可選）"), row, 0)
        form.addWidget(self.report_name_edit, row, 1, 1, 2)
        layout.addLayout(form)

        action_row = QHBoxLayout()
        self.start_button = QPushButton("開始執行")
        self.open_output_button = QPushButton("開啟輸出資料夾")
        self.open_report_button = QPushButton("開啟報告")
        action_row.addWidget(self.start_button)
        action_row.addWidget(self.open_output_button)
        action_row.addWidget(self.open_report_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("尚未開始")
        layout.addWidget(self.status_label)

        self.summary_label = QLabel("成功：0｜失敗：0｜低風險替換：0｜高風險候選：0｜異常字元：0")
        layout.addWidget(self.summary_label)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        layout.addWidget(self.log_box)

        self.setCentralWidget(root)

    def _bind_events(self) -> None:
        self.single_mode_radio.toggled.connect(self._apply_mode_state)
        self.batch_mode_radio.toggled.connect(self._apply_mode_state)
        self.single_input_button.clicked.connect(self._pick_single_file)
        self.input_dir_button.clicked.connect(self._pick_input_dir)
        self.output_dir_button.clicked.connect(self._pick_output_dir)
        self.config_button.clicked.connect(self._pick_config_file)
        self.term_dict_button.clicked.connect(self._pick_term_dict_file)
        self.start_button.clicked.connect(self._start)
        self.open_output_button.clicked.connect(self._open_output_dir)
        self.open_report_button.clicked.connect(self._open_report_file)

    def _apply_mode_state(self) -> None:
        single = self.single_mode_radio.isChecked()
        self.single_input_edit.setEnabled(single)
        self.single_input_button.setEnabled(single)
        self.input_dir_edit.setEnabled(not single)
        self.input_dir_button.setEnabled(not single)
        self.recursive_checkbox.setEnabled(not single)
        if single:
            self.recursive_checkbox.setChecked(False)

    def _pick_single_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇 .docx 檔案", "", "Word 文件 (*.docx)")
        if path:
            self.single_input_edit.setText(path)

    def _pick_input_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "選擇輸入資料夾")
        if path:
            self.input_dir_edit.setText(path)

    def _pick_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "選擇輸出資料夾")
        if path:
            self.output_dir_edit.setText(path)

    def _pick_config_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇 config.yaml", "", "YAML (*.yaml *.yml)")
        if path:
            self.config_edit.setText(path)

    def _pick_term_dict_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇詞庫檔", "", "YAML (*.yaml *.yml)")
        if path:
            self.term_dict_edit.setText(path)

    def _build_request(self) -> GuiRunRequest:
        output_text = self.output_dir_edit.text().strip()
        if not output_text:
            raise ValueError("請先選擇輸出資料夾。")
        output_dir = Path(output_text)
        output_dir.mkdir(parents=True, exist_ok=True)

        if self.single_mode_radio.isChecked():
            input_file_text = self.single_input_edit.text().strip()
            if not input_file_text:
                raise ValueError("請先選擇單一 .docx 檔案。")
            input_file = Path(input_file_text)
            if not input_file.exists():
                raise ValueError("找不到輸入檔案。")
            if input_file.suffix.lower() != ".docx":
                raise ValueError("輸入檔案必須是 .docx。")
            input_dir = None
            recursive = False
        else:
            input_dir_text = self.input_dir_edit.text().strip()
            if not input_dir_text:
                raise ValueError("請先選擇輸入資料夾。")
            input_dir = Path(input_dir_text)
            if not input_dir.exists() or not input_dir.is_dir():
                raise ValueError("輸入資料夾不存在或格式不正確。")
            input_file = None
            recursive = self.recursive_checkbox.isChecked()

        config_path = Path(self.config_edit.text().strip()) if self.config_edit.text().strip() else None
        term_dict_path = Path(self.term_dict_edit.text().strip()) if self.term_dict_edit.text().strip() else None
        report_name = self.report_name_edit.text().strip() or None

        return GuiRunRequest(
            output_dir=output_dir,
            input_file=input_file,
            input_dir=input_dir,
            recursive=recursive,
            config_path=config_path,
            term_dict_path=term_dict_path,
            report_name=report_name,
        )

    def _start(self) -> None:
        try:
            request = self._build_request()
        except ValueError as exc:
            QMessageBox.warning(self, "輸入錯誤", str(exc))
            return

        self.start_button.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.status_label.setText("執行中...")
        self.log_box.clear()
        self.log_box.append("開始執行...")

        self._thread = QThread(self)
        self._worker = ProcessingWorker(request)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.success.connect(self._on_success)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_progress(self, current: int, total: int, message: str) -> None:
        if total > 0:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
        self.status_label.setText(message)
        self.log_box.append(message)

    def _on_success(self, payload: dict) -> None:
        success_count = int(payload["success_count"])
        failure_count = int(payload["failure_count"])
        total_replacements = int(payload.get("total_replacements", 0))
        total_review_candidates = int(payload.get("total_review_candidates", 0))
        total_anomalies = int(payload.get("total_anomalies", 0))

        self._last_output_dir = Path(payload["output_dir"])
        self._last_report_path = Path(payload["report_path"])

        self.summary_label.setText(
            f"成功：{success_count}｜失敗：{failure_count}｜"
            f"低風險替換：{total_replacements}｜高風險候選：{total_review_candidates}｜異常字元：{total_anomalies}"
        )
        if failure_count > 0:
            self.status_label.setText("執行完成（含檔案層級失敗，請查看報告 failures 工作表）")
        else:
            self.status_label.setText("執行完成")
        self.log_box.append(f"報告檔案：{self._last_report_path}")
        self._update_open_buttons()

    def _on_error(self, message: str) -> None:
        self.status_label.setText("執行失敗")
        self.log_box.append(f"錯誤：{message}")
        QMessageBox.critical(self, "執行失敗", f"處理失敗：{message}")

    def _on_finished(self) -> None:
        self.start_button.setEnabled(True)
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

    def _update_open_buttons(self) -> None:
        self.open_output_button.setEnabled(
            self._last_output_dir is not None and self._last_output_dir.exists()
        )
        self.open_report_button.setEnabled(
            self._last_report_path is not None and self._last_report_path.exists()
        )

    def _open_output_dir(self) -> None:
        if self._last_output_dir is None or not self._last_output_dir.exists():
            QMessageBox.information(self, "尚無輸出", "目前沒有可開啟的輸出資料夾。")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_output_dir)))

    def _open_report_file(self) -> None:
        if self._last_report_path is None or not self._last_report_path.exists():
            QMessageBox.information(self, "尚無報告", "目前沒有可開啟的報告檔案。")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_report_path)))

