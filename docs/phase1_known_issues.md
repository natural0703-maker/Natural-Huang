# Phase 1 已知問題

本文件記錄 Phase 1 目前已知但未在本輪處理的項目、已知技術債，以及已收斂的問題。這些項目應另開修正任務處理，不應在文件收尾中順手修改功能行為。

## 1. 已知未解問題

### 1.1 `app.py` 尚未直接整合新主幹

`app.py` 目前仍維持 GUI / CLI 路由角色，尚未直接整合 Phase 1 新主幹流程。

### 1.2 `src/cli_v35.py` 僅完成第一版保守轉發

`src/cli_v35.py` 已在 `--json-report`、`--txt-report`、`--apply-review` 出現時保守轉發到 `src.phase1_cli`，但尚未全面改為 Phase 1 CLI 流程。

### 1.3 GUI 主視窗尚未正式接入 Phase 1 三模式操作

目前 GUI 只做到 `src/gui/phase1_worker.py` worker 層接線，既有 GUI 主視窗尚未提供 analyze / convert / apply_review 三模式操作。

### 1.4 TOC 尚未實作

Phase 1 目前尚未寫入 Word TOC field，也尚未建立前置可跳轉章節清單。

### 1.5 paragraph merge 套用尚未實作

Phase 1 目前只產生 `paragraph_merge_candidates` 候選，不實際合併段落。

### 1.6 run-level 格式保真尚未實作

Phase 1C / 1D 目前接受段內 run-level 格式可能丟失，不保證保留粗細、局部字型、超連結等細節。

### 1.7 report 仍為最小可用版本

Phase 1 report 目前只支援 JSON / TXT，且欄位維持最小可用，不包含 HTML / Excel report。

## 2. Phase 1 已知技術債

### 2.1 `Phase1StubResult` 命名已不準確

`Phase1StubResult` 最初用於 Phase 1A stub，但目前 Phase 1B 到 Phase 1D 已包含實際 analyze / convert / apply_review 流程。後續若要調整，應另開小型重命名任務，不應在功能收斂或文件收尾時順手大規模重命名。

### 2.2 `ReviewSchema` 仍是假凍結

`ReviewSchema` 目前可作為 Phase 1 review 資料結構依據，但尚未導入完整 schema 驗證器或正式版本遷移機制。後續若要把 reviewed JSON 視為穩定外部格式，應另開 schema 驗證與版本相容任務。

### 2.3 部分 `type` 欄位仍偏鬆

部分 candidate 的 `type` 欄位目前仍偏字串型約定，尚未全面收斂成嚴格 enum 或集中驗證。後續若要強化 reviewed JSON 契約，應另開欄位約束收斂任務。

### 2.4 GUI 目前只做到 worker 層整合

GUI 目前只做到 Phase 1 worker 層整合；既有 GUI 主視窗尚未提供對應操作。後續接主視窗時仍必須維持 GUI 薄包裝，不得重寫 analyzer / converter / review apply / reporter 邏輯。

## 3. 已解決事項

### 3.1 高風險規則預設檔名不一致已收斂

- 公開預設：`data/high_risk_rules.yaml`
- 中文舊檔名 `data/高風險規則.yaml` 僅作最小 fallback。
- 使用者或 profile 已明確指定路徑時，不改寫、不套 fallback。

### 3.2 `--reviewed-output` 契約已收斂

- `--reviewed-output` 有提供時，視為 apply_review 的精確輸出檔路徑。
- 精確輸出檔路徑優先於 `output_dir`。
- 精確輸出檔已存在時報錯，不覆蓋、不自動改名。
- 未提供時，才使用 `output_dir + {stem}_reviewed.docx` 與 `_001` 避免衝突規則。
- `--reviewed-output` 不單獨觸發 apply_review。

### 3.3 GUI worker 舊 TODO 測試衝突已清理

GUI worker 已改為直接呼叫 pipeline 並回傳 pipeline result。舊測試中期待 apply_review 回 TODO 字串的衝突已清理，GUI worker 行為集中由 `tests/test_gui_phase1_worker.py` 覆蓋。

## 4. 驗證狀態

- 完整 pytest：`137 passed`
- `verify_v2.bat`：通過
- `verify_v2.ps1`：通過
