@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if not exist ".tmp" mkdir ".tmp"
if not exist ".pytest_tmp" mkdir ".pytest_tmp"
if exist ".tmp\runtime" rmdir /s /q ".tmp\runtime" >nul 2>&1
mkdir ".tmp\runtime" >nul 2>&1
set "TEMP=%CD%\.tmp\runtime"
set "TMP=%CD%\.tmp\runtime"
set "TMP_PROBE=%TEMP%\_verify_tmp_probe.tmp"

echo [V2 VERIFY] Check TEMP/TMP writable...
echo probe>"%TMP_PROBE%" 2>nul
if errorlevel 1 (
  echo [WARN] TEMP/TMP probe write failed, continue: "%TEMP%"
) else (
  del /f /q "%TMP_PROBE%" >nul 2>&1
  if exist "%TMP_PROBE%" (
    echo [WARN] TEMP probe cleanup failed, continue: "%TMP_PROBE%"
  )
)

echo [V2 VERIFY] Prepare test data...
%PYTHON% tests\tools\generate_v2_test_data.py
if errorlevel 1 (
  echo [FAIL] test data generation failed
  exit /b 1
)

echo [V2 VERIFY] 1/7 Run pytest -vv -s (basetemp=.pytest_tmp)
%PYTHON% -m pytest -vv -s --basetemp="%CD%\.pytest_tmp"
if errorlevel 1 (
  echo [FAIL] pytest failed
  exit /b 1
)

echo [V2 VERIFY] 2/7 Clean old outputs
if exist "tests\out_single" rmdir /s /q "tests\out_single"
if exist "tests\out_batch" rmdir /s /q "tests\out_batch"
mkdir "tests\out_single" >nul 2>&1
mkdir "tests\out_batch" >nul 2>&1

echo [V2 VERIFY] 3/7 Single file smoke test
%PYTHON% app.py --input-file "tests\data\single_ok.docx" --output-dir "tests\out_single"
if errorlevel 1 (
  echo [FAIL] single smoke test failed
  exit /b 1
)
if not exist "tests\out_single\single_ok_TW.docx" (
  echo [FAIL] missing tests\out_single\single_ok_TW.docx
  exit /b 1
)
if not exist "tests\out_single\report.xlsx" (
  echo [FAIL] missing tests\out_single\report.xlsx
  exit /b 1
)

echo [V2 VERIFY] 4/7 Batch smoke test (non-recursive)
%PYTHON% app.py --input-dir "tests\data\batch_input" --output-dir "tests\out_batch"
set "BATCH_EXIT=%ERRORLEVEL%"
if not exist "tests\out_batch\report.xlsx" (
  echo [FAIL] missing tests\out_batch\report.xlsx
  exit /b 1
)

echo [V2 VERIFY] 5/7 Batch smoke test (recursive)
%PYTHON% app.py --input-dir "tests\data\batch_input" --output-dir "tests\out_batch" --recursive
set "RECURSIVE_EXIT=%ERRORLEVEL%"
if not exist "tests\out_batch\report.xlsx" (
  echo [FAIL] missing tests\out_batch\report.xlsx after recursive run
  exit /b 1
)

echo [V2 VERIFY] 6/7 Check recursive output
if not exist "tests\out_batch\sub_test_TW*.docx" (
  echo [FAIL] missing tests\out_batch\sub_test_TW*.docx
  exit /b 1
)

echo [V2 VERIFY] 7/7 Cleanup extensionless files at project root
for %%F in ("%CD%\*") do (
  if /I not "%%~aF"=="" (
    if /I "%%~xF"=="" (
      del /f /q "%%~fF" >nul 2>&1
    )
  )
)

echo.
echo pytest passed
echo single file smoke test passed
echo batch smoke test passed (exit code: %BATCH_EXIT%)
echo recursive smoke test passed (exit code: %RECURSIVE_EXIT%)
echo verification complete
exit /b 0
