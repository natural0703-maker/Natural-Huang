# Phase 1 CLI 使用說明

本文件說明 `src/phase1_cli.py` 的目前用法。此 CLI 是 Phase 1 的獨立入口；既有 `src/cli_v35.py` 已在特定 Phase 1 專屬參數下做第一版保守轉發。

## 1. 基本執行方式

在專案根目錄執行：

```powershell
.\.venv\Scripts\python.exe -m src.phase1_cli
```

也可使用目前啟用的 Python：

```powershell
python -m src.phase1_cli
```

## 2. 建議入口與相容性定位

新主幹 CLI 建議使用：

```powershell
python -m src.phase1_cli
```

GUI 主視窗定位為薄包裝層，透過 `src/gui/phase1_worker.py` 呼叫既有 pipeline；GUI 不重寫 analyzer、converter、review apply 或 reporter 邏輯。

`src/cli_v35.py` 定位為 legacy compatibility forwarder，只在明確、既有的保守條件下轉發到 `src.phase1_cli`。它保留相容性用途，不建議作為新功能的主要入口。

`app.py` 定位為 thin router / launcher，不承擔核心處理邏輯。

相容性原則：

- 現階段不刪除舊入口。
- 現階段不改舊參數語意。
- 新功能與新流程優先使用 `python -m src.phase1_cli`。

## 3. Dispatch 規則

CLI 模式由既有參數推導，不新增 `--mode`。

1. 若提供 `--apply-review`，執行 `apply_review`。
2. 否則若提供 `--output-dir`，執行 `convert`。
3. 否則執行 `analyze`。

`--reviewed-output` 只作為 reviewed 輸出路徑相關選項，不單獨觸發 `apply_review`。

## 4. Analyze 範例

```powershell
.\.venv\Scripts\python.exe -m src.phase1_cli `
  --input C:\path\to\novel.docx `
  --json-report C:\path\to\analyze_report.json `
  --txt-report C:\path\to\analyze_report.txt
```

目前 analyze 只讀取 `.docx` 並產生候選資料，不修改原檔。

## 5. Convert 範例

```powershell
.\.venv\Scripts\python.exe -m src.phase1_cli `
  --input C:\path\to\novel.docx `
  --output-dir C:\path\to\out `
  --json-report C:\path\to\convert_report.json `
  --txt-report C:\path\to\convert_report.txt
```

目前 convert 只做 Phase 1C 的最小輸出流程：

- OpenCC `s2t`。
- 低風險詞替換。
- 高風險詞偵測與報告。
- 輸出 converted `.docx`。

若某段存在高風險候選，該段只做 OpenCC，不套用低風險詞替換。

## 6. Apply Review 範例

```powershell
.\.venv\Scripts\python.exe -m src.phase1_cli `
  --input C:\path\to\novel_converted.docx `
  --output-dir C:\path\to\out `
  --apply-review C:\path\to\reviewed.json `
  --json-report C:\path\to\apply_review_report.json `
  --txt-report C:\path\to\apply_review_report.txt
```

目前 apply_review 只處理 `review_candidates`：

- 僅套用 `status = accepted`。
- `resolved_text` 必須非空白。
- `pending`、`rejected`、`skip` 不修改文件文字。
- `chapter_candidates` 與 `paragraph_merge_candidates` 不套用。

若要指定 reviewed 第二版文件的精確輸出路徑，可使用：

```powershell
.\.venv\Scripts\python.exe -m src.phase1_cli `
  --input C:\path\to\novel_converted.docx `
  --apply-review C:\path\to\reviewed.json `
  --reviewed-output C:\path\to\novel_reviewed.docx
```

`--reviewed-output` 契約：

- 有提供時，視為精確輸出檔路徑。
- 精確輸出檔路徑優先於 `output_dir`。
- 精確輸出檔已存在時報錯。
- 不覆蓋既有檔案。
- 不自動改名。
- 未提供時，才使用 `output_dir + {stem}_reviewed.docx` 與 `_001` 避免衝突規則。

## 7. JSON / TXT report

可用下列參數輸出 report：

- `--json-report`
- `--txt-report`

不指定 report 路徑時，不輸出該格式 report。

JSON report 行為：

- `success` 固定為 `len(schema.errors) == 0`。
- candidate 級 skipped / failed 不影響 `success`。
- 沒有輸出檔時，`output_path` 固定為 `null`。
- `config_check.warnings` 會輸出為 `config_warnings`。

TXT report 行為：

- 至少輸出操作、成功狀態、輸出檔案、候選數、錯誤數、設定警告數。
- 若有流程級錯誤，至少輸出第一個錯誤的 `code` 與 `message`。

JSON 與 TXT 寫入互相獨立：一者寫入失敗時，另一者仍會嘗試寫入。

## 8. Exit code

- `0`：流程級 `schema.errors` 為空，且 report 寫入無錯誤。
- `1`：流程級 `schema.errors` 不為空、report 寫入錯誤，或發生未預期例外。
- `2`：CLI 參數錯誤，由 `argparse` 回傳。

report 寫入錯誤會使用固定 stderr 前綴：

```text
錯誤：{code} {message}
```

## 9. 舊 CLI 轉發現況

`src/cli_v35.py` 是 legacy compatibility forwarder。在下列參數出現時，會保守轉發到 `src.phase1_cli`：

- `--json-report`
- `--txt-report`
- `--apply-review`

`--reviewed-output` 不單獨觸發 Phase 1 轉發，只會在已因上述參數轉發時一併傳入。

此 legacy 入口不建議作為新功能的主要入口；新功能與新流程請優先使用 `python -m src.phase1_cli`。

`src/cli_v35.py` 已補上基本 help / usage wording 與 forward-guard 防回歸測試，但仍維持保守 forwarder 定位，不是新版完整 CLI。

## 10. 目前不支援 / 限制

- `app.py` 目前定位為 thin router / launcher，不承擔核心處理邏輯。
- `src/cli_v35.py` 目前只做第一版保守轉發，未全面改為 Phase 1 CLI。
- GUI 主視窗已完成第一版最小接線，但仍不是完整 GUI 重構。
- TOC 目前僅支援 convert / apply_review 的最小方案，尚未支援進階 TOC 行為。
- paragraph merge 目前僅支援 apply_review 的最小保守套用，尚未支援 GUI controls 或進階診斷面板。
- chapter candidate 目前僅支援 accepted chapter candidate 套用為 `Heading 2`，尚未支援完整章節工作流。
- 尚未支援 GUI 逐筆 reviewed 編輯器。
- 不支援 GUI reviewed JSON 編輯器。
- 不支援 `.doc`。
- 不保證 run-level 格式完整保真。
- 段落合併只產生候選，不實際合併。
- 高風險詞只報告，不自動替換。
- report 目前是最小可用版本，只支援 JSON / TXT，不支援 HTML / Excel。
