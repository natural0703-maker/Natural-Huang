# Phase 1 Freeze Release Note

## Summary

Phase 1 mainline is frozen and verified.

## Included

- Phase 1A-1E mainline.
- Phase 1 CLI.
- JSON / TXT reporting.
- high-risk rules default filename contract alignment.
- `--reviewed-output` contract finalization.
- legacy CLI first-pass forwarding.
- GUI Phase 1 worker first-pass integration.
- GUI main window first-pass minimal integration.
- Phase 2A review schema / reviewed JSON validation hardening.
- Phase 2B chapter candidate apply foundation.
- Phase 2C minimal TOC support for convert flow.
- Phase 2D-1 TOC support for apply_review flow.
- Phase 2D-2 TOC status reporting.
- Phase 2D-3 GUI TOC status summary.
- Phase 2E-1 paragraph merge schema validation.
- Phase 2E-2 paragraph merge apply.
- Phase 2E-3 paragraph merge summary reporting.
- Phase 2E-4 GUI paragraph merge summary.
- Phase 2F-1 paragraph merge mismatch diagnostics.
- Phase 2F-2 GUI merge diagnostics.
- Phase 2F-3A diagnostics sample entries.
- Phase 2F-3B GUI diagnostics sample entries.
- Phase G-2 legacy entry governance documentation alignment.
- Phase G-3A legacy forwarder wording and forward-guard tests.
- Phase 1 freeze / usage / known issues documentation.

## Verification

- Full pytest passed: 245 passed.
- `verify_v2.bat` passed.
- `verify_v2.ps1` passed.

## Not Included

- full GUI integration.
- complete chapter workflow.
- GUI TOC controls.
- advanced TOC behavior.
- paragraph merge source mismatch verification against docx content.
- GUI paragraph merge controls.
- GUI detailed diagnostics panel.
- GUI diagnostics controls.
- source mismatch detailed diagnostics panel.
- reviewed JSON editor.
- run-level formatting fidelity.
- G-3B minimal forward condition adjustment.
- G-4 legacy retirement evaluation.
- `app.py` runtime governance changes.
- new CLI parameters or forwarding condition expansion.
- full legacy entry replacement.
