# Windows GUI One-Folder Packaging

## 目的與定位

本文件記錄 Windows 上使用 PyInstaller 進行 GUI one-folder 測試封裝的第一版成功條件。

目前定位：

- 內部測試版 executable
- 用於確認 Python 專案可被封裝、啟動 GUI、載入設定與資料檔，並完成最小 `.docx` 流程
- 不是正式一般使用者交付版

本輪不做：

- one-file
- installer
- CLI 封裝
- 一般使用者安裝流程

## 正式打包入口

第一版封裝入口使用：

```powershell
app.py
```

封裝後啟動 GUI 時使用：

```powershell
.\dist\docx-gui-test\docx-gui-test.exe --gui
```

不直接以 `src/gui/main_window_clean.py` 作為打包入口，避免繞過目前正式啟動路由。

## PyInstaller 命令

第一版使用 one-folder，並保留 console 以方便排查錯誤：

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --onedir --name docx-gui-test --add-data "data;data" --add-data "設定檔.yaml;." app.py
```

已確認 PyInstaller 版本：

```text
6.19.0
```

## 必要資源帶入

第一版已驗證可行的資源帶入策略：

- `data/`
- `設定檔.yaml`

原因：

- `config_loader` 預設會從專案根層級找 `設定檔.yaml`
- 規則檔會透過設定檔與預設路徑解析到 `data/`
- 封裝後 PyInstaller 會將這些資源放在 `_internal` 下，已通過最小流程驗證

第一版不帶入：

- `tests/`
- `docs/`
- `.git/`
- `.venv/`
- `requirements.txt`

## 產物結構

第一版預期產物：

```text
dist/
  docx-gui-test/
    docx-gui-test.exe
    _internal/
      設定檔.yaml
      data/
        term_dict_v35.yaml
        high_risk_rules.yaml
        低風險詞庫.yaml
        高風險規則.yaml
        ...
```

同時會產生 PyInstaller 建置輸出：

```text
build/
docx-gui-test.spec
```

## 啟動方式

GUI 啟動：

```powershell
.\dist\docx-gui-test\docx-gui-test.exe --gui
```

第一版仍保留 console。若 GUI 啟動或處理文件失敗，console 輸出可協助排查。

## 最小驗證清單

已完成的最小驗證：

- PyInstaller 可用
- one-folder 封裝成功
- `docx-gui-test.exe` 存在
- `_internal\設定檔.yaml` 存在
- `_internal\data\high_risk_rules.yaml` 存在
- `_internal\data\低風險詞庫.yaml` 存在
- `docx-gui-test.exe --help` 可執行
- `docx-gui-test.exe --gui` 可啟動 GUI 程序
- 封裝後 exe 可完成最小 `.docx` 處理 smoke test
- 輸出的 `.docx` 可由 `python-docx` 讀取

後續若重新驗證，建議至少檢查：

1. exe 能啟動 GUI。
2. GUI 主視窗可正常開啟。
3. 可選擇一份最小 `.docx`。
4. 可選擇輸出資料夾。
5. 可完成最小 convert 流程。
6. 輸出 `.docx` 可正常開啟。
7. 發生錯誤時能看到可理解的錯誤訊息。

## 已知限制

目前限制：

- 尚未做完整人工 GUI 點選流程驗證
- 尚未驗證所有 TOC 情境
- 尚未驗證所有 paragraph merge / diagnostics 情境
- 尚未驗證 profile 全組合
- 尚未驗證不同工作目錄啟動時的路徑行為
- 尚未做無 console 版本
- 尚未做 one-file
- 尚未做 installer
- 尚未封裝 CLI

PyInstaller warning 中可能出現 optional missing modules，例如部分 POSIX-only modules、`bs4`、`html5lib`、`numpy`、`PIL` 等。第一版 smoke test 未顯示這些是阻塞項目，但正式交付前仍需依實際功能驗證。

## 後續不建議立即做的事

目前不建議立刻做：

- one-file 封裝
- installer
- 自動更新
- 程式簽章
- 桌面捷徑
- CLI + GUI 雙入口封裝
- 新增 launcher
- 修改 production code 來配合封裝

建議先完成：

- 人工 GUI 最小流程驗證
- 不同工作目錄啟動驗證
- 常見失敗情境排查
- 確認是否真的需要獨立 launcher
