# AGENTS.md / 代理規範

## 1) Language & Documentation / 語言與文件
- `README.md` 主體必須為繁體中文。  
  `README.md` must remain primarily in Traditional Chinese.
- `AGENTS.md` 使用逐段中英對照。  
  `AGENTS.md` must be maintained as paragraph-by-paragraph bilingual content.

## 2) Core Safety Rules / 核心安全規則
- OpenCC 預設必須維持 `s2t`。  
  OpenCC default must stay `s2t`.
- 高風險詞只允許偵測與報告，禁止直接改寫輸出文字。  
  High-risk terms are report-only and must never be directly rewritten in output text.
- GUI 必須是薄包裝層，不可重寫核心 pipeline 邏輯。  
  GUI must remain a thin wrapper and must not reimplement core pipeline logic.
- CLI 必須持續可獨立運作。  
  CLI must remain fully functional as a standalone interface.

## 3) Verification Temp Policy / 驗證暫存目錄政策
- 驗證流程固定使用專案內暫存目錄：`.tmp`、`.pytest_tmp`。  
  Verification must use project-local temp directories: `.tmp`, `.pytest_tmp`.
- 執行驗證前，應將 `TEMP/TMP` 指向專案內 `.tmp`（通常為 `.tmp/runtime`）。  
  Before verification, set `TEMP/TMP` to project-local `.tmp` (typically `.tmp/runtime`).
- `pytest` 必須搭配 `--basetemp=.pytest_tmp`。  
  `pytest` must run with `--basetemp=.pytest_tmp`.
- 不可依賴不穩定的系統 TEMP 路徑。  
  Do not rely on unstable system-wide TEMP paths.

## 4) Formatting Standards (V3.1+) / 文件格式標準（V3.1+）
- 非章節標題段落預設格式：新細明體 12 pt，段前 0 pt，段後 6 pt，最小行高 12 pt，首行縮排約 2 字元。  
  Default non-heading paragraph format: New MingLiU 12 pt, 0 pt before, 6 pt after, at-least 12 pt line height, and ~2-character first-line indent.
- 章節標題（直接規則命中）套用 `Heading 2`（或等效可用樣式）。  
  Directly detected chapter headings must use `Heading 2` (or available equivalent style).
- 頁面邊界預設為上/下/左/右 `1.27 cm`。  
  Default page margins are `1.27 cm` on all sides.

## 5) Review Workflow Rules (V3.3+) / 人工複核流程規則（V3.3+）
- `review_candidates` 與 `review_summary` 的目的是提升人工複核效率，不是自動修文。  
  `review_candidates` and `review_summary` are for human review efficiency, not automatic correction.
- `candidate_id` 必須穩定且唯一，用於追蹤。  
  `candidate_id` must be stable and unique for tracking.
- 可顯示高風險摘要與開啟待複核報表，但不可提供 GUI 逐筆編輯回寫。  
  Showing risk summary and opening review report is allowed, but GUI must not become an interactive write-back editor.

## 6) Explicit Non-Goals / 明確不做事項
- 不新增 `.doc` 支援。  
  Do not add `.doc` support.
- 不新增段落合併。  
  Do not add paragraph merging.
- 不新增高風險詞自動修正（例如「的/得/地」自動文法修正）。  
  Do not add automatic high-risk correction (e.g., auto grammar correction for 的/得/地).
- 不新增 GUI 詞庫編輯器或逐筆複核編輯器。  
  Do not add a GUI term editor or interactive per-item review editor.

## 7) Required Validation Before Completion / 完成前必跑驗證
1. `python -m pip install -r requirements.txt`  
   安裝依賴。  
   Install dependencies.
2. `pytest -vv --basetemp=.pytest_tmp`  
   執行測試（固定 basetemp）。  
   Run tests with fixed basetemp.
3. `verify_v2.bat`  
   驗證批次腳本（cmd）。  
   Run Windows batch verification.
4. `powershell -ExecutionPolicy Bypass -File .\verify_v2.ps1`  
   驗證批次腳本（PowerShell）。  
   Run PowerShell verification.

## 8) Completion Gate / 完成門檻
- 僅當上述驗證全數通過，才可標記完成。  
  Mark the task complete only when all required validations pass.

## 9) V3.4 Review-Apply Rules / V3.4 人工複核回填規則
- 僅當 `status = accepted` 且 `resolved_text` 非空白時，才允許套用人工複核內容。  
  Human-reviewed changes may only be applied when `status = accepted` and `resolved_text` is non-empty.
- `pending`、`rejected`、`skip` 一律不得改動文件文字。  
  `pending`, `rejected`, and `skip` must never modify document text.
- 回填必須採保守定位，只在目標匹配足夠可靠時套用。  
  Apply reviewed changes conservatively and only when target matching is sufficiently reliable.
- 本階段禁止導入高風險建議自動接受機制。  
  Never introduce automatic AI acceptance of high-risk suggestions in this phase.
- 禁止覆蓋第一版輸出文件，必須產生第二版 reviewed 文件。  
  Never overwrite the first-pass output document; always create a second reviewed version.
- GUI 可觸發回填流程，但不可成為 Word 內容的內嵌編輯器。  
  GUI may trigger review-apply workflow, but must not become an inline editor for Word content.

## 10) V3.5 Rule Management / V3.5 規則管理
- 低風險與高風險規則資料必須可維護且可外部化設定。  
  Keep low-risk and high-risk rule data maintainable and externally configurable.
- 必須保留舊版低風險詞庫格式向後相容。  
  Preserve backward compatibility with older low-risk dictionary formats.
- 預設規則檔為 `data/term_dict_v35.yaml` 與 `data/high_risk_rules.yaml`，可由 config/CLI 覆蓋。  
  Default rule files are `data/term_dict_v35.yaml` and `data/high_risk_rules.yaml` unless config/CLI overrides them.
- 高風險詞規則仍為純報告模式，不得直接改寫輸出文字。  
  High-risk rules must remain report-only and must never directly rewrite output text.
- GUI 可顯示規則來源資訊，但不可提供規則編輯器。  
  GUI may display rule-source information, but must not become a rule editor in this phase.
- 完成前必須先驗證規則檔有效性。  
  Always validate rule files before considering the task complete.

## 11) GUI Path Handling / GUI 路徑處理規則
- GUI 在做預設值、比較與顯示前，必須先正規化檔案與資料夾路徑。  
  GUI must normalize file and directory paths before using them for defaults, comparisons, or display.
- 選擇單一輸入檔案後，預設輸出資料夾應為該檔案父目錄。  
  When a single input file is selected, the default output directory must be set to that file's parent directory.
- 在 Windows 上，路徑顯示需統一格式，避免 `/` 與 `\` 混用造成混淆。  
  On Windows, GUI path display should be normalized to a consistent style to reduce confusion from mixed `/` and `\`.
- 使用者手動指定的輸出資料夾必須永遠優先於自動預設值。  
  Manual user selection of output directory must always take priority over auto-derived defaults.
- 僅在使用者尚未手動覆寫輸出路徑時，允許自動更新預設輸出資料夾。  
  Auto-derived output-directory updates may happen only when the user has not manually overridden the output path.
- GUI 路徑預設行為的調整不得影響 CLI 與核心 pipeline。  
  Changing GUI default path behavior must not affect CLI behavior or core pipeline logic.

## 12) V3.6 Profile Management / V3.6 規則方案管理
- profile 機制必須以向後相容方式導入。  
  Introduce rule profiles in a backward-compatible way.
- 舊版 config 在未使用 profile 時必須維持可用。  
  Keep old config behavior working when profiles are not explicitly used.
- GUI 可切換 profile，但不可提供完整的 profile 建立/編輯器。  
  GUI may switch profiles, but must not become a full profile editor in this phase.
- CLI、GUI 與核心 pipeline 必須解析到一致的 active profile 與規則來源。  
  CLI, GUI, and core pipeline must resolve to the same active profile and rule sources.
- 高風險詞仍必須維持純報告策略，不得直接改寫輸出。  
  High-risk terms must remain report-only and must never be directly rewritten.
- 完成前必跑：  
  Required before completion:
  1. `python -m pip install -r requirements.txt`
  2. `pytest -vv --basetemp=.pytest_tmp`
  3. `verify_v2.bat`
  4. `powershell -ExecutionPolicy Bypass -File .\verify_v2.ps1`
