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

## 2. Dispatch 規則

CLI 模式由既有參數推導，不新增 `--mode`。

1. 若提供 `--apply-review`，執行 `apply_review`。
2. 否則若提供 `--output-dir`，執行 `convert`。
3. 否則執行 `analyze`。

`--reviewed-output` 只作為 reviewed 輸出路徑相關選項，不單獨觸發 `apply_review`。

## 3. Analyze 範例

```powershell
.\.venv\Scripts\python.exe -m src.phase1_cli `
  --input C:\path\to\novel.docx `
  --json-report C:\path\to\analyze_report.json `
  --txt-report C:\path\to\analyze_report.txt
```

目前 analyze 只讀取 `.docx` 並產生候選資料，不修改原檔。

## 4. Convert 範例

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

## 5. Apply Review 範例

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

## 6. JSON / TXT report

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

## 7. Exit code

- `0`：流程級 `schema.errors` 為空，且 report 寫入無錯誤。
- `1`：流程級 `schema.errors` 不為空、report 寫入錯誤，或發生未預期例外。
- `2`：CLI 參數錯誤，由 `argparse` 回傳。

report 寫入錯誤會使用固定 stderr 前綴：

```text
錯誤：{code} {message}
```

## 8. 舊 CLI 轉發現況

`src/cli_v35.py` 在下列參數出現時，會保守轉發到 `src.phase1_cli`：

- `--json-report`
- `--txt-report`
- `--apply-review`

`--reviewed-output` 不單獨觸發 Phase 1 轉發，只會在已因上述參數轉發時一併傳入。

## 9. 目前不支援 / 限制

- Phase 1 CLI 尚未接入 `app.py`。
- `src/cli_v35.py` 目前只做第一版保守轉發，未全面改為 Phase 1 CLI。
- GUI 主視窗尚未正式接入 Phase 1 三模式操作。
- 尚未支援 TOC 寫入。
- 不支援 paragraph merge 套用。
- 不支援 chapter candidate 套用。
- 尚未支援 GUI 逐筆 reviewed 編輯器。
- 不支援 GUI reviewed JSON 編輯器。
- 不支援 `.doc`。
- 不保證 run-level 格式完整保真。
- 段落合併只產生候選，不實際合併。
- 高風險詞只報告，不自動替換。
- report 目前是最小可用版本，只支援 JSON / TXT，不支援 HTML / Excel。
