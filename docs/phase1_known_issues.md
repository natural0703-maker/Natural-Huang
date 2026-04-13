# Phase 1 已知問題

本文件記錄 Phase 1 目前已知但未在本輪處理的項目、已知技術債，以及已收斂的問題。這些項目應另開修正任務處理，不應在文件收尾中順手修改功能行為。

## 1. 已知未解問題

### 1.1 `app.py` 尚未直接整合新主幹

`app.py` 目前仍維持 GUI / CLI 路由角色，尚未直接整合 Phase 1 新主幹流程。

### 1.2 `src/cli_v35.py` 僅完成第一版保守轉發

`src/cli_v35.py` 已在 `--json-report`、`--txt-report`、`--apply-review` 出現時保守轉發到 `src.phase1_cli`，但尚未全面改為 Phase 1 CLI 流程。

### 1.3 GUI 主視窗仍未完成完整 GUI 整合

GUI 主視窗第一版已完成最小接線，可最小操作 Phase 1 的 analyze / convert / apply_review。

目前仍未支援：

- report path 欄位。
- TOC GUI 操作。
- chapter candidate / paragraph merge 套用的 GUI 操作。
- reviewed JSON 編輯器。
- batch / recursive。
- Excel report。
- 多頁籤或完整 GUI 重構。

### 1.4 進階 TOC 行為尚未實作

Phase 2C 已完成 convert 流程的 TOC 最小方案，Phase 2D-1 已完成 apply_review 流程的 TOC 支援，Phase 2D-2 已完成 report TOC 狀態摘要，Phase 2D-3 已完成 GUI TOC 狀態摘要顯示；但尚未支援 TOC GUI 操作、既有 TOC 更新 / 合併、多層目錄、頁碼更新等更完整的 TOC 行為。

### 1.5 paragraph merge 後續 GUI 與詳細診斷仍未完成

Phase 2E-2 已完成 paragraph merge apply 最小套用，Phase 2E-3 已完成 paragraph merge summary 與 JSON / TXT report 輸出，Phase 2E-4 已完成 GUI paragraph merge summary 顯示，Phase 2F-1 已完成 paragraph merge source mismatch diagnostics 最小統計摘要，Phase 2F-2 已完成 GUI paragraph merge diagnostics 顯示；但 GUI diagnostics controls、source mismatch detailed diagnostics panel、GUI paragraph merge controls、reviewed JSON editor 仍未完成。

### 1.6 run-level 格式保真尚未實作

Phase 1C / 1D 目前接受段內 run-level 格式可能丟失，不保證保留粗細、局部字型、超連結等細節。

### 1.7 report 仍為最小可用版本

Phase 1 report 目前只支援 JSON / TXT，Phase 2D-2 已補上 TOC 狀態摘要，但仍維持最小可用，不包含 HTML / Excel report。

## 2. Phase 1 已知技術債

### 2.1 `Phase1StubResult` 命名已不準確

`Phase1StubResult` 最初用於 Phase 1A stub，但目前 Phase 1B 到 Phase 1D 已包含實際 analyze / convert / apply_review 流程。後續若要調整，應另開小型重命名任務，不應在功能收斂或文件收尾時順手大規模重命名。

### 2.2 `ReviewSchema` 尚未導入正式版本遷移機制

Phase 2A 已完成 reviewed JSON / ReviewSchema 最小驗證契約收斂，但尚未導入正式 schema 版本遷移機制。後續若要支援跨版本 reviewed JSON 相容，應另開版本相容任務。

### 2.3 部分 `type` 欄位仍偏鬆

部分非 reviewed JSON 回填路徑的 candidate `type` 欄位仍偏字串型約定，尚未全面收斂成嚴格 enum。reviewed JSON 中不支援的字串 `type` 目前維持 candidate 級 `SKIPPED_UNSUPPORTED_TYPE`。

### 2.4 GUI 目前只完成第一版最小主視窗接線

GUI 目前已從 worker 層推進到主視窗第一版最小接線，但仍不是完整 GUI 整合。後續調整時仍必須維持 GUI 薄包裝，不得重寫 analyzer / converter / review apply / reporter 邏輯。

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

### 3.4 GUI 主視窗第一版最小接線已完成

`src/gui/main_window_clean.py` 已可透過 `src/gui/phase1_worker.py` 最小操作 analyze / convert / apply_review，並顯示純文字結果摘要與簡短錯誤訊息。

### 3.5 Phase 2A reviewed JSON / ReviewSchema 最小驗證契約已收斂

reviewed JSON 驗證已集中到可重用 helper，並支援 root object、`review_candidates` list、candidate 必要欄位與型別、`auto_accepted` 禁止規則，以及 fail-fast 流程級 error。unsupported string `type` 仍維持 candidate 級 `SKIPPED_UNSUPPORTED_TYPE`。

### 3.6 Phase 2B chapter candidate 套用基礎已完成

Phase 2B 已完成最小 chapter candidate 套用基礎：在既有 `apply_review` 流程中，`status == "accepted"` 且 `type == "chapter"` 的候選可將目標段落樣式套用為 `Heading 2`。此能力不修改段落文字、不修改段落順序、不建立 TOC，也不處理 paragraph merge 套用。

### 3.7 Phase 2C convert 流程 TOC 最小方案已完成

Phase 2C 已完成 convert 流程的 TOC 最小方案：依據既有 `Heading 2` 插入最小 Word TOC field；若 field 插入失敗，fallback 為前置章節清單。Phase 2D-1 另已將同一套 TOC builder 延伸到 `apply_review()` 流程；目前仍不處理 paragraph merge 套用，也不處理 run-level 格式保真。

### 3.8 Phase 2D-1 apply_review 流程 TOC 支援已完成

Phase 2D-1 已完成 apply_review 流程的 TOC 支援：review candidates 與 chapter candidates 套用後，沿用既有 TOC builder 插入 TOC，再儲存 reviewed 文件。field 插入失敗但 fallback 成功仍視為流程成功；只有 TOC field 與 fallback 都失敗時才回 `TOC_INSERT_FAILED`。此能力未新增 CLI / GUI 參數，也未修改 reviewed JSON schema。

### 3.9 Phase 2D-2 report TOC 狀態摘要已完成

Phase 2D-2 已完成 report TOC 狀態摘要：JSON report top-level 固定輸出 `toc`，TXT report 補上最小 TOC 摘要。`success` 契約未改，仍只由 `len(schema.errors) == 0` 決定。

### 3.10 Phase 2D-3 GUI TOC 狀態摘要顯示已完成

Phase 2D-3 已完成 GUI TOC 狀態摘要顯示：GUI 結果摘要區固定顯示 `TOC 狀態`、`TOC fallback`、`TOC 章節數`，並涵蓋 analyze / convert / apply_review。此能力不新增 TOC 控制項、不新增 report path 欄位、不新增 reviewed JSON 編輯器，也不修改核心 TOC 行為。

### 3.11 Phase 2E-1 paragraph merge schema 驗證契約已收斂

Phase 2E-1 已完成 `paragraph_merge_candidates` 的 reviewed JSON / schema 契約收斂：必要欄位、型別、`paragraph_index` / `next_paragraph_index` 相鄰關係、`type == "paragraph_merge"`、`status` 不允許 `auto_accepted` 等規則已納入 fail-fast 流程級驗證。此能力不包含 paragraph merge apply、`.docx` 內容讀寫、段落刪除或 `PARAGRAPH_MERGE_SOURCE_MISMATCH` 實際比對。

### 3.12 Phase 2E-2 paragraph merge apply 最小套用已完成

Phase 2E-2 已完成 paragraph merge apply 最小套用：在既有 `apply_review()` 流程中，`status == "accepted"` 且 `type == "paragraph_merge"` 的相鄰兩段候選可依 `previous_text.rstrip() + next_text.lstrip()` 合併，成功後刪除下一段，並依 `paragraph_index` 降序處理。此能力不自動插入空格、不做標點修正、不保證 run-level 格式保真，也不新增 GUI paragraph merge controls 或 report merge summary。

### 3.13 Phase 2E-3 paragraph merge result summary / report 輸出已完成

Phase 2E-3 已完成 paragraph merge result summary 與 JSON / TXT report 輸出：`ReviewApplyResult` 目前會帶出 `paragraph_merge_summary`，JSON report top-level 已新增 `paragraph_merge`，TXT report 已新增段落合併套用數、略過數、失敗數與結果碼摘要。此能力不包含 GUI controls、source mismatch 診斷面板或逐筆 candidate 明細 dump。

### 3.14 Phase 2E-4 GUI paragraph merge summary 顯示已完成

Phase 2E-4 已完成 GUI paragraph merge summary 顯示：GUI 結果摘要區現在會固定顯示段落合併套用數、略過數、失敗數與結果碼摘要，且固定接在 TOC 摘要後面。analyze / convert 會顯示預設 `0 / 0 / 0 / 無`，`codes` 非空時依 code 名稱排序輸出。此能力不包含 GUI paragraph merge controls、source mismatch 診斷面板、reviewed JSON 編輯器或 paragraph merge apply 核心規則變更。

### 3.15 Phase 2F-1 paragraph merge source mismatch diagnostics 最小統計摘要已完成

Phase 2F-1 已完成 paragraph merge source mismatch diagnostics 最小統計摘要：`ReviewApplyResult` 目前會帶出 `paragraph_merge_diagnostics`，可統計 `source_mismatch_count`、`next_source_mismatch_count`、`total_mismatch_count` 與最多 3 筆 `sample_candidate_ids`。JSON report top-level 已新增 `paragraph_merge_diagnostics`，TXT report 已新增 mismatch 總數、前段 mismatch、後段 mismatch 與範例候選摘要。此能力不包含 GUI diagnostics 顯示、source mismatch 詳細診斷面板、expected / actual 全文 diff、paragraph index 詳細清單或所有 candidate_id 清單輸出。

### 3.16 Phase 2F-2 GUI paragraph merge diagnostics 顯示已完成

Phase 2F-2 已完成 GUI paragraph merge diagnostics 顯示：GUI 結果摘要區現在會固定顯示段落合併 mismatch 總數、前段 mismatch、後段 mismatch 與 mismatch 範例候選，並固定接在 paragraph merge summary 後面。analyze / convert 會顯示預設 `0 / 0 / 0 / 無`，`sample_candidate_ids` 有值時以 `id1, id2` 形式顯示。此能力不包含 GUI diagnostics controls、source mismatch detailed diagnostics panel、reviewed JSON editor 或 paragraph merge apply 核心規則變更。

## 4. 驗證狀態

- 完整 pytest：`240 passed`
- `verify_v2.bat`：通過
- `verify_v2.ps1`：通過
