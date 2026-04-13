# Version Overview

## Current Status

DOCX 小說簡轉繁工具目前已完成 Phase 1A-1E 主幹，並延伸到 Phase 2F-2。核心流程已涵蓋 analyze、convert、apply_review、review schema 驗證、chapter candidate apply、convert / apply_review TOC、report TOC 摘要、GUI TOC 狀態摘要顯示、`paragraph_merge_candidates` schema / reviewed JSON 驗證收斂、paragraph merge 最小安全套用、paragraph merge summary reporting、GUI paragraph merge summary display、paragraph merge source mismatch diagnostics reporting，以及 GUI paragraph merge diagnostics display。

CLI 可透過 `src.phase1_cli` 獨立運作，舊 CLI 已完成第一版保守轉發。GUI 已完成 worker 與主視窗第一版最小接線，可操作 analyze / convert / apply_review，並顯示最小結果摘要。

最新驗證狀態：

- Full pytest passed: 240 passed
- `verify_v2.bat` passed
- `verify_v2.ps1` passed

## Version Timeline

- `v1.0-phase1-freeze` - `e78b8d5`
  - 凍結 Phase 1A-1E 主幹。
  - 建立獨立 Phase 1 CLI、JSON / TXT report、規則檔契約、reviewed output 契約、legacy CLI 第一版保守轉發。

- `v1.1-phase1-gui-minimal` - `b182d6b`
  - 完成 GUI 主視窗第一版最小接線。
  - GUI 可最小操作 analyze / convert / apply_review。

- `v1.2-phase2a-schema-validation` - `df12785`
  - 收斂 reviewed JSON / ReviewSchema 最小驗證契約。
  - 建立 fail-fast 流程級錯誤與 candidate 型別驗證規則。

- `v1.3-phase2b-chapter-apply` - `31eda22`
  - 建立 chapter candidate apply 基礎。
  - accepted chapter candidate 可將目標段落套用為 `Heading 2`。

- `v1.4-phase2c-toc-minimal` - `a30a8be`
  - 完成 convert 流程的 TOC 最小方案。
  - 支援既有 `Heading 2` 的 Word TOC field 與 fallback 前置章節清單。

- `v1.5-phase2d1-apply-review-toc` - `21e847d`
  - 完成 apply_review 流程的 TOC 支援。
  - apply_review 沿用既有 TOC builder，並維持 review candidates、chapter candidates、TOC、save 的固定順序。

- `v1.6-phase2d2-report-toc` - `b128551`
  - 完成 report TOC 狀態摘要。
  - JSON report top-level 固定輸出 `toc`，TXT report 補上最小 TOC 摘要。

- `v1.7-phase2d3-gui-toc-summary` - `0968e71`
  - 完成 GUI TOC 狀態摘要顯示。
  - GUI 結果摘要區顯示 `TOC 狀態`、`TOC fallback`、`TOC 章節數`。

## Completed Capabilities

- Phase 1A-1E 主幹。
- GUI worker / GUI 主視窗第一版。
- reviewed JSON / ReviewSchema 驗證收斂。
- chapter candidate apply 基礎。
- convert TOC 最小方案。
- apply_review TOC 支援。
- report TOC 狀態摘要。
- GUI TOC 狀態摘要顯示。
- paragraph_merge_candidates schema / reviewed JSON validation hardening.
- paragraph merge apply (minimal safe apply in apply_review).
- paragraph merge summary reporting.
- GUI paragraph merge summary display.
- paragraph merge source mismatch diagnostics reporting.
- GUI paragraph merge diagnostics display.
- 獨立 Phase 1 CLI。
- legacy CLI 第一版保守轉發。
- 高風險規則預設檔名契約收斂。
- `--reviewed-output` 契約收斂。

## Remaining Major Gaps

- GUI diagnostics controls.
- source mismatch detailed diagnostics panel.
- GUI paragraph merge controls.
- reviewed JSON editor.
- run-level formatting fidelity.
- advanced TOC behavior.
- full GUI integration.
- full legacy entry replacement.
- complete chapter workflow.

## Next Candidate Directions

- GUI paragraph merge controls planning.
- run-level formatting fidelity planning.
- chapter workflow planning.
- legacy entry governance planning.
- GUI second-pass planning.
