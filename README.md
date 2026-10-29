# 💽 C-Drive Dormant Space Scope & Analyzer

[![Platform: Windows](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011-0078D6?logo=windows&logoColor=white)](https://microsoft.com/windows)
[![Python: 3.8+](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Dependencies: None](https://img.shields.io/badge/Dependencies-Zero%20(Pure%20Stdlib)-success)](#-architecture--zero-dependencies)
[![Recycle Bin Protected](https://img.shields.io/badge/Deletion-Recycle%20Bin%20Safe-10B981)](#-1-click-delete--safety-protection)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **High-Performance Windows C: Drive Storage Audit & Inactive Space Cleanup Engine**  
> Identifies multi-gigabyte files untouched for months or years, presents them in an executive presentation view with exact locations on `C:\`, provides safe 1-click deletion into the Windows Recycle Bin, and integrates directly with Windows File Explorer.

---

## 📸 Key Highlights

- **🎯 Precision C: Drive Inspection**: Live partition metrics (`Total`, `Used`, `Free`, and `% Capacity`).
- **📽️ Executive Presentation Slides Deck**: 5 animated slides illustrating storage health, age decay curves, top space wasters, folder hotspots, and a 3-phase remediation plan.
- **📊 Interactive Data Explorer**: Searchable, filterable, sortable data table with instant category filtering.
- **🗑️ 1-Click Recycle Bin Deletion**: Deletes files directly into the Windows Recycle Bin using native Windows Shell API (`SHFileOperationW`), automatically clearing read-only flags.
- **🛡️ Access Denied Guidance & Explorer Redirection**: When Windows blocks deletion of locked or admin-protected files, provides clear guidance and redirects you directly to the containing folder in Windows File Explorer.
- **⚡ Pure Python Standard Library**: **Zero `pip install` required!** Runs completely out of the box on Python 3.8+.

---

## 🚀 Quickstart

### 1-Click Launch (Recommended)
Double-click `run_analyzer.bat` in the project root, or launch via PowerShell:
```powershell
.\run_analyzer.ps1
```
This launches the local analyzer server and opens your default browser at:
👉 **`http://127.0.0.1:8765`**

### Command Line / Headless Launch
```powershell
# Run local web server
python c_drive_analyzer/app.py

# Or run a fast CLI scan without browser UI:
python c_drive_analyzer/app.py --cli --target "C:\Users" --min-mb 25 --min-days 60
```

---

## ✨ Core Features & Capabilities

### 1. 🔍 High-Performance Scan Engine
- **Non-blocking Breadth-First Search**: Traverses directory trees with `os.scandir` in a background thread without freezing the UI.
- **Symlink & Junction Loop Protection**: Detects and skips recursive junction loops and reparse points.
- **Configurable Thresholds**:
  - Minimum size: `10 MB`, `25 MB`, `50 MB`, `100 MB`, `250 MB`, `500 MB`, `1 GB+`.
  - Inactivity window: `30 days`, `60 days`, `90 days (1 quarter)`, `180 days (6 months)`, `1 year`, `2 years (ancient)`.
  - Inactivity basis: Effective dormancy (`max(Modified, Accessed)`), Last Modified only, or Last Accessed only.
- **Target Presets**: One-click switching between `Entire C: Drive`, `User Profile`, `Downloads Folder`, and `Dev Caches (.gradle, .m2, pip)`.

### 2. 📽️ Executive Presentation View
A built-in 5-slide deck engineered for management reporting and disk audits:
1. **Slide 1 — Executive Summary & Capacity Health**: Overall capacity meter, storage health grade (`A+` to `Critical`), and total dormant waste.
2. **Slide 2 — Time Decay & Inactivity Spectrum**: Visual distribution of dormant gigabytes categorized across age tiers (`>2 Years`, `1–2 Years`, `6–12 Months`, `3–6 Months`, `1–3 Months`).
3. **Slide 3 — Top Culprits Leaderboard**: Cards spotlighting giant dormant files with exact `C:\` paths, category badges, safety levels, and 1-click **Delete** and **Reveal in Explorer** buttons.
4. **Slide 4 — Storage Geography & Category Breakdown**: Horizontal breakdown of the top folders harboring inactive data, paired with a category distribution chart.
5. **Slide 5 — Recommended Action Plan**: A structured 3-phase remediation plan (`Safe Quick Wins`, `User Review`, and `Windows OS Managed`).
*Controls*: Fullscreen mode (`F11`), Autoplay (7s per slide), and keyboard arrow navigation.

### 3. 📊 Interactive Data Explorer
- **Instant Search**: Real-time filtering across file name, extension (`.iso`, `.zip`, `.safetensors`, `.mp4`), and path.
- **Category Chips**: Fast filtering by `Installers`, `Archives`, `Media & Video`, `AI Models & Datasets`, `VM Disks`, `Dev Caches`, or `Safe to Clean Only`.
- **Sortable Columns**: Sort ascending or descending by File Name, Path, Size, Days Inactive, Modified Date, or Safety Rating.
- **Metadata Inspector**: Detailed modal with exact byte size, modification timestamp, last access timestamp, category, and safe cleanup advice.

### 4. 🗑️ 1-Click Delete & Safety Protection
- **Recycle Bin by Default**: Files are sent to the Windows Recycle Bin via Windows `SHFileOperationW` (`FOF_ALLOWUNDO`), allowing accidental deletions to be restored.
- **Auto Read-Only Flag Stripping**: Automatically applies `os.chmod` write permissions prior to deletion to eliminate common Windows read-only removal errors.
- **OS File Protection Shield**: Crucial Windows operating system files (`hiberfil.sys`, `pagefile.sys`, `swapfile.sys`, and anything under `C:\Windows`) are marked **System Protected** and blocked from deletion.
- **Session Fast-Delete Mode**: Toggle *"Don't ask confirmation again this session"* for rapid pruning.

### 5. 📁 Rock-Solid File Explorer Redirection
- **Direct Shell Focus**: Uses Windows `AllowSetForegroundWindow` and `ShellExecuteW` with Explorer's working directory locked to the target folder, ensuring Explorer takes foreground focus over your browser.
- **Missing & System File Auto-Fallback**: If a file was already deleted or is a hidden OS file, the system automatically redirects to the containing folder instead of defaulting to "This PC".
- **Clipboard Fallback**: Every click automatically copies the exact path to your clipboard. Users can also press <kbd>Win</kbd> + <kbd>R</kbd>, paste, and hit <kbd>Enter</kbd> to jump straight to the directory.
- **Access Denied Modal**: When a file cannot be deleted due to Administrator permissions or process locking, a dedicated alert provides 1-click buttons to open the containing folder and delete it with administrative elevation.

---

## 🗂️ Project Directory Structure

```
├── run_analyzer.bat              # 1-Click Windows Batch launcher
├── run_analyzer.ps1              # 1-Click Windows PowerShell launcher
├── README.md                     # Project documentation
│
└── c_drive_analyzer/             # Application Package
    ├── app.py                    # Multi-threaded HTTP server & REST API
    ├── scanner.py                # BFS disk scanner & Windows Shell integration
    ├── README.md                 # Package documentation
    │
    └── static/                   # Embedded Frontend (Offline Web UI)
        ├── index.html            # Dual-view dashboard (Presentation + Explorer)
        ├── style.css             # Responsive glassmorphism dark/light theme
        └── app.js                # Frontend controller & canvas charts
```

---

## 🔌 REST API Reference

The built-in Python server provides a lightweight JSON API:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/drive-info` | Returns C: drive capacity, used GB, free GB, and usage percentage. |
| `GET` | `/api/presets` | Returns available scanning presets (`C:\`, User Profile, Downloads, Caches). |
| `POST` | `/api/scan/start` | Starts background scan (`target_path`, `min_size_mb`, `min_dormant_days`, etc.). |
| `POST` | `/api/scan/stop` | Halts active scan gracefully. |
| `GET` | `/api/scan/status` | Returns live scan progress (`files_scanned`, `dormant_found`, `scan_rate_fps`). |
| `GET` | `/api/scan/results` | Returns completed scan results and aggregated analytics. |
| `POST` | `/api/open-explorer` | Opens Windows File Explorer at target location (`path`, `mode: 'select'|'folder'`). |
| `POST` | `/api/delete-file` | Safely deletes file to Windows Recycle Bin (`path`, `permanent: bool`). |
| `GET` | `/api/export/csv` | Downloads complete dormant files report as UTF-8 CSV with BOM for Excel. |
| `GET` | `/api/export/presentation`| Generates and downloads a self-contained HTML presentation deck. |

---

## 🛡️ Architecture & Zero Dependencies

- **Pure Python Standard Library**: Built strictly using `os`, `sys`, `json`, `time`, `shutil`, `ctypes`, `subprocess`, `threading`, and `http.server`.
- **Zero Third-Party Pip Packages**: No installation steps, no virtualenv requirements, no risk of dependency breakage.
- **Native Windows API Calls**: Direct ctypes bindings into `shell32.dll` (`SHFileOperationW`, `ShellExecuteW`) and `user32.dll` (`AllowSetForegroundWindow`).
- **Offline Frontend**: Pure vanilla HTML5, CSS3, and Canvas API with zero CDN requirements.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
