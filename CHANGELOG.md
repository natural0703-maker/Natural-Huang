# Changelog

## [V3.6] - 2026-04-05
### Added
- 新增 profile 設定模型，`config.yaml` 可定義 `profiles` 與 `active_profile`，每個 profile 支援 `low_risk_dict`、`high_risk_rules`、`format_config`、`description`。
- CLI 新增 `--profile` 參數，可在單次執行時覆蓋設定檔的 `active_profile`。
- GUI 新增 profile 下拉選單與 profile 資訊顯示，執行時會帶入目前選定 profile。
- 新增測試 `tests/test_profile_config_v36.py`、`tests/test_gui_profile_worker_v36.py`，覆蓋 profile 載入、錯誤處理、CLI 切換與 GUI worker 參數傳遞。

### Changed
- `load_config` 新增 profile 解析與向後相容邏輯：舊版無 profiles 的 config 仍自動映射為 `default` profile。
- `run_processing` / `run_apply_review` 支援 `profile` 參數，並在處理結果中回傳 `active_profile` 與 `available_profiles`。
- GUI 成功摘要 payload 擴充 profile 相關欄位，並同步顯示目前實際生效的方案。

### Fixed
- 修正舊版 config 置於臨時目錄時，預設高風險規則路徑可能錯解到不存在位置的相容性問題。
- 修正 profile 指向缺檔或規則格式異常時缺乏明確錯誤來源的問題，錯誤訊息改為包含 profile 名稱與檔案角色。
- 修正 GUI 執行前刷新 profile 時可能覆蓋使用者已選 profile 的問題，改為優先保留目前選擇（若仍有效）。

### Docs
- README 新增 V3.6 說明：profile 概念、`active_profile`、CLI `--profile` 用法、GUI 切換方式、相容性與限制。

## [V3.5] - 2026-04-05
### Added
- 新增 `data/high_risk_rules.yaml`，將高風險詞規則資料化，支援 `term`、`risk_category`、`enabled`、`suggested_candidates`、`note` 欄位。
- 新增 `data/term_dict_v35.yaml`，提供可維護的低風險詞庫新版格式範例，支援 `source`、`target`、`risk_level`、`enabled`、`category`、`note`。
- 新增 `src/rule_loader.py`，集中處理低風險/高風險規則載入、欄位驗證、重複規則檢查與啟用狀態過濾。
- 新增 CLI 參數 `--high-risk-rules`，可在執行時指定高風險規則檔。
- 新增 GUI 規則資訊顯示：低風險詞庫路徑、高風險規則路徑、啟用規則數量、config 路徑。
- 新增測試 `tests/test_rule_loader_v35.py`、`tests/test_processing_rules_v35.py`，覆蓋規則檔向後相容與生效行為。

### Changed
- `run_processing` 改為由規則檔驅動低風險與高風險規則來源，CLI/GUI 共用同一套載入流程。
- `risk_detector` 支援注入高風險 `terms/category_map/suggestion_map`，不再只能依賴硬編碼映射。
- `config.yaml` 新增 `default_high_risk_rules_path`，並將預設低風險詞庫指向 `data/term_dict_v35.yaml`。
- GUI 視窗標題更新為 V3.5，並新增高風險規則檔案選擇欄位。

### Fixed
- 修正規則來源分散導致 CLI/GUI 與核心規則狀態不易追蹤問題，改為集中在 `rule_loader` 管理。
- 修正高風險規則檔缺失時可能悄悄回退造成誤判的風險；當使用者顯式指定不存在規則檔時，改為明確拋錯。
- 修正 GUI 成功 payload 缺少規則來源與啟用數量資訊的問題。

### Docs
- README 補充 V3.5 規則檔格式、向後相容策略、config 指定方式與 GUI 規則資訊區塊說明。

## [V3.3] - 2026-04-05
### Added
- `review_candidates` 新增 `candidate_id`、`chapter_guess`、`position_hint`、`resolved_text` 欄位，並保持既有欄位相容。
- 新增 `review_summary.xlsx` 專用待複核報表，輸出人工複核需要的核心欄位。
- GUI 新增「開啟待複核報表」按鈕，可直接開啟 `review_summary.xlsx`。

### Changed
- `review_candidates` 輸出順序改為依 `file_name`、`paragraph_index`、`candidate_id` 穩定排序。
- GUI 完成摘要新增高風險分類統計（`grammar` / `wording` / `regional_usage`）與高風險較多檔案提示。
- `summary` 工作表新增高風險分類統計欄位：`review_grammar_count`、`review_wording_count`、`review_regional_usage_count`。

### Fixed
- 修正高風險候選追蹤資料不足問題，改為每筆候選都可追溯到段落位置與章節推測。
- 修正 GUI 成功 payload 缺少待複核報表路徑與高風險分類統計的問題。

### Docs
- README 補充 V3.3 高風險人工複核工作流、`review_summary.xlsx` 用途與欄位說明。

## [V3.2] - 2026-04-05
### Added
- `document_format` 設定區塊，支援頁邊界、字體、字級、段落間距、行距、首行縮排、標題樣式等格式參數。
- GUI 新增文件格式覆寫入口，可設定內文字體、內文字級、首行縮排、段後距離、邊界、標題樣式。

### Changed
- 文件格式套用改為 config 驅動，CLI 與 GUI 共用同一套格式規則。
- 保留 V3.1 預設格式作為 fallback，避免舊設定缺欄位時行為改變。

### Fixed
- 修正格式參數缺失時可能造成輸出不一致的問題，未提供欄位時回退到穩定預設值。

### Docs
- README 新增可配置格式欄位說明、GUI 格式設定說明、章節導覽能力說明。

## [V3.1] - 2026-04-05
### Added
- 新增正文段落格式標準化：新細明體 12 pt、段前 0 pt、段後 6 pt、最小行高 12 pt。
- 新增頁面邊界標準化：上/下/左/右皆為 1.27 cm。
- 新增正文首行縮排規則：以 2 字元等效長度套用第一行縮排。

### Changed
- 章節標題段落統一套用 `Heading 2`（或等效可用樣式）。
- 章節標題判定採文字規則優先，格式特徵僅作輔助訊號。

### Fixed
- 修正短句誤判為章節標題的風險，僅直接規則命中時套用標題樣式。
- 修正 Word 樣式語系差異造成的不穩定，加入樣式回退策略（例如 `Normal`）。

### Docs
- README 補充章節判定規則、格式訊號為輔的理由、樣式語系差異處理策略。

## [V3.0] - 2026-04-05
### Added
- 高風險詞分類機制：`grammar`、`wording`、`regional_usage`。
- `review_candidates` 工作表新增 `risk_category`、`original_snippet`、`processed_snippet`、`status`、`note`。
- GUI 完成摘要新增高風險候選總數與異常字元總數顯示。

### Changed
- 高風險偵測輸出改為提供人工複核上下文，不參與自動替換。
- 詞庫結構擴充為可相容舊 mapping 與可擴充欄位格式（`source/target/risk_level/enabled/note`）。

### Fixed
- 修正低風險替換與高風險詞可能衝突的問題，明確排除高風險詞條。

### Docs
- README 補充高風險分類意義與 `review_candidates` 欄位用途。

## [V2.2.1] - 2026-04-05
### Added
- 驗證流程固定建立並使用專案內暫存目錄：`.tmp`、`.pytest_tmp`。
- `verify_v2.bat` 與 `verify_v2.ps1` 新增 TEMP/TMP 可用性探測步驟。

### Changed
- 驗證腳本統一將 TEMP/TMP 指向 `.tmp/runtime`。
- `pytest` 驗證改為固定使用 `--basetemp=.pytest_tmp`。

### Fixed
- 修正驗證流程依賴系統 TEMP 導致的路徑不穩與清理失敗問題。

### Docs
- README 新增專案內 temp 治理策略與執行方式說明。

## [V2.2] - 2026-04-05
### Added
- 新增 `verify_v2.ps1`，提供 PowerShell 一鍵驗證流程。
- `verify_v2.bat` 新增 smoke test 關鍵輸出存在性檢查。

### Changed
- 驗證腳本先產生測試資料再執行 pytest 與 smoke test。
- 批次驗收摘要改為區分「預期檔級失敗」與「整體流程失敗」。

### Fixed
- 修正 `verify_v2.ps1` 以 exit code 誤判 batch/recursive 結果的問題。

### Docs
- README 新增 `verify_v2.bat` / `verify_v2.ps1` 用法與驗證範圍說明。

## [V2.1] - 2026-04-04
### Added
- 新增 pytest：非 `.docx` 批次忽略、壞檔進 failures、OpenCC 預設 `s2t`、五工作表存在。

### Changed
- README 主體改為繁體中文，補齊 CLI/批次/recursive/config/詞庫/報表說明。
- CLI 錯誤訊息統一為繁體中文風格。

### Fixed
- 修正測試收集時 `src` 匯入問題（補 `src/__init__.py` 與 `pytest.ini` 設定）。

### Docs
- README 明確標註 OpenCC 預設 `s2t` 與原因（避免簡轉繁階段誤動高風險詞）。

## [V2] - 2026-04-04
### Added
- 新增高風險詞偵測模組（只標記不替換）。
- 新增異常字元掃描模組（`?`、`�` 與指定不可見字元）。
- 新增批次處理與子資料夾遞迴支援（`--input-dir`、`--recursive`）。
- 報表新增工作表：`review_candidates`、`anomalies`、`failures`。

### Changed
- pipeline 擴充為：簡轉繁 → 低風險替換 → 空格清理 → 高風險偵測（只讀）→ 異常掃描（只讀）→ 輸出。
- 批次模式改為單檔失敗不中斷，整批繼續處理。

### Fixed
- 修正高風險詞被誤替換問題，改為全程只偵測與報告。

### Docs
- README 新增高風險與異常掃描說明、批次處理說明與 V2 限制。

## [V1] - 2026-04-03
### Added
- 建立 CLI 單檔 `.docx` 處理流程（`--input-file/--input`、`--output-dir`）。
- 新增 OpenCC 簡轉繁、低風險詞替換、空格清理。
- 新增輸出命名規則（`_TW`、`_001` 續號）與 Excel 報表（`summary`、`replacements`）。
- 建立基本 pytest 測試集。

### Changed
- 低風險替換採最長詞優先，重疊詞以較長詞條優先。

### Fixed
- 強化輸入驗證：不存在檔案、非 `.docx`、讀寫失敗提供明確錯誤。

### Docs
- README 建立專案目的、安裝方式、CLI 用法、設定檔與已知限制。
