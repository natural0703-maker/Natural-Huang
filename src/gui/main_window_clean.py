from __future__ import annotations

from pathlib import Path
from pathlib import PureWindowsPath
from typing import Any

from PySide6.QtCore import QThread, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
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

from src.config_loader import load_config
from src.gui import phase1_worker
from src.gui.worker import GuiRunRequest, ProcessingWorker


def normalize_path_for_display(raw_path: str | Path) -> str:
    path = Path(str(raw_path)).expanduser()
    try:
        normalized = path.resolve()
    except OSError:
        normalized = path
    return str(PureWindowsPath(str(normalized)))


def should_autofill_output_dir(
    current_output_text: str,
    last_auto_output_text: str | None,
    user_modified: bool,
) -> bool:
    if user_modified:
        return False
    if not current_output_text.strip():
        return True
    if last_auto_output_text is None:
        return True
    return normalize_path_for_display(current_output_text) == normalize_path_for_display(last_auto_output_text)


def _phase1_paragraph_merge_summary(result: Any) -> dict[str, int | str]:
    apply_result = getattr(result, "apply_result", None)
    summary = getattr(apply_result, "paragraph_merge_summary", None) if apply_result is not None else None
    if summary is None:
        return {
            "applied_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "codes_text": "無",
        }

    codes = getattr(summary, "codes", {}) or {}
    codes_text = "無"
    if codes:
        codes_text = ", ".join(f"{code}={count}" for code, count in sorted(codes.items()))

    return {
        "applied_count": int(getattr(summary, "applied_count", 0) or 0),
        "skipped_count": int(getattr(summary, "skipped_count", 0) or 0),
        "failed_count": int(getattr(summary, "failed_count", 0) or 0),
        "codes_text": codes_text,
    }


def _phase1_paragraph_merge_mismatch_type_label(raw_type: object) -> str:
    mismatch_type = str(raw_type)
    if mismatch_type == "source_text":
        return "前段 mismatch"
    if mismatch_type == "next_source_text":
        return "後段 mismatch"
    return mismatch_type


def _phase1_paragraph_merge_sample_entry_text(index: int, entry: object) -> str:
    candidate_id = str(getattr(entry, "candidate_id", ""))
    mismatch_type = _phase1_paragraph_merge_mismatch_type_label(getattr(entry, "mismatch_type", ""))
    expected_preview = str(getattr(entry, "expected_preview", ""))
    actual_preview = str(getattr(entry, "actual_preview", ""))
    return (
        f"{index}. 候選：{candidate_id}；類型：{mismatch_type}；"
        f"預期：{expected_preview}；目前：{actual_preview}"
    )


def _phase1_paragraph_merge_diagnostics(result: Any) -> dict[str, int | str]:
    apply_result = getattr(result, "apply_result", None)
    diagnostics = (
        getattr(apply_result, "paragraph_merge_diagnostics", None) if apply_result is not None else None
    )
    if diagnostics is None:
        return {
            "total_mismatch_count": 0,
            "source_mismatch_count": 0,
            "next_source_mismatch_count": 0,
            "sample_candidate_ids_text": "無",
            "sample_entries_text": "無",
        }

    sample_candidate_ids = list(getattr(diagnostics, "sample_candidate_ids", []) or [])
    sample_candidate_ids_text = "無"
    if sample_candidate_ids:
        sample_candidate_ids_text = ", ".join(str(candidate_id) for candidate_id in sample_candidate_ids)

    sample_entries = list(getattr(diagnostics, "sample_entries", []) or [])[:3]
    sample_entries_text = "無"
    if sample_entries:
        sample_entries_text = " | ".join(
            _phase1_paragraph_merge_sample_entry_text(index, entry)
            for index, entry in enumerate(sample_entries, start=1)
        )

    return {
        "total_mismatch_count": int(getattr(diagnostics, "total_mismatch_count", 0) or 0),
        "source_mismatch_count": int(getattr(diagnostics, "source_mismatch_count", 0) or 0),
        "next_source_mismatch_count": int(getattr(diagnostics, "next_source_mismatch_count", 0) or 0),
        "sample_candidate_ids_text": sample_candidate_ids_text,
        "sample_entries_text": sample_entries_text,
    }


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DOCX 文件處理工具 GUI（V3.6）")
        self.resize(980, 760)

        self._thread: QThread | None = None
        self._worker: ProcessingWorker | None = None
        self._last_output_dir: Path | None = None
        self._last_report_path: Path | None = None
        self._last_review_summary_path: Path | None = None
        self._last_apply_summary_path: Path | None = None
        self._last_reviewed_file_path: Path | None = None
        self._output_dir_user_modified = False
        self._last_auto_output_dir_text: str | None = None
        self._active_profile_name: str = "default"
        self._available_profile_names: list[str] = ["default"]
        self._profile_details: dict[str, dict[str, str]] = {}
        self._last_phase1_result = None

        self._build_ui()
        self._bind_events()
        self._apply_mode_state()
        self._apply_phase1_mode_state()
        self._update_open_buttons()
        self._refresh_profiles_from_config()

    def _build_ui(self) -> None:
        root = QWidget(self)
        layout = QVBoxLayout(root)

        mode_box = QGroupBox("處理模式")
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
        self.single_input_button = QPushButton("選擇檔案")
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
        self.output_dir_button = QPushButton("選擇資料夾")
        form.addWidget(QLabel("輸出資料夾"), row, 0)
        form.addWidget(self.output_dir_edit, row, 1)
        form.addWidget(self.output_dir_button, row, 2)
        row += 1

        self.recursive_checkbox = QCheckBox("遞迴處理子資料夾（recursive）")
        form.addWidget(self.recursive_checkbox, row, 1, 1, 2)
        row += 1

        self.config_edit = QLineEdit()
        self.config_button = QPushButton("選擇設定檔")
        form.addWidget(QLabel("設定檔（可選）"), row, 0)
        form.addWidget(self.config_edit, row, 1)
        form.addWidget(self.config_button, row, 2)
        row += 1

        self.profile_combo = QComboBox()
        form.addWidget(QLabel("規則方案（Profile）"), row, 0)
        form.addWidget(self.profile_combo, row, 1, 1, 2)
        row += 1

        self.term_dict_edit = QLineEdit()
        self.term_dict_button = QPushButton("選擇詞庫")
        form.addWidget(QLabel("低風險詞庫（可選）"), row, 0)
        form.addWidget(self.term_dict_edit, row, 1)
        form.addWidget(self.term_dict_button, row, 2)
        row += 1

        self.high_risk_rules_edit = QLineEdit()
        self.high_risk_rules_button = QPushButton("選擇高風險規則")
        form.addWidget(QLabel("高風險規則（可選）"), row, 0)
        form.addWidget(self.high_risk_rules_edit, row, 1)
        form.addWidget(self.high_risk_rules_button, row, 2)
        row += 1

        self.report_name_edit = QLineEdit("report.xlsx")
        form.addWidget(QLabel("報告檔名（可選）"), row, 0)
        form.addWidget(self.report_name_edit, row, 1, 1, 2)
        row += 1

        self.apply_review_summary_edit = QLineEdit()
        self.apply_review_summary_button = QPushButton("選擇待複核報表")
        form.addWidget(QLabel("回填來源（可選）"), row, 0)
        form.addWidget(self.apply_review_summary_edit, row, 1)
        form.addWidget(self.apply_review_summary_button, row, 2)
        row += 1

        format_box = QGroupBox("文件格式覆寫（可選）")
        format_grid = QGridLayout(format_box)

        self.body_font_edit = QLineEdit("\u65b0\u7d30\u660e\u9ad4")
        self.body_font_size_edit = QLineEdit("12")
        self.indent_chars_edit = QLineEdit("2")
        self.space_after_edit = QLineEdit("6")
        self.margin_cm_edit = QLineEdit("1.27")
        self.heading_style_edit = QLineEdit("Heading 2")

        format_grid.addWidget(QLabel("內文字體"), 0, 0)
        format_grid.addWidget(self.body_font_edit, 0, 1)
        format_grid.addWidget(QLabel("內文字級（pt）"), 0, 2)
        format_grid.addWidget(self.body_font_size_edit, 0, 3)

        format_grid.addWidget(QLabel("首行縮排（字元）"), 1, 0)
        format_grid.addWidget(self.indent_chars_edit, 1, 1)
        format_grid.addWidget(QLabel("段後距離（pt）"), 1, 2)
        format_grid.addWidget(self.space_after_edit, 1, 3)

        format_grid.addWidget(QLabel("四邊邊界（cm）"), 2, 0)
        format_grid.addWidget(self.margin_cm_edit, 2, 1)
        format_grid.addWidget(QLabel("章節標題樣式"), 2, 2)
        format_grid.addWidget(self.heading_style_edit, 2, 3)

        layout.addLayout(form)
        layout.addWidget(format_box)

        phase1_box = QGroupBox("Phase 1 最小操作")
        phase1_grid = QGridLayout(phase1_box)
        row = 0

        self.phase1_operation_combo = QComboBox()
        self.phase1_operation_combo.addItem("Analyze", "analyze")
        self.phase1_operation_combo.addItem("Convert", "convert")
        self.phase1_operation_combo.addItem("Apply Review", "apply_review")
        phase1_grid.addWidget(QLabel("模式"), row, 0)
        phase1_grid.addWidget(self.phase1_operation_combo, row, 1, 1, 2)
        row += 1

        self.phase1_input_edit = QLineEdit()
        self.phase1_input_button = QPushButton("選擇檔案")
        phase1_grid.addWidget(QLabel("輸入檔案"), row, 0)
        phase1_grid.addWidget(self.phase1_input_edit, row, 1)
        phase1_grid.addWidget(self.phase1_input_button, row, 2)
        row += 1

        self.phase1_output_dir_edit = QLineEdit()
        self.phase1_output_dir_button = QPushButton("選擇資料夾")
        phase1_grid.addWidget(QLabel("輸出資料夾"), row, 0)
        phase1_grid.addWidget(self.phase1_output_dir_edit, row, 1)
        phase1_grid.addWidget(self.phase1_output_dir_button, row, 2)
        row += 1

        self.phase1_config_edit = QLineEdit()
        self.phase1_config_button = QPushButton("選擇設定檔")
        phase1_grid.addWidget(QLabel("設定檔（可選）"), row, 0)
        phase1_grid.addWidget(self.phase1_config_edit, row, 1)
        phase1_grid.addWidget(self.phase1_config_button, row, 2)
        row += 1

        self.phase1_profile_edit = QLineEdit()
        phase1_grid.addWidget(QLabel("Profile（可選）"), row, 0)
        phase1_grid.addWidget(self.phase1_profile_edit, row, 1, 1, 2)
        row += 1

        self.phase1_apply_review_edit = QLineEdit()
        self.phase1_apply_review_button = QPushButton("選擇 JSON")
        phase1_grid.addWidget(QLabel("reviewed JSON"), row, 0)
        phase1_grid.addWidget(self.phase1_apply_review_edit, row, 1)
        phase1_grid.addWidget(self.phase1_apply_review_button, row, 2)
        row += 1

        self.phase1_reviewed_output_edit = QLineEdit()
        self.phase1_reviewed_output_button = QPushButton("選擇輸出檔")
        phase1_grid.addWidget(QLabel("reviewed 輸出檔"), row, 0)
        phase1_grid.addWidget(self.phase1_reviewed_output_edit, row, 1)
        phase1_grid.addWidget(self.phase1_reviewed_output_button, row, 2)
        row += 1

        self.phase1_run_button = QPushButton("執行 Phase 1")
        phase1_grid.addWidget(self.phase1_run_button, row, 1, 1, 2)
        row += 1

        self.phase1_result_label = QLabel("Phase 1 尚未執行")
        phase1_grid.addWidget(self.phase1_result_label, row, 0, 1, 3)
        row += 1

        self.phase1_error_label = QLabel("")
        phase1_grid.addWidget(self.phase1_error_label, row, 0, 1, 3)

        layout.addWidget(phase1_box)

        action_row = QHBoxLayout()
        self.start_button = QPushButton("開始執行")
        self.apply_review_button = QPushButton("套用複核結果")
        self.open_output_button = QPushButton("開啟輸出資料夾")
        self.open_report_button = QPushButton("開啟報告")
        self.open_review_summary_button = QPushButton("開啟待複核報表")
        self.open_apply_summary_button = QPushButton("開啟回填摘要")
        self.open_reviewed_file_button = QPushButton("開啟第二版文件")
        action_row.addWidget(self.start_button)
        action_row.addWidget(self.apply_review_button)
        action_row.addWidget(self.open_output_button)
        action_row.addWidget(self.open_report_button)
        action_row.addWidget(self.open_review_summary_button)
        action_row.addWidget(self.open_apply_summary_button)
        action_row.addWidget(self.open_reviewed_file_button)
        action_row.addStretch(1)
        layout.addLayout(action_row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("尚未執行")
        layout.addWidget(self.status_label)

        self.summary_label = QLabel("成功=0 | 失敗=0 | 低風險替換=0 | 高風險候選=0 | 異常字元=0")
        layout.addWidget(self.summary_label)
        self.risk_summary_label = QLabel("高風險分類：grammar=0 | wording=0 | regional_usage=0")
        layout.addWidget(self.risk_summary_label)
        self.top_risk_files_label = QLabel("高風險較多檔案：無")
        layout.addWidget(self.top_risk_files_label)
        self.rules_info_label = QLabel(
            "規則資訊：低風險詞庫=未設定 | 高風險規則=未設定 | 低風險啟用數=0 | 高風險啟用數=0 | 設定檔=預設"
        )
        layout.addWidget(self.rules_info_label)
        self.profile_info_label = QLabel("Profile：default")
        layout.addWidget(self.profile_info_label)

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
        self.profile_combo.currentIndexChanged.connect(self._on_profile_changed)
        self.term_dict_button.clicked.connect(self._pick_term_dict_file)
        self.high_risk_rules_button.clicked.connect(self._pick_high_risk_rules_file)
        self.apply_review_summary_button.clicked.connect(self._pick_apply_review_summary_file)
        self.phase1_operation_combo.currentIndexChanged.connect(self._apply_phase1_mode_state)
        self.phase1_input_button.clicked.connect(self._pick_phase1_input_file)
        self.phase1_output_dir_button.clicked.connect(self._pick_phase1_output_dir)
        self.phase1_config_button.clicked.connect(self._pick_phase1_config_file)
        self.phase1_apply_review_button.clicked.connect(self._pick_phase1_apply_review_file)
        self.phase1_reviewed_output_button.clicked.connect(self._pick_phase1_reviewed_output_file)
        self.phase1_run_button.clicked.connect(self._run_phase1)
        self.output_dir_edit.textEdited.connect(self._on_output_dir_text_edited)
        self.start_button.clicked.connect(self._start)
        self.apply_review_button.clicked.connect(self._start_apply_review)
        self.open_output_button.clicked.connect(self._open_output_dir)
        self.open_report_button.clicked.connect(self._open_report_file)
        self.open_review_summary_button.clicked.connect(self._open_review_summary_file)
        self.open_apply_summary_button.clicked.connect(self._open_apply_summary_file)
        self.open_reviewed_file_button.clicked.connect(self._open_reviewed_file)

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
            self.single_input_edit.setText(normalize_path_for_display(path))
            self._prefill_output_dir_from_path(Path(path).parent)

    def _pick_input_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "選擇輸入資料夾")
        if path:
            self.input_dir_edit.setText(normalize_path_for_display(path))
            self._prefill_output_dir_from_path(Path(path))

    def _pick_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "選擇輸出資料夾")
        if path:
            self.output_dir_edit.setText(normalize_path_for_display(path))
            self._output_dir_user_modified = True

    def _prefill_output_dir_from_path(self, path: Path) -> None:
        new_auto_output = normalize_path_for_display(path)
        if not should_autofill_output_dir(
            current_output_text=self.output_dir_edit.text(),
            last_auto_output_text=self._last_auto_output_dir_text,
            user_modified=self._output_dir_user_modified,
        ):
            return
        self.output_dir_edit.setText(new_auto_output)
        self._last_auto_output_dir_text = new_auto_output
        self._output_dir_user_modified = False

    def _on_output_dir_text_edited(self, _text: str) -> None:
        self._output_dir_user_modified = True

    def _pick_config_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇設定檔", "", "YAML (*.yaml *.yml)")
        if path:
            self.config_edit.setText(normalize_path_for_display(path))
            self._refresh_profiles_from_config()

    def _pick_term_dict_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇詞庫檔", "", "YAML (*.yaml *.yml)")
        if path:
            self.term_dict_edit.setText(normalize_path_for_display(path))

    def _pick_high_risk_rules_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇高風險規則檔", "", "YAML (*.yaml *.yml)")
        if path:
            self.high_risk_rules_edit.setText(normalize_path_for_display(path))

    def _pick_apply_review_summary_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "選擇待套用的 review_summary",
            "",
            "Review Summary (*.xlsx *.csv)",
        )
        if path:
            self.apply_review_summary_edit.setText(normalize_path_for_display(path))

    def _apply_phase1_mode_state(self) -> None:
        operation = str(self.phase1_operation_combo.currentData() or "analyze")
        needs_output_dir = operation in {"convert", "apply_review"}
        needs_apply_review = operation == "apply_review"

        self.phase1_output_dir_edit.setEnabled(needs_output_dir)
        self.phase1_output_dir_button.setEnabled(needs_output_dir)
        self.phase1_apply_review_edit.setEnabled(needs_apply_review)
        self.phase1_apply_review_button.setEnabled(needs_apply_review)
        self.phase1_reviewed_output_edit.setEnabled(needs_apply_review)
        self.phase1_reviewed_output_button.setEnabled(needs_apply_review)

    def _pick_phase1_input_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇 Phase 1 輸入檔案", "", "Word 文件 (*.docx)")
        if path:
            self.phase1_input_edit.setText(normalize_path_for_display(path))

    def _pick_phase1_output_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "選擇 Phase 1 輸出資料夾")
        if path:
            self.phase1_output_dir_edit.setText(normalize_path_for_display(path))

    def _pick_phase1_config_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇 Phase 1 設定檔", "", "YAML (*.yaml *.yml)")
        if path:
            self.phase1_config_edit.setText(normalize_path_for_display(path))

    def _pick_phase1_apply_review_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "選擇 reviewed JSON", "", "JSON (*.json)")
        if path:
            self.phase1_apply_review_edit.setText(normalize_path_for_display(path))

    def _pick_phase1_reviewed_output_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "選擇 reviewed 輸出檔", "", "Word 文件 (*.docx)")
        if path:
            self.phase1_reviewed_output_edit.setText(normalize_path_for_display(path))

    def _phase1_optional_path(self, text: str) -> Path | None:
        stripped = text.strip()
        return Path(stripped) if stripped else None

    def _build_phase1_request(self) -> phase1_worker.Phase1GuiRequest:
        operation = str(self.phase1_operation_combo.currentData() or "analyze")
        input_text = self.phase1_input_edit.text().strip()
        output_dir_text = self.phase1_output_dir_edit.text().strip()
        apply_review_text = self.phase1_apply_review_edit.text().strip()
        reviewed_output_text = self.phase1_reviewed_output_edit.text().strip()

        if not input_text:
            raise ValueError("請先輸入 Phase 1 輸入檔案。")
        if operation == "convert" and not output_dir_text:
            raise ValueError("Convert 模式需要輸出資料夾。")
        if operation == "apply_review":
            if not apply_review_text:
                raise ValueError("Apply Review 模式需要 reviewed JSON。")
            if not output_dir_text and not reviewed_output_text:
                raise ValueError("Apply Review 模式需要輸出資料夾或 reviewed 輸出檔。")

        profile = self.phase1_profile_edit.text().strip() or None
        return phase1_worker.Phase1GuiRequest(
            operation=operation,
            input_path=Path(input_text),
            output_dir=self._phase1_optional_path(output_dir_text),
            config_path=self._phase1_optional_path(self.phase1_config_edit.text()),
            profile=profile,
            apply_review_path=self._phase1_optional_path(apply_review_text),
            reviewed_output_path=self._phase1_optional_path(reviewed_output_text),
        )

    def _run_phase1(self) -> None:
        try:
            request = self._build_phase1_request()
        except ValueError as exc:
            self.phase1_error_label.setText(str(exc))
            QMessageBox.warning(self, "Phase 1 輸入錯誤", str(exc))
            return

        self.phase1_error_label.setText("")
        try:
            result = phase1_worker.run_phase1_gui_request(request)
        except Exception as exc:
            message = f"Phase 1 執行失敗：{exc}"
            self.phase1_result_label.setText("Phase 1 執行失敗")
            self.phase1_error_label.setText(message)
            QMessageBox.critical(self, "Phase 1 執行失敗", message)
            return

        self._last_phase1_result = result
        self._show_phase1_result(result)

    def _show_phase1_result(self, result) -> None:
        schema = getattr(result, "schema", None)
        errors = list(getattr(schema, "errors", []) or [])
        config_check = getattr(result, "config_check", None)
        config_warnings = list(getattr(config_check, "warnings", []) or [])
        operation = str(getattr(result, "operation", ""))
        output_path = getattr(result, "output_path", None)
        error_count = len(errors)
        warning_count = len(config_warnings)
        toc = getattr(schema, "toc", None)
        toc_status = str(getattr(toc, "status", "not_requested"))
        toc_fallback = "是" if bool(getattr(toc, "fallback_used", False)) else "否"
        toc_chapter_count = int(getattr(toc, "chapter_count", 0) or 0)
        merge_summary = _phase1_paragraph_merge_summary(result)
        merge_diagnostics = _phase1_paragraph_merge_diagnostics(result)

        if operation == "analyze":
            summary = (
                f"Analyze | 章節候選數={len(getattr(schema, 'chapter_candidates', []) or [])} | "
                f"高風險候選數={len(getattr(schema, 'review_candidates', []) or [])} | "
                f"段落合併候選數={len(getattr(schema, 'paragraph_merge_candidates', []) or [])} | "
                f"錯誤數={error_count} | 設定警告數={warning_count}"
            )
        elif operation == "convert":
            summary = (
                f"Convert | 輸出檔案={output_path or ''} | "
                f"高風險候選數={len(getattr(schema, 'review_candidates', []) or [])} | "
                f"錯誤數={error_count} | 設定警告數={warning_count}"
            )
        elif operation == "apply_review":
            apply_result = getattr(result, "apply_result", None)
            summary = (
                f"Apply Review | 輸出檔案={output_path or ''} | "
                f"套用數={int(getattr(apply_result, 'applied_count', 0) or 0)} | "
                f"略過數={int(getattr(apply_result, 'skipped_count', 0) or 0)} | "
                f"失敗數={int(getattr(apply_result, 'failed_count', 0) or 0)} | "
                f"錯誤數={error_count} | 設定警告數={warning_count}"
            )
        else:
            summary = f"Phase 1 | 操作={operation} | 錯誤數={error_count} | 設定警告數={warning_count}"

        summary = (
            f"{summary} | TOC 狀態：{toc_status} | TOC fallback：{toc_fallback} | "
            f"TOC 章節數：{toc_chapter_count} | "
            f"段落合併套用數：{merge_summary['applied_count']} | "
            f"段落合併略過數：{merge_summary['skipped_count']} | "
            f"段落合併失敗數：{merge_summary['failed_count']} | "
            f"段落合併結果碼摘要：{merge_summary['codes_text']} | "
            f"段落合併 mismatch 總數：{merge_diagnostics['total_mismatch_count']} | "
            f"段落合併前段 mismatch：{merge_diagnostics['source_mismatch_count']} | "
            f"段落合併後段 mismatch：{merge_diagnostics['next_source_mismatch_count']} | "
            f"段落合併 mismatch 範例候選：{merge_diagnostics['sample_candidate_ids_text']} | "
            f"段落合併 mismatch 範例：{merge_diagnostics['sample_entries_text']}"
        )
        self.phase1_result_label.setText(summary)
        if errors:
            first = errors[0]
            code = getattr(first, "code", "")
            message = getattr(first, "message", "")
            self.phase1_error_label.setText(f"第一個錯誤：{code} {message}".strip())
        else:
            self.phase1_error_label.setText("")

    def _on_profile_changed(self, _index: int) -> None:
        selected = self.profile_combo.currentData()
        if isinstance(selected, str) and selected.strip():
            self._active_profile_name = selected.strip()
        else:
            self._active_profile_name = "default"
        details = self._profile_details.get(self._active_profile_name, {})
        low = details.get("low_risk_dict", "未知")
        high = details.get("high_risk_rules", "未知")
        heading = details.get("heading_style_name", "Heading 2")
        self.profile_info_label.setText(
            f"Profile：{self._active_profile_name} | 低風險詞庫：{low} | 高風險規則：{high} | 標題樣式：{heading}"
        )

    def _refresh_profiles_from_config(self) -> None:
        config_text = self.config_edit.text().strip()
        config_path = Path(config_text) if config_text else None
        try:
            cfg = load_config(config_path)
        except Exception as exc:
            self.profile_combo.clear()
            self.profile_combo.addItem("default", "default")
            self._available_profile_names = ["default"]
            self._active_profile_name = "default"
            self._profile_details = {}
            self.profile_info_label.setText(f"Profile：default（載入失敗：{exc}）")
            return

        current_selected = self.profile_combo.currentData()
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self._available_profile_names = sorted(cfg.profiles.keys())
        self._profile_details = {}
        for name in self._available_profile_names:
            self.profile_combo.addItem(name, name)
            profile_cfg = cfg.profiles[name]
            self._profile_details[name] = {
                "low_risk_dict": str(profile_cfg.low_risk_dict_path),
                "high_risk_rules": str(profile_cfg.high_risk_rules_path),
                "heading_style_name": profile_cfg.document_format.heading_style_name,
            }

        if isinstance(current_selected, str) and current_selected in cfg.profiles:
            target_profile = current_selected
        else:
            target_profile = cfg.active_profile if cfg.active_profile in cfg.profiles else self._available_profile_names[0]
        target_index = self.profile_combo.findData(target_profile)
        if target_index < 0:
            target_index = 0
        self.profile_combo.setCurrentIndex(target_index)
        self.profile_combo.blockSignals(False)
        self._active_profile_name = str(self.profile_combo.currentData())
        self._on_profile_changed(target_index)

    def _build_format_overrides(self) -> dict[str, Any]:
        def _to_float(text: str, fallback: float) -> float:
            try:
                return float(text.strip())
            except (TypeError, ValueError):
                return fallback

        margin = _to_float(self.margin_cm_edit.text(), 1.27)
        return {
            "body_font_name": self.body_font_edit.text().strip() or "\u65b0\u7d30\u660e\u9ad4",
            "body_font_size_pt": _to_float(self.body_font_size_edit.text(), 12.0),
            "body_first_line_indent_chars": _to_float(self.indent_chars_edit.text(), 2.0),
            "body_space_after_pt": _to_float(self.space_after_edit.text(), 6.0),
            "page_margin_top_cm": margin,
            "page_margin_bottom_cm": margin,
            "page_margin_left_cm": margin,
            "page_margin_right_cm": margin,
            "heading_style_name": self.heading_style_edit.text().strip() or "Heading 2",
        }

    def _build_request(self) -> GuiRunRequest:
        self._refresh_profiles_from_config()
        output_text = self.output_dir_edit.text().strip()
        if not output_text:
            raise ValueError("請先選擇輸出資料夾。")
        normalized_output = normalize_path_for_display(output_text)
        self.output_dir_edit.setText(normalized_output)
        output_dir = Path(normalized_output)
        output_dir.mkdir(parents=True, exist_ok=True)

        if self.single_mode_radio.isChecked():
            input_file_text = self.single_input_edit.text().strip()
            if not input_file_text:
                raise ValueError("請先選擇 .docx 檔案。")
            normalized_input_file = normalize_path_for_display(input_file_text)
            self.single_input_edit.setText(normalized_input_file)
            input_file = Path(normalized_input_file)
            if not input_file.exists():
                raise ValueError("找不到輸入檔案。")
            if input_file.suffix.lower() != ".docx":
                raise ValueError("輸入檔案必須為 .docx。")
            input_dir = None
            recursive = False
        else:
            input_dir_text = self.input_dir_edit.text().strip()
            if not input_dir_text:
                raise ValueError("請先選擇輸入資料夾。")
            normalized_input_dir = normalize_path_for_display(input_dir_text)
            self.input_dir_edit.setText(normalized_input_dir)
            input_dir = Path(normalized_input_dir)
            if not input_dir.exists() or not input_dir.is_dir():
                raise ValueError("輸入資料夾不存在或格式不正確。")
            input_file = None
            recursive = self.recursive_checkbox.isChecked()

        config_path = Path(self.config_edit.text().strip()) if self.config_edit.text().strip() else None
        term_dict_path = Path(self.term_dict_edit.text().strip()) if self.term_dict_edit.text().strip() else None
        high_risk_rules_path = (
            Path(self.high_risk_rules_edit.text().strip())
            if self.high_risk_rules_edit.text().strip()
            else None
        )
        if high_risk_rules_path is not None and not high_risk_rules_path.exists():
            raise ValueError("找不到高風險規則檔案。")
        report_name = self.report_name_edit.text().strip() or None

        return GuiRunRequest(
            mode="process",
            output_dir=output_dir,
            input_file=input_file,
            input_dir=input_dir,
            recursive=recursive,
            config_path=config_path,
            term_dict_path=term_dict_path,
            high_risk_rules_path=high_risk_rules_path,
            report_name=report_name,
            format_overrides=self._build_format_overrides(),
            profile=self._active_profile_name,
        )

    def _build_apply_request(self) -> GuiRunRequest:
        request = self._build_request()
        apply_review_summary_text = self.apply_review_summary_edit.text().strip()
        if not apply_review_summary_text:
            raise ValueError("請先選擇待套用的 review_summary 檔案。")
        apply_review_summary_path = Path(apply_review_summary_text)
        if not apply_review_summary_path.exists():
            raise ValueError("找不到待套用的 review_summary 檔案。")

        return GuiRunRequest(
            mode="apply_review",
            output_dir=request.output_dir,
            apply_review_summary_path=apply_review_summary_path,
            input_file=request.input_file,
            input_dir=request.input_dir,
            recursive=request.recursive,
            config_path=request.config_path,
            term_dict_path=None,
            report_name=None,
            format_overrides=request.format_overrides,
            profile=self._active_profile_name,
        )

    def _start(self) -> None:
        try:
            request = self._build_request()
        except ValueError as exc:
            QMessageBox.warning(self, "輸入錯誤", str(exc))
            return

        self.start_button.setEnabled(False)
        self.apply_review_button.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.status_label.setText("執行中...")
        self.log_box.clear()
        self.log_box.append("開始處理...")
        self.risk_summary_label.setText("高風險分類：grammar=0 | wording=0 | regional_usage=0")
        self.top_risk_files_label.setText("高風險較多檔案：無")
        self.rules_info_label.setText(
            "規則資訊：低風險詞庫=未設定 | 高風險規則=未設定 | 低風險啟用數=0 | 高風險啟用數=0 | 設定檔=預設"
        )
        self._last_report_path = None
        self._last_review_summary_path = None
        self._last_apply_summary_path = None
        self._last_reviewed_file_path = None
        self._update_open_buttons()

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

    def _start_apply_review(self) -> None:
        try:
            request = self._build_apply_request()
        except ValueError as exc:
            QMessageBox.warning(self, "輸入錯誤", str(exc))
            return

        self.start_button.setEnabled(False)
        self.apply_review_button.setEnabled(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setValue(0)
        self.status_label.setText("回填執行中...")
        self.log_box.clear()
        self.log_box.append("開始套用人工複核結果...")
        self._last_apply_summary_path = None
        self._last_reviewed_file_path = None
        self._update_open_buttons()

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
        mode = str(payload.get("mode", "process"))
        if mode == "apply_review":
            applied_count = int(payload.get("applied_count", 0))
            skipped_count = int(payload.get("skipped_count", 0))
            failed_count = int(payload.get("failed_count", 0))
            total_candidates = int(payload.get("total_candidates", 0))
            not_found_count = int(payload.get("not_found_count", 0))
            conflict_count = int(payload.get("conflict_count", 0))

            self._last_output_dir = Path(payload["output_dir"])
            apply_summary_raw = str(payload.get("apply_summary_path", "")).strip()
            self._last_apply_summary_path = Path(apply_summary_raw) if apply_summary_raw else None
            reviewed_raw = str(payload.get("reviewed_file_path", "")).strip()
            self._last_reviewed_file_path = Path(reviewed_raw) if reviewed_raw else None

            self.summary_label.setText(
                f"候選總數={total_candidates} | 套用={applied_count} | 跳過={skipped_count} | 失敗={failed_count}"
            )
            self.risk_summary_label.setText(
                f"找不到定位={not_found_count} | 衝突={conflict_count} | 失敗={failed_count}"
            )
            self.top_risk_files_label.setText("人工複核回填完成")
            self.status_label.setText("回填完成")
            if self._last_apply_summary_path:
                self.log_box.append(f"回填摘要：{self._last_apply_summary_path}")
            if self._last_reviewed_file_path:
                self.log_box.append(f"第二版文件：{self._last_reviewed_file_path}")
            self._update_open_buttons()
            return

        success_count = int(payload["success_count"])
        failure_count = int(payload["failure_count"])
        total_replacements = int(payload.get("total_replacements", 0))
        total_review_candidates = int(payload.get("total_review_candidates", 0))
        total_anomalies = int(payload.get("total_anomalies", 0))

        self._last_output_dir = Path(payload["output_dir"])
        self._last_report_path = Path(payload["report_path"])
        review_summary_raw = str(payload.get("review_summary_path", "")).strip()
        self._last_review_summary_path = Path(review_summary_raw) if review_summary_raw else None
        review_category_counts = payload.get("review_category_counts", {}) or {}
        top_risk_files = payload.get("top_risk_files", []) or []
        low_risk_rules_path = str(payload.get("low_risk_rules_path", "")).strip()
        high_risk_rules_path = str(payload.get("high_risk_rules_path", "")).strip()
        active_low_risk_rule_count = int(payload.get("active_low_risk_rule_count", 0))
        active_high_risk_rule_count = int(payload.get("active_high_risk_rule_count", 0))
        active_config_path = str(payload.get("active_config_path", "")).strip()
        active_profile = str(payload.get("active_profile", "default")).strip() or "default"
        available_profiles = payload.get("available_profiles", []) or []

        self.summary_label.setText(
            f"成功={success_count} | 失敗={failure_count} | "
            f"低風險替換={total_replacements} | 高風險候選={total_review_candidates} | 異常字元={total_anomalies}"
        )
        self.risk_summary_label.setText(
            "高風險分類："
            f"grammar={int(review_category_counts.get('grammar', 0))} | "
            f"wording={int(review_category_counts.get('wording', 0))} | "
            f"regional_usage={int(review_category_counts.get('regional_usage', 0))}"
        )
        if top_risk_files:
            top_text = "、".join(f"{name}({count})" for name, count in top_risk_files[:3])
            self.top_risk_files_label.setText(f"高風險較多檔案：{top_text}")
        else:
            self.top_risk_files_label.setText("高風險較多檔案：無")
        self.rules_info_label.setText(
            "規則資訊："
            f"低風險詞庫={low_risk_rules_path or '預設'} | "
            f"高風險規則={high_risk_rules_path or '預設'} | "
            f"低風險啟用數={active_low_risk_rule_count} | "
            f"高風險啟用數={active_high_risk_rule_count} | "
            f"設定檔={active_config_path or '預設'}"
        )
        if available_profiles:
            profiles_text = "、".join(str(item) for item in available_profiles)
            self.profile_info_label.setText(f"Profile：{active_profile}（可用：{profiles_text}）")
        else:
            self.profile_info_label.setText(f"Profile：{active_profile}")
        combo_index = self.profile_combo.findData(active_profile)
        if combo_index >= 0:
            self.profile_combo.setCurrentIndex(combo_index)
        self.status_label.setText("執行完成" if failure_count == 0 else "執行完成（含檔案層級失敗）")
        self.log_box.append(f"報告檔案：{self._last_report_path}")
        if self._last_review_summary_path:
            self.log_box.append(f"待複核報表：{self._last_review_summary_path}")
        self._update_open_buttons()

    def _on_error(self, message: str) -> None:
        self.status_label.setText("執行失敗")
        self.log_box.append(f"錯誤：{message}")
        QMessageBox.critical(self, "處理失敗", message)

    def _on_finished(self) -> None:
        self.start_button.setEnabled(True)
        self.apply_review_button.setEnabled(True)
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
        self.open_review_summary_button.setEnabled(
            self._last_review_summary_path is not None and self._last_review_summary_path.exists()
        )
        self.open_apply_summary_button.setEnabled(
            self._last_apply_summary_path is not None and self._last_apply_summary_path.exists()
        )
        self.open_reviewed_file_button.setEnabled(
            self._last_reviewed_file_path is not None and self._last_reviewed_file_path.exists()
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

    def _open_review_summary_file(self) -> None:
        if self._last_review_summary_path is None or not self._last_review_summary_path.exists():
            QMessageBox.information(self, "尚無待複核報表", "目前沒有可開啟的待複核報表。")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_review_summary_path)))

    def _open_apply_summary_file(self) -> None:
        if self._last_apply_summary_path is None or not self._last_apply_summary_path.exists():
            QMessageBox.information(self, "尚無回填摘要", "目前沒有可開啟的回填摘要。")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_apply_summary_path)))

    def _open_reviewed_file(self) -> None:
        if self._last_reviewed_file_path is None or not self._last_reviewed_file_path.exists():
            QMessageBox.information(self, "尚無第二版文件", "目前沒有可開啟的第二版文件。")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_reviewed_file_path)))
