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
- Phase 1 freeze / usage / known issues documentation.

## Verification

- Full pytest passed: 217 passed.
- `verify_v2.bat` passed.
- `verify_v2.ps1` passed.

## Not Included

- full GUI integration.
- complete chapter workflow.
- GUI TOC controls.
- advanced TOC behavior.
- paragraph merge source mismatch verification against docx content.
- paragraph merge result reporting.
- GUI paragraph merge controls.
- run-level formatting fidelity.
- full legacy entry replacement.
