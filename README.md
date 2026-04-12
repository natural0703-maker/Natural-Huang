# DOCX 簡轉繁處理工具（V2.2）

## 一、專案目的
本專案是 Windows 本地端執行的 Python CLI 工具，用於處理小說 `.docx` 正文段落，提供可追蹤、低風險的文字轉換與檢測流程。

核心目標：
1. 簡體中文轉繁體中文（OpenCC）
2. 低風險詞替換（可擴充詞庫）
3. 空格清理
4. 高風險詞標記（不直接修改）
5. 異常字元掃描（不直接修改）
6. 輸出轉換後 `.docx` 與 `report.xlsx`

## 二、支援範圍
1. 支援單一 `.docx` 檔案處理
2. 支援資料夾批次處理
3. 支援子資料夾遞迴掃描（`--recursive`）
4. 批次模式單檔失敗不中斷，失敗寫入 `failures` 工作表
5. 只處理 `.docx` 正文段落文字

## 三、不支援範圍
1. GUI 詞庫逐筆編輯器（目前 GUI 為執行控制與摘要顯示）
2. `.doc` 檔案
3. 段落合併
4. 問號自動修復
5. 詞庫編輯器
6. Windows `.exe` 打包
7. OCR

## 四、安裝方式
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 五、CLI 用法
```bash
python app.py --input-file "D:\novel.docx" --output-dir "D:\output"
```

參數說明：
- `--input-file`：單一 `.docx` 輸入路徑
- `--input`：`--input-file` 相容別名
- `--input-dir`：資料夾輸入路徑（批次）
- `--recursive`：遞迴掃描 `--input-dir` 子資料夾內 `.docx`
- `--output-dir`：輸出資料夾（不存在會自動建立）
- `--config`：設定檔路徑
- `--term-dict`：低風險詞庫路徑
- `--report-name`：報告檔名（預設 `report.xlsx`）

規則：
1. `--input-file/--input` 與 `--input-dir` 二選一
2. 非 `.docx` 檔案在資料夾模式會被忽略，不計入 failures
3. 真正處理失敗的 `.docx` 才會記錄到 failures

## 六、單檔處理範例
```bash
python app.py --input-file "D:\novel.docx" --output-dir "D:\output"
```

## 七、批次處理範例
```bash
python app.py --input-dir "D:\novels" --output-dir "D:\output"
```

## 八、recursive 用法範例
```bash
python app.py --input-dir "D:\novels" --recursive --output-dir "D:\output"
```

## 九、config.yaml 說明
預設使用根目錄 `config.yaml`：

```yaml
# OpenCC 預設使用 s2t（僅做簡轉繁，不直接導入台灣用詞替換）
# 原因：避免在簡轉繁階段誤動到高風險詞，統一由後續檢測流程處理
opencc_config: s2t
default_report_name: report.xlsx
default_term_dict_path: data/term_dict.yaml
enable_space_cleanup: true
```

欄位說明：
- `opencc_config`：OpenCC 設定，預設 `s2t`
- `default_report_name`：報告檔名預設值
- `default_term_dict_path`：低風險詞庫預設路徑
- `enable_space_cleanup`：是否啟用空格清理

## 十、詞庫檔格式說明
檔案：`data/term_dict.yaml`

格式：YAML key-value（來源詞 -> 目標詞）

```yaml
"\u8f6f\u4ef6": "\u8edf\u9ad4"
"\u6587\u6863": "\u6587\u4ef6"
"\u670d\u52a1\u5668": "\u4f3a\u670d\u5668"
"\u5c4f\u5e55": "\u87a2\u5e55"
"\u9f20\u6807": "\u6ed1\u9f20"
```

注意：
1. 低風險替換會自動排除高風險詞條
2. 高風險詞只做偵測，不進行替換

## 十一、Excel 報告工作表說明
報告包含 5 個工作表：

### 1. summary
欄位：
- `file_name`
- `paragraph_count`
- `total_replacements`
- `total_review_candidates`
- `total_anomalies`
- `status`
- `elapsed_time_sec`
- `output_file`

### 2. replacements
欄位：
- `file_name`
- `paragraph_index`
- `original_snippet`
- `replaced_term`
- `target_term`
- `replacement_count`

### 3. review_candidates
欄位：
- `file_name`
- `paragraph_index`
- `hit_term`
- `context_snippet`
- `suggested_candidates`
- `confidence`

### 4. anomalies
欄位：
- `file_name`
- `paragraph_index`
- `anomaly_char`
- `original_snippet`
- `converted_snippet`

### 5. failures
欄位：
- `file_name`
- `error_type`
- `error_message`

## 十二、pytest 執行方式
```bash
python -m pytest -q
```

## 十三、一鍵驗證腳本（verify_v2.bat / verify_v2.ps1）
### A. verify_v2.bat
在 Windows `cmd` 或 PowerShell 執行：

```bat
verify_v2.bat
```

### B. verify_v2.ps1
在 PowerShell 執行：

```powershell
powershell -ExecutionPolicy Bypass -File .\verify_v2.ps1
```

兩個腳本都會自動執行：
1. 建立/更新 smoke test 測試資料（`tests/tools/generate_v2_test_data.py`）
2. 建立專案內暫存目錄 `.tmp` 與 `.pytest_tmp`，並固定 TEMP/TMP 到 `.tmp/runtime`（每次重建）
3. 執行 `pytest -vv -s --basetemp=<專案路徑>\.pytest_tmp`（失敗即中止）
4. 清理 `tests/out_single` 與 `tests/out_batch`
5. 單檔 smoke test
6. 批次 smoke test（不加 recursive）
7. 批次 smoke test（加 recursive）
8. 檢查關鍵輸出檔是否存在並輸出摘要

為什麼固定使用專案內暫存目錄：
1. 避免系統全域 TEMP/TMP 路徑被其他程式或權限策略干擾
2. 避免暫存檔散落到系統路徑，便於清理與追蹤
3. 降低 pytest 清理暫存時的不穩定性

腳本重點驗證：
- `single_ok_TW.docx`、`report.xlsx` 是否產生
- 批次報告 `tests/out_batch/report.xlsx` 是否存在
- recursive 後 `sub_test_TW*.docx` 是否存在

深度內容驗證仍由 pytest 負責（例如）：
- `bad.docx` 是否進 failures
- `ignore.txt` 是否被忽略且不進 failures
- 高風險詞不直接修改
- 報告五個工作表存在

## 十四、測試資料結構
`tests/tools/generate_v2_test_data.py` 會建立以下資料：

```text
tests/data/
├─ single_ok.docx
└─ batch_input/
   ├─ normal_1.docx
   ├─ risk_terms.docx
   ├─ anomaly.docx
   ├─ bad.docx
   ├─ ignore.txt
   └─ subfolder/
      └─ sub_test.docx
```

## 十五、已知限制
1. GUI 為第一版，僅提供基本操作與執行控制，不含進階檢視與編輯能力。
2. 不處理 `.doc`
3. 不提供段落合併
4. 不做問號自動修復
5. 不提供詞庫編輯器
6. 不提供 exe 打包

## 十六、GUI 啟動方式（V1）
GUI 使用 PySide6，為既有核心流程的控制介面，不重寫轉換邏輯。

啟動方式：

```bash
python app.py --gui
```

## 十七、GUI 功能說明
GUI 第一版提供：
1. 單一 `.docx` 檔案選擇
2. 輸入資料夾選擇（批次）
3. 輸出資料夾選擇
4. `recursive` 勾選
5. `config.yaml` 路徑選擇
6. 詞庫 YAML 路徑選擇
7. 開始執行按鈕
8. 執行進度與狀態顯示
9. 完成後成功/失敗統計
10. 開啟輸出資料夾
11. 開啟報告檔（report.xlsx）

## 十八、GUI 與 CLI 差異
1. CLI 適合自動化與腳本整合。
2. GUI 適合人工操作與快速檢查執行結果。
3. 兩者都共用相同核心處理模組（讀檔、轉換、替換、風險檢測、異常掃描、輸出、報表）。
4. GUI 只負責參數輸入與執行控制，不另寫一套轉換邏輯。

## 十九、GUI 操作範例
1. 啟動 `python app.py --gui`。
2. 選擇「單檔模式」並指定 `.docx`、輸出資料夾。
3. 按「開始執行」。
4. 完成後可按「開啟報告」查看 `report.xlsx`。

批次與 recursive：
1. 切換到「資料夾批次模式」。
2. 選擇輸入資料夾、輸出資料夾。
3. 需要時勾選 recursive。
4. 按「開始執行」。

## 二十、GUI 已知限制
1. 不提供詞庫編輯器。
2. 不提供高風險詞互動式人工複核介面。
3. 不提供報表內嵌預覽表格。
4. 不提供差異比對視窗。
5. 不提供 `.doc` 支援。
6. 不提供 exe 打包。

## 二十一、GUI 仍依賴既有核心驗證流程
1. GUI 的處理結果依然建議透過 `pytest`、`verify_v2.bat`、`verify_v2.ps1` 驗證。
2. GUI 不是替代測試框架，而是操作入口。

## 二十二、V3.0 高風險複核與報表強化
### 1. 高風險詞分類
V3.0 將高風險詞分成三類，僅供人工複核，不做自動改寫：
- `grammar`：`的`、`得`、`地`
- `wording`：`信息`、`訊息`、`資訊`、`視頻`、`影片`、`視訊`、`支持`、`優化`、`質量`
- `regional_usage`：`裡`、`裏`、`於`、`在`

### 2. review_candidates 新欄位
`review_candidates` 工作表至少包含以下欄位：
- `file_name`
- `paragraph_index`
- `hit_term`
- `risk_category`
- `original_snippet`
- `processed_snippet`
- `context_snippet`
- `suggested_candidates`
- `confidence`
- `status`
- `note`

欄位用途：
- `status`：人工複核狀態，預設 `pending`
- `note`：人工複核備註，預設空白

### 3. GUI 完成摘要（V3.0）
GUI 執行完成後會顯示：
- 成功檔案數
- 失敗檔案數
- 低風險替換總次數
- 高風險候選總數
- 異常字元總數

### 4. 詞庫格式向後相容
目前支援兩種格式：
1. 舊版 mapping（`source -> target`）
2. 擴充 list 格式（可含 `source`、`target`、`risk_level`、`enabled`、`note`）

擴充格式中：
- `enabled: false` 會被忽略
- `risk_level: high` 會被忽略（高風險詞不進低風險替換）

### 5. V3.0 仍不處理事項
1. 高風險詞自動修正（例如 `的/得/地` 自動文法判斷）
2. `.doc` 支援
3. 問號/缺字/亂碼自動修復
4. GUI 詞庫編輯器
5. 高風險詞逐筆互動複核介面
6. exe 打包

## 二十三、V3.1 文件格式標準化
### 1. 內文格式規則
所有「非章節標題」段落輸出時統一為：
1. 字體：新細明體
2. 字級：12 pt
3. 樣式策略：優先套用「內文/本文」，若目標環境無該樣式則回退為 `Normal`（或語系等效樣式）

### 2. 章節標題格式規則
所有被「直接判定」為章節標題的段落，輸出時統一套用：
1. `Heading 2` / `標題 2` 樣式（依 Word 環境可用樣式）
2. 字體仍統一套用新細明體 12 pt

### 3. 章節標題判定規則（文字規則為主）
直接判定條件：
1. 開頭符合 `第...章` / `第...節` / `第...回`（`...` 可為中文數字或阿拉伯數字），後續可接空格、全形空格、冒號與章名
2. 全段文字屬白名單：`序章`、`楔子`、`終章`、`後記`、`番外`、`尾聲`

### 4. 為何格式訊號只作輔助
短句、置中、粗體、大字級等格式特徵容易誤判一般段落，因此 V3.1 不以這些訊號單獨判定章節標題，只採文字規則直接判定，降低誤判風險。

### 5. Word 樣式語系差異處理策略
不同 Word 語系下樣式名稱可能不同，實作上採「多名稱候選 + 回退策略」：
1. 標題優先 `標題 2`，次選 `Heading 2`
2. 內文優先 `內文/本文`，無法使用時回退 `Normal/標準`
3. 即使樣式名稱不同，仍會強制套用新細明體 12 pt，避免輸出失敗

### 6. 頁面與段落格式（V3.1 新增）
1. 頁面邊界統一為：上/下/左/右 `1.27 cm`
2. 非章節標題段落：
   - 字體：新細明體
   - 字級：12 pt
   - 樣式：內文（不可用時回退 Normal/等效樣式）
   - 與前段距離：0 pt
   - 與後段距離：6 pt（約 0.5 行）
   - 行距：最小行高 12 pt（At Least 12 pt）
3. 被直接判定的章節標題段落：套用 `標題 2 / Heading 2`

## 二十四、V3.2 格式規則可配置化與章節導覽
### 1. 可配置格式欄位（config.yaml）
`document_format` 支援以下欄位：
- `page_margin_top_cm`
- `page_margin_bottom_cm`
- `page_margin_left_cm`
- `page_margin_right_cm`
- `body_font_name`
- `body_font_size_pt`
- `body_space_before_pt`
- `body_space_after_pt`
- `body_line_spacing_mode`
- `body_min_line_height_pt`
- `body_first_line_indent_chars`
- `heading_style_name`
- `insert_toc`（預設關閉）

若未提供上述欄位，系統會回退到 V3.1 已驗證的預設值。

### 2. 章節導覽能力
章節標題段落會套用 `Heading 2/標題 2`（可由 `heading_style_name` 覆蓋），以便 Word 導覽窗格辨識章節結構。
本版本不預設插入目錄頁。

### 3. GUI 格式設定入口
GUI 新增「Document Format Overrides」區塊，可設定：
- 內文字體
- 內文字級
- 第一行縮排字元數
- 段後距離
- 邊界（統一邊界）
- 章節標題樣式名稱

GUI 只做設定輸入，仍呼叫同一套核心 pipeline，CLI 與 GUI 輸出規則一致。

## 二十五、V3.3 高風險人工複核工作流
### 1. `review_candidates` 新增欄位
V3.3 在既有欄位上新增（且保持相容）：
1. `candidate_id`：每筆候選唯一識別碼（穩定、可追蹤）
2. `chapter_guess`：推測章節（若無法判斷可空白）
3. `position_hint`：段落位置提示
4. `resolved_text`：人工複核後可填寫結果

### 2. `review_summary.xlsx`（待複核專用報表）
每次執行除 `report.xlsx` 外，會額外產生 `review_summary.xlsx`，用於人工複核彙整。

欄位包含：
- `candidate_id`
- `file_name`
- `chapter_guess`
- `paragraph_index`
- `hit_term`
- `risk_category`
- `context_snippet`
- `suggested_candidates`
- `confidence`
- `status`
- `note`
- `resolved_text`

### 3. GUI 高風險摘要強化
GUI 執行完成後會顯示：
1. 高風險候選總數
2. 各分類數量（`grammar` / `wording` / `regional_usage`）
3. 高風險較多的檔案（簡要清單）
4. 可透過「開啟待複核報表」直接開啟 `review_summary.xlsx`

### 4. 本輪仍不做
1. 高風險詞自動修正
2. GUI 逐筆互動式複核編輯器
3. GUI 直接回寫 Word 內容
4. `.doc` 支援

## 二十六、V3.4 人工複核回填與二次輸出
### 1. 回填規則
`review_summary` 的欄位語意如下：
1. `status`：支援 `pending` / `accepted` / `rejected` / `skip`
2. `resolved_text`：人工確認後要回填的文字
3. `note`：人工備註

只有同時符合下列條件才會真正改動第二版文件：
1. `status = accepted`
2. `resolved_text` 非空白

其餘狀態（`pending` / `rejected` / `skip`）一律不改動文件內容。

### 2. CLI 套用複核結果
可使用既有輸入參數搭配 `--apply-review-summary`：

```bash
python app.py --input-file "D:\output\novel_TW.docx" --output-dir "D:\output" --apply-review-summary "D:\output\review_summary.xlsx"
```

批次模式：

```bash
python app.py --input-dir "D:\output" --output-dir "D:\output" --apply-review-summary "D:\output\review_summary.xlsx"
```

### 3. 第二版命名規則
回填後文件不覆蓋第一版，命名為：
1. `原檔名_reviewed.docx`
2. 若重名則遞增：`原檔名_reviewed_001.docx`、`_002`…

### 4. 回填定位策略（保守）
回填以 `file_name`、`paragraph_index`、`hit_term`、`context_snippet`、`candidate_id` 進行保守定位：
1. 段落索引不存在：跳過並記錄 `not_found`
2. 同段落同詞多次命中：視為 `conflict`，不做模糊替換
3. 定位不確定時一律跳過，不中斷整批

### 5. 回填摘要
每次回填會輸出 `apply_summary.xlsx`，包含：
1. `apply_summary`：每檔總候選、實際套用、跳過、找不到、衝突、失敗
2. `apply_details`：每筆候選的套用結果與原因
3. `apply_failures`：例外失敗資訊

### 6. GUI 套用複核結果
GUI 新增：
1. 選擇 `review_summary.xlsx/.csv`
2. 「套用複核結果」按鈕
3. 顯示套用摘要（套用數、跳過數、失敗數）
4. 開啟 `apply_summary.xlsx`
5. 開啟第二版輸出文件

### 7. 本輪仍不做
1. 高風險詞自動修文（例如 的/得/地）
2. AI 自動填入 `resolved_text`
3. GUI 逐筆編輯器
4. 一鍵接受全部建議

## 二十七、V3.5 詞庫管理與規則維護
### 1. 低風險詞庫新格式（向後相容）
V3.5 支援兩種低風險詞庫格式：
1. 舊版 mapping（相容）
2. 新版 list（建議）

新版 list 欄位：
- `source`
- `target`
- `risk_level`
- `enabled`
- `category`
- `note`

範例（`data/term_dict_v35.yaml`）：
```yaml
- source: 软件
  target: 軟體
  risk_level: low
  enabled: true
  category: tech
  note: 預設低風險替換
```

相容性說明：
1. 舊版 mapping 仍可讀取。
2. `enabled: false` 會忽略該規則。
3. `risk_level: high` 不會進入低風險替換流程。

### 2. 高風險規則檔格式
V3.5 將高風險詞規則資料化，預設檔案為 `data/high_risk_rules.yaml`。

欄位：
- `term`
- `risk_category`（`grammar` / `wording` / `regional_usage`）
- `enabled`
- `suggested_candidates`
- `note`

範例：
```yaml
- term: 的
  risk_category: grammar
  enabled: true
  suggested_candidates: 請依語境確認「的/得/地」
  note: 文法高風險詞，僅標記
```

注意：
1. 高風險詞仍只做偵測與報告，不會直接改寫輸出文字。
2. `enabled: false` 的高風險規則不生效。

### 3. 規則檔載入與驗證
V3.5 新增規則驗證機制，包含：
1. 缺少必要欄位（例如 `source/target`、`term`）會報錯。
2. 重複啟用規則（低風險同 `source`、高風險同 `term`）會報錯。
3. 無效分類（高風險 `risk_category` 非三種合法值）會報錯。
4. 錯誤訊息以繁體中文為主。

### 4. 透過 config 指定規則檔
`config.yaml` 可指定：
- `default_term_dict_path`
- `default_high_risk_rules_path`

預設示例：
```yaml
opencc_config: s2t
default_report_name: report.xlsx
default_term_dict_path: data/term_dict_v35.yaml
default_high_risk_rules_path: data/high_risk_rules.yaml
enable_space_cleanup: true
```

也可透過 CLI 覆蓋：
```bash
python app.py --input-file "D:\novel.docx" --output-dir "D:\out" --term-dict "D:\rules\low.yaml" --high-risk-rules "D:\rules\high.yaml"
```

### 5. GUI 規則資訊區塊
GUI 新增規則資訊顯示（僅顯示、不編輯）：
1. 目前低風險詞庫路徑
2. 目前高風險規則檔路徑
3. 啟用中的低風險詞數量
4. 啟用中的高風險詞數量
5. 目前使用的 config 路徑（若未指定則顯示預設）

### 6. 本輪仍不做
1. GUI 詞庫逐筆編輯器
2. 高風險詞自動接受
3. AI 自動生成規則
4. 文法模型判斷
5. `.doc` 支援

## 二十八、V3.6 規則方案切換與預設檔管理
### 1. Profile 概念與用途
V3.6 新增「規則方案（profile）」概念，可把同一套流程的規則來源分組管理。  
每個 profile 至少包含：
1. `low_risk_dict`
2. `high_risk_rules`
3. `format_config`
4. `profile name`（由 key 或 `profile_name` 定義）
5. `description`（可選）

### 2. `active_profile` 設定方式
在 `config.yaml` 可指定目前預設方案：

```yaml
active_profile: default
profiles:
  default:
    description: 預設規則方案
    low_risk_dict: data/term_dict_v35.yaml
    high_risk_rules: data/high_risk_rules.yaml
    format_config:
      body_font_size_pt: 12
```

若未指定 `profiles`，系統會自動建立相容舊版的 `default` profile。  
若未指定 `active_profile`，預設使用 `default`。

### 3. CLI 如何指定 profile
CLI 新增 `--profile`：

```bash
python app.py --input-file "D:\novel.docx" --output-dir "D:\out" --config "D:\config.yaml" --profile strict_tw
```

行為：
1. 指定 `--profile` 時，該次執行以指定方案為準。
2. 若 profile 不存在，會回傳明確繁體中文錯誤訊息。
3. 未指定時，使用 `config.yaml` 的 `active_profile`。

### 4. GUI 如何切換 profile
GUI 新增「規則方案（Profile）」下拉選單：
1. 顯示目前 active profile。
2. 可切換可用 profile。
3. 執行時會帶入本次選定 profile。
4. 完成後摘要會顯示實際啟用的 profile 與規則來源。

### 5. Profile 驗證機制
V3.6 會在載入設定時驗證：
1. `active_profile` 是否存在。
2. profile 名稱是否重複（list 格式時）。
3. profile 指向的低風險詞庫 / 高風險規則檔是否存在。
4. 規則檔格式是否合法（沿用既有規則驗證）。

### 6. 向後相容說明
1. 舊版 config（無 `profiles`）仍可使用。
2. 舊版低風險詞庫 mapping 仍可使用。
3. 高風險詞仍「只標記、不直接改寫」。
4. OpenCC 預設仍為 `s2t`。

### 7. 本輪仍不做
1. GUI 內建立/刪除/編輯 profile。
2. GUI 詞庫逐筆編輯器。
3. 高風險詞自動接受或自動修文。
4. `.doc` 支援。
