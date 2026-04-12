# Phase 1 Freeze 備忘錄

## 目前凍結範圍

- Phase 1A～1E 最小主幹能力。
- Phase 1 CLI。
- JSON / TXT report。
- 高風險規則預設檔名契約修正。
- `--reviewed-output` 契約收斂。
- 舊 CLI 第一版保守轉發。
- GUI Phase 1 worker 第一版接線。
- Phase 1 文件收尾。

## 目前已完成能力

- Analyze：只讀分析 `.docx`。
- Convert：最小 converted `.docx` 輸出。
- Apply Review：reviewed JSON 回填最小流程。
- Paragraph merge candidates：只偵測，不套用。
- CLI：`src.phase1_cli` 已可獨立運作。
- Report：JSON / TXT report 已可輸出。
- Legacy CLI：`src/cli_v35.py` 已可在特定旗標下保守轉發到 `src.phase1_cli`。
- GUI worker：`src/gui/phase1_worker.py` 已可直接呼叫 pipeline。

## 已收斂契約

- OpenCC 固定 `s2t`。
- 高風險詞 convert 階段不自動替換。
- paragraph merge 只產生候選，不套用。
- reviewed 回填只接受 `accepted + 非空 resolved_text`。
- 高風險規則公開預設檔名：`data/high_risk_rules.yaml`。
- 中文舊檔名 `data/高風險規則.yaml` 僅作最小 fallback。
- `--reviewed-output` 只在 apply_review 模式下有意義。
- 有 `--reviewed-output` 時，視為精確輸出檔路徑。
- `--reviewed-output` 優先於 `output_dir`。
- 精確輸出路徑已存在時報錯，不覆蓋、不自動改名。
- JSON report `success = len(schema.errors) == 0`。

## 驗證結果

- Full pytest：`137 passed`。
- `verify_v2.bat`：passed。
- `verify_v2.ps1`：passed。
- requirements install：passed。

## 本次 freeze 不包含

- GUI 主視窗完整整合。
- TOC 寫入。
- paragraph merge 套用。
- chapter candidate 套用。
- run-level 格式保真。
- 舊入口完整替換。
- GUI reviewed JSON 編輯器。
- Excel / HTML report。

## 仍保留為後續任務

- `app.py` 是否維持純路由器角色的正式決策。
- `src/cli_v35.py` 是否要進一步擴張轉發範圍。
- GUI 主視窗最小接線。
- TOC 規劃。
- run-level 格式保真評估。

## 建議 commit message

`Freeze Phase 1 verified mainline`

## 建議 tag

`v1.0-phase1-freeze`
