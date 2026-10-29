# 💽 C-Drive Dormant Space Scope & Analyzer

> **Intelligent Windows Laptop C: Drive Audit & Inactive Space Analyzer**  
> Identifies large files untouched for long periods, presents them in an executive presentation view with exact C: locations, provides safe 1-click deletion into the Windows Recycle Bin, and provides one-click Windows File Explorer integration.

---

## ✨ Features

- **🎯 Precision C: Drive Analysis**:
  - Live inspection of Windows partition capacity (`Total`, `Used`, `Free`, and `% Occupied`).
  - High-speed, non-blocking scan using breadth-first traversal (`os.scandir`) with symlink and junction loop protection.
  - Configurable minimum size thresholds: `10MB`, `25MB`, `50MB`, `100MB`, `250MB`, `500MB`, `1GB+`.
  - Configurable dormancy thresholds: `30 days`, `60 days`, `90 days (1 quarter)`, `180 days (6 months)`, `1 year`, `2 years (ancient)`.
  - Smart dormancy metric: Evaluates effective inactivity (`max(Last Modified, Last Accessed)`), Last Modified only, or Last Accessed only.

- **📽️ Presentation View (Executive Slides Deck)**:
  - **Slide 1: Executive Summary & C: Drive Health**: Storage health score, capacity meter (Used vs Free vs Dormant), and reclaimable GB estimates.
  - **Slide 2: Time Decay & Inactivity Spectrum**: Visual distribution of dormant gigabytes across age tiers (`>2 Years`, `1-2 Years`, `6-12 Months`, `3-6 Months`, `1-3 Months`).
  - **Slide 3: Top 10 Giant Dormant Culprits & Locations**: Leaderboard cards featuring file size, days untouched, exact path in `C:\`, and immediate **Reveal in File Explorer** actions.
  - **Slide 4: Storage Geography & Category Breakdown**: Identifies which top folders on `C:\` harbor the most inactive gigabytes and file category breakdown.
  - **Slide 5: Recommended Action Plan & Safety Roadmap**: Actionable 3-phase guide (`Safe Quick Wins`, `User Review`, `Windows OS Managed`).
  - Presentation controls: Fullscreen mode, autoplay toggle, keyboard arrow navigation, slide indicators.

- **📊 Interactive Data Explorer View**:
  - Live search by filename, extension (`.iso`, `.zip`, `.mp4`, `.safetensors`), or path substring.
  - Quick category filtering chips (`Installers`, `Archives`, `Media`, `AI Models`, `VM Disks`, `Dev Caches`, `Safe to Clean Only`).
  - Sortable data table: click any column header (Size, Inactivity Days, Date Modified, Path, Safety).
  - Row actions:
    - 📁 **Reveal in Explorer**: Opens Windows File Explorer with the exact file pre-selected.
    - 📋 **Copy Path**: Copies the Windows absolute path to the clipboard.
    - ℹ️ **Details Modal**: Detailed file metadata, timestamps, byte breakdown, and cleanup advice.

- **🗑️ 1-Click Delete Functionality**:
  - Delete any file with a single click directly from the **Top Culprits cards in Presentation View**, from each table row in **Data Explorer View**, or from the **File Details modal**.
  - **Safe Windows Recycle Bin Integration**: Deletes via native Windows Shell API (`SHFileOperationW`) to safely place files into the Windows Recycle Bin, allowing recovery if needed. Automatically clears read-only attributes before deletion.
  - **Access Denied Guidance Modal**: If Windows blocks automated deletion due to Administrator permissions or process locking, a dedicated alert suggests opening the location in File Explorer and provides a 1-click **"📂 Open Containing Folder"** button.
  - **Rock-Solid Explorer Reveal**: Uses Windows `AllowSetForegroundWindow` and `ShellExecuteW` with full binary path, working directory binding, and automatic directory fallback for missing or system files (`hiberfil.sys`, `pagefile.sys`).
  - **System Protection Safeguard**: Windows operating system files (`pagefile.sys`, `hiberfil.sys`, `C:\Windows`) are protected and blocked from accidental deletion.
  - **Dynamic In-Memory Updates**: Deleting a file instantly animates the row away, updates the C: drive capacity meters, and recalculates reclaimable gigabytes without requiring a full re-scan.
  - **Session 1-Click Fast Delete**: Check *"Don't ask confirmation again this session"* for rapid, zero-dialog single-click pruning.

- **🛡️ Smart Safety Ratings**:
  - **Safe to Clean**: Downloads, Temp directories, old package caches (`.gradle`, `.m2`, `npm-cache`).
  - **Review Needed**: User media, documents, virtual disks, AI weights.
  - **Installed App / Caution**: Program Files, ProgramData, XboxGames.
  - **System Protected**: Windows OS files (`pagefile.sys`, `hiberfil.sys`, `swapfile.sys`).

- **📑 Presentation & Data Export**:
  - Export standalone executive presentation HTML (interactive, self-contained slide deck).
  - Export CSV report for auditing.

---

## 🚀 How to Run

### Option 1: 1-Click Launch (Batch / PowerShell)
Double click `run_analyzer.bat` in the workspace root, or run in PowerShell:
```powershell
.\run_analyzer.ps1
```
This automatically starts the local backend server and opens your web browser to:
👉 **`http://127.0.0.1:8765`**

### Option 2: Python Command Line
```powershell
cd c_drive_analyzer
python app.py
```
Or run a fast CLI scan without opening the browser:
```powershell
python app.py --cli --target "C:\Users" --min-mb 25 --min-days 60
```

---

## 🛠️ Architecture & Requirements
- **Runtime**: Python 3.8+ (Tested on Python 3.15).
- **Dependencies**: **Zero external pip packages required!** Runs 100% on Python standard library (`http.server`, `os`, `shutil`, `subprocess`, `csv`, `json`, `threading`, `ctypes`).
- **Frontend**: Self-contained HTML5, CSS3, Vanilla JS, and HTML5 Canvas charts. Works entirely offline.
