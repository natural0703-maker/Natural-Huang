$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$python = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $python = ".venv\Scripts\python.exe"
}

$tmpDir = Join-Path $PSScriptRoot ".tmp"
$pytestTmpDir = Join-Path $PSScriptRoot ".pytest_tmp"
$runtimeTmpDir = Join-Path $tmpDir "runtime"
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
New-Item -ItemType Directory -Force -Path $pytestTmpDir | Out-Null
if (Test-Path $runtimeTmpDir) {
    Remove-Item -Recurse -Force $runtimeTmpDir -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Force -Path $runtimeTmpDir | Out-Null
$env:TEMP = $runtimeTmpDir
$env:TMP = $runtimeTmpDir

function Assert-TempWritable {
    param([Parameter(Mandatory = $true)][string]$DirPath)
    $probePath = Join-Path $DirPath "_verify_tmp_probe.tmp"
    try {
        Set-Content -LiteralPath $probePath -Value "probe" -Encoding ASCII -ErrorAction Stop
    }
    catch {
        throw "TEMP/TMP 目錄不可用：$DirPath"
    }
    try {
        Remove-Item -LiteralPath $probePath -Force -ErrorAction Stop
    }
    catch {
        Write-Host "[V2 VERIFY] TEMP probe cleanup failed, continue: $probePath"
    }
}

function Run-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Title,
        [Parameter(Mandatory = $true)][scriptblock]$Action
    )
    Write-Host $Title
    & $Action
}

function Assert-PathExists {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path $Path)) {
        throw "missing $Path"
    }
}

function Test-ReportHasFailureEntry {
    param(
        [Parameter(Mandatory = $true)][string]$ReportPath,
        [Parameter(Mandatory = $true)][string]$ExpectedFileName
    )

    $code = @'
import sys
from openpyxl import load_workbook

report_path = sys.argv[1]
expected_name = sys.argv[2]

wb = load_workbook(report_path, data_only=True)
if "failures" not in wb.sheetnames:
    raise SystemExit(2)

ws = wb["failures"]
for row in ws.iter_rows(min_row=2, values_only=True):
    if row and str(row[0]) == expected_name:
        raise SystemExit(0)

raise SystemExit(1)
'@
    $scriptPath = Join-Path $PSScriptRoot ".tmp\check_failures.py"
    Set-Content -LiteralPath $scriptPath -Value $code -Encoding UTF8
    & $python $scriptPath $ReportPath $ExpectedFileName
    return ($LASTEXITCODE -eq 0)
}

Run-Step "[V2 VERIFY] Prepare test data..." {
    Assert-TempWritable -DirPath $env:TEMP
    & $python "tests\tools\generate_v2_test_data.py"
    if ($LASTEXITCODE -ne 0) {
        throw "test data generation failed"
    }
}

Run-Step "[V2 VERIFY] 1/7 Run pytest -vv -s (basetemp=.pytest_tmp)" {
    & $python -m pytest -vv -s --basetemp $pytestTmpDir
    if ($LASTEXITCODE -ne 0) {
        throw "pytest failed"
    }
}

Run-Step "[V2 VERIFY] 2/7 Clean old outputs" {
    if (Test-Path "tests\out_single") {
        try {
            Remove-Item -Recurse -Force "tests\out_single" -ErrorAction Stop
        }
        catch {
            Write-Host "[V2 VERIFY] 清理 tests\out_single 時略過無法刪除的舊檔"
        }
    }
    if (Test-Path "tests\out_batch") {
        try {
            Remove-Item -Recurse -Force "tests\out_batch" -ErrorAction Stop
        }
        catch {
            Write-Host "[V2 VERIFY] 清理 tests\out_batch 時略過無法刪除的舊檔"
        }
    }
    New-Item -ItemType Directory -Force -Path "tests\out_single" | Out-Null
    New-Item -ItemType Directory -Force -Path "tests\out_batch" | Out-Null
}

Run-Step "[V2 VERIFY] 3/7 Single file smoke test" {
    & $python "app.py" --input-file "tests\data\single_ok.docx" --output-dir "tests\out_single"
    if ($LASTEXITCODE -ne 0) {
        throw "single smoke test failed: exit code $LASTEXITCODE"
    }
    Assert-PathExists "tests\out_single\single_ok_TW.docx"
    Assert-PathExists "tests\out_single\report.xlsx"
}

$batchExit = 0
Run-Step "[V2 VERIFY] 4/7 Batch smoke test (non-recursive)" {
    & $python "app.py" --input-dir "tests\data\batch_input" --output-dir "tests\out_batch"
    $script:batchExit = $LASTEXITCODE

    Assert-PathExists "tests\out_batch\report.xlsx"
    $normalOut = Get-ChildItem "tests\out_batch" -Filter "normal_1_TW*.docx" -ErrorAction SilentlyContinue
    if (-not $normalOut) {
        throw "batch smoke test failed: missing normal output docx"
    }
    if (-not (Test-ReportHasFailureEntry -ReportPath "tests\out_batch\report.xlsx" -ExpectedFileName "bad.docx")) {
        throw "batch smoke test failed: failures sheet missing bad.docx record"
    }
    if (($batchExit -ne 0) -and ($batchExit -ne 1)) {
        throw "batch smoke test failed: unexpected exit code $batchExit"
    }
}

$recursiveExit = 0
Run-Step "[V2 VERIFY] 5/7 Batch smoke test (recursive)" {
    & $python "app.py" --input-dir "tests\data\batch_input" --output-dir "tests\out_batch" --recursive
    $script:recursiveExit = $LASTEXITCODE

    Assert-PathExists "tests\out_batch\report.xlsx"
    $subOutput = Get-ChildItem "tests\out_batch" -Filter "sub_test_TW*.docx" -ErrorAction SilentlyContinue
    if (-not $subOutput) {
        throw "recursive smoke test failed: missing subfolder output docx"
    }
    if (-not (Test-ReportHasFailureEntry -ReportPath "tests\out_batch\report.xlsx" -ExpectedFileName "bad.docx")) {
        throw "recursive smoke test failed: failures sheet missing bad.docx record"
    }
    if (($recursiveExit -ne 0) -and ($recursiveExit -ne 1)) {
        throw "recursive smoke test failed: unexpected exit code $recursiveExit"
    }
}

Run-Step "[V2 VERIFY] 6/7 Cleanup extensionless files at project root" {
    Get-ChildItem -LiteralPath $PSScriptRoot -File |
        Where-Object { $_.Extension -eq "" } |
        ForEach-Object {
            Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
        }
}

Write-Host ""
Write-Host "pytest passed"
Write-Host "single file smoke test passed"
Write-Host "batch smoke test passed with expected file-level failures"
Write-Host "recursive smoke test passed with expected file-level failures"
Write-Host "verification complete"
exit 0
