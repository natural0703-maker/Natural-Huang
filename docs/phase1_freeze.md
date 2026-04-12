# Phase 1 Freeze 文件

本文件記錄 Phase 1A 到 Phase 1E 目前已凍結的主幹狀態。後續若要變更本文件列出的核心行為，應先另外提出規劃，不應在功能實作中順手改動。

## 1. Phase 狀態

Phase 1A 到 Phase 1E 的最小主幹能力已建立。Phase 1 目前包含只讀分析、最小轉換輸出、reviewed 回填、獨立 CLI、JSON / TXT report、舊 CLI 第一版保守轉發、GUI Phase 1 worker 薄包裝接線，以及 GUI 主視窗第一版最小操作入口。

### Phase 1A：骨架與設定基礎

- 已建立 Frozen Spec v1 必要常數。
- 已建立 `ReviewSchema` 基礎資料結構。
- 已建立 Phase 1 設定檢查流程。
- 已建立 Phase 1 pipeline、CLI、GUI worker 的平行骨架。
- GUI 仍維持薄包裝，不重寫核心 pipeline。

### Phase 1B：只讀分析

- `analyze()` 已升級為只讀 `.docx` 分析流程。
- 可讀取主文件段落文字。
- 可產生 `chapter_candidates`。
- 可產生高風險詞 `review_candidates`。
- 可產生 `paragraph_merge_candidates`，但只做候選報告。
- 不修改輸入 `.docx`。

### Phase 1C：最小轉換輸出

- `convert()` 已支援最小 converted `.docx` 輸出。
- OpenCC 預設固定使用 `s2t`。
- 低風險詞可自動替換。
- 高風險詞只偵測與報告，不自動替換。
- 若某段存在高風險候選，該段只做 OpenCC，不套用低風險詞替換。
- Phase 1C 接受段內 run-level 格式可能丟失。

### Phase 1D：reviewed 回填

- `apply_review()` 已支援 reviewed JSON 回填。
- 僅處理 `review_candidates`。
- 僅允許 `status = accepted` 且 `resolved_text` 非空白的候選套用。
- `pending`、`rejected`、`skip` 不修改文件文字。
- 不處理 `chapter_candidates`。
- 不處理 `paragraph_merge_candidates`。
- 輸出 reviewed 第二版文件，不覆蓋第一版輸出。

### Phase 1E：CLI 與 report

- `src/phase1_cli.py` 已可獨立執行 analyze / convert / apply_review。
- Phase 1 CLI 已完成目前 Frozen Spec v1 範圍內的主流程接線。
- CLI dispatch 規則已固定。
- JSON / TXT report 已由獨立 reporter 模組輸出。
- report 寫入錯誤不塞進 `schema.errors`。
- JSON report 的 `success` 固定定義為 `len(schema.errors) == 0`。

## 2. Frozen 決策

- OpenCC 預設固定為 `s2t`。
- 章節標題樣式固定使用 `Heading 2`。
- 頁面邊界固定為上、下、左、右 `1.27 cm`。
- 標題字型為新細明體 16 pt。
- 內文字型為新細明體 12 pt。
- 內文首行縮排實作值為 24 pt。
- 高風險詞固定 report-only，不直接改寫輸出文字。
- 高風險規則公開預設檔名已統一為 `data/high_risk_rules.yaml`；中文舊檔名只作最小 fallback。
- 段落合併在 Phase 1 只產生候選，不直接合併正文。
- CLI 必須可獨立運作。
- GUI 必須維持薄包裝層。
- converted 與 reviewed 輸出不得覆蓋原始檔或上一版輸出。
- `--reviewed-output` 一旦提供，即視為 apply_review 的精確輸出檔路徑，優先於 `output_dir`。
- `--reviewed-output` 不得單獨觸發 apply_review。

## 3. 主幹模組清單

- `src/frozen_spec_v1.py`：Frozen Spec v1 必要常數。
- `src/review_schema.py`：Phase 1 review schema 與 candidate id 規則。
- `src/phase1_config.py`：Phase 1 設定載入與 Frozen 值檢查。
- `src/phase1_analyzer.py`：只讀 `.docx` 分析、章節候選、高風險候選、段落合併候選偵測。
- `src/phase1_converter.py`：最小 converted `.docx` 輸出。
- `src/phase1_review_apply.py`：reviewed JSON 回填。
- `src/phase1_pipeline.py`：Phase 1 pipeline 入口。
- `src/phase1_cli.py`：Phase 1 獨立 CLI。
- `src/phase1_reporter.py`：Phase 1 JSON / TXT report 輸出。
- `src/gui/phase1_worker.py`：Phase 1 GUI worker 薄包裝接線。
- `src/gui/main_window_clean.py`：既有 GUI 主視窗與 Phase 1 三模式的第一版最小接線。

## 4. GUI Worker 狀態

- GUI Phase 1 worker 第一版已接上 pipeline。
- `src/gui/phase1_worker.py` 直接建立 `Phase1Options`，並呼叫 `analyze`、`convert`、`apply_review`。
- worker 直接回傳 pipeline result，不包裝成 dict、字串或新 wrapper。
- worker 不呼叫 CLI。
- GUI worker 目前不包含 report 路徑、TOC、chapter review、paragraph merge 套用等欄位。
- GUI 主視窗已透過 worker 執行 Phase 1 三模式操作。

## 5. GUI Main Window 狀態

- GUI 主視窗第一版最小接線已完成。
- `src/gui/main_window_clean.py` 已可最小操作 `analyze`、`convert`、`apply_review`。
- 主視窗只負責收集欄位、建立 `Phase1GuiRequest`、呼叫 `run_phase1_gui_request()`，以及顯示結果摘要與錯誤。
- 第一版主視窗仍不包含 TOC、paragraph merge 套用、report path 欄位、reviewed JSON 編輯器、batch / recursive、Excel report。

## 6. Legacy CLI Forwarding 狀態

- 舊 CLI `src/cli_v35.py` 已完成第一版保守轉發。
- 轉發條件只限 `--json-report`、`--txt-report`、`--apply-review`。
- `--reviewed-output` 不會單獨觸發轉發；只有已因其他 Phase 1 專屬參數轉發時才原樣傳入。
- `--chapter-review`、`--create-toc`、`--chapter-page-break` 第一版不作為單獨轉發條件。
- 轉發時直接呼叫 `src.phase1_cli.main(argv)`，並沿用其 exit code。

## 7. 已收斂的契約

- 高風險規則預設檔名契約已統一為 `data/high_risk_rules.yaml`。
- 未指定高風險規則路徑時，才允許對中文舊檔名 `data/高風險規則.yaml` 做最小 fallback。
- `--reviewed-output` 有提供時視為精確輸出檔路徑。
- 精確 reviewed 輸出檔已存在時報錯，不覆蓋、不自動改名。
- 未提供 `--reviewed-output` 時，才使用 `output_dir + {stem}_reviewed.docx` 與 `_001` 避免衝突規則。
- GUI worker 不再回傳 reviewed TODO 字串，改為直接回傳 pipeline result。

## 8. 明確未納入 Phase 1 的項目

- 不接入 `app.py`。
- 不直接取代 `src/cli_v35.py` 的舊流程，只做第一版保守轉發。
- 不做 GUI 主視窗完整整合或多頁籤大改版。
- 不實作 GUI 逐筆 reviewed 編輯器。
- 不實作 GUI 詞庫編輯器。
- 不實作 TOC 寫入。
- 不實作實際段落合併。
- 不新增 `.doc` 支援。
- 不保證 run-level 格式完整保真。
- 不新增 HTML / Excel report 到 Phase 1 CLI report。

## 9. 最終驗證狀態

- 完整 pytest 已通過：`144 passed`。
- `verify_v2.bat` 已通過。
- `verify_v2.ps1` 已通過。
