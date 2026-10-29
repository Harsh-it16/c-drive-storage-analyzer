"""
C-Drive Dormant File Analyzer - Scanner Engine
Scans drives/folders on Windows, identifies space-wasting files untouched for long periods,
and computes analytics for executive presentation and interactive exploration.
"""

import os
import stat
import time
import shutil
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
import ctypes
from ctypes import wintypes

class SHFILEOPSTRUCTW(ctypes.Structure):
    _fields_ = [
        ('hwnd', wintypes.HWND),
        ('wFunc', wintypes.UINT),
        ('pFrom', wintypes.LPCWSTR),
        ('pTo', wintypes.LPCWSTR),
        ('fFlags', wintypes.WORD),
        ('fAnyOperationsAborted', wintypes.BOOL),
        ('hNameMappings', wintypes.LPVOID),
        ('lpszProgressTitle', wintypes.LPCWSTR),
    ]

FO_DELETE = 0x0003
FOF_ALLOWUNDO = 0x0040       # Recycle Bin
FOF_NOCONFIRMATION = 0x0010  # Don't prompt Windows dialog
FOF_SILENT = 0x0004          # Don't show progress window
FOF_NOERRORUI = 0x0400       # Don't display error UI

def delete_file_from_disk(filepath: str, permanent: bool = False) -> tuple[bool, str, bool]:
    """
    Deletes a file, defaulting to the Windows Recycle Bin for safety.
    Returns: (success: bool, message: str, is_access_denied: bool)
    """
    if not os.path.exists(filepath):
        return False, "File does not exist on disk.", False

    # Attempt to clear Read-Only flag if set
    try:
        os.chmod(filepath, stat.S_IWRITE | stat.S_IREAD)
    except Exception:
        pass

    if permanent:
        try:
            os.remove(filepath)
            return True, "File permanently deleted.", False
        except PermissionError:
            return False, "Access is denied: Windows requires administrative privileges or the file is locked by a running process.", True
        except Exception as e:
            err_str = str(e).lower()
            is_denied = "access is denied" in err_str or "permission" in err_str
            return False, f"Failed to permanently delete: {str(e)}", is_denied

    # Native Windows Recycle Bin deletion
    try:
        norm = os.path.normpath(os.path.abspath(filepath))
        pfrom = norm + '\0\0'
        fileop = SHFILEOPSTRUCTW()
        fileop.hwnd = None
        fileop.wFunc = FO_DELETE
        fileop.pFrom = pfrom
        fileop.pTo = None
        fileop.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT | FOF_NOERRORUI
        res = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(fileop))
        if res == 0:
            return True, "File safely moved to Windows Recycle Bin.", False
        elif res in (120, 0x78): # DE_ACCESSDENIED
            return False, "Access is denied: Windows requires administrative privileges or the file is locked.", True
        elif res in (117, 0x75): # DE_SHARINGVIOLATION
            return False, "Access is denied: File is currently locked and in use by another running program.", True
        else:
            # Fallback to standard delete if Recycle Bin isn't supported for this drive
            try:
                os.remove(filepath)
                return True, "File deleted directly (Recycle Bin not supported).", False
            except PermissionError:
                return False, "Access is denied: Windows requires administrative privileges or the file is locked by a running process.", True
            except Exception as e2:
                err_str = str(e2).lower()
                is_denied = "access is denied" in err_str or "permission" in err_str
                return False, f"Failed to delete file: {str(e2)}", is_denied
    except PermissionError:
        return False, "Access is denied: Windows requires administrative privileges or the file is locked by a running process.", True
    except Exception as e:
        try:
            os.remove(filepath)
            return True, "File deleted directly.", False
        except PermissionError:
            return False, "Access is denied: Windows requires administrative privileges or the file is locked by a running process.", True
        except Exception as e2:
            err_str = str(e2).lower()
            is_denied = "access is denied" in err_str or "permission" in err_str
            return False, f"Failed to delete file: {str(e2)}", is_denied

# File category extensions mapping
CATEGORIES = {
    "Installers & Setup": {
        "extensions": {".exe", ".msi", ".msp", ".pkg", ".appx", ".msix", ".msixbundle", ".cab"},
        "icon": "📦",
        "description": "Software installers and setup executables"
    },
    "Archives & Compressed": {
        "extensions": {".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".zst", ".iso", ".img"},
        "icon": "🗄️",
        "description": "Compressed archives and disk images"
    },
    "Media & Video": {
        "extensions": {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".flv", ".webm", ".m4v", ".mp3", ".wav", ".flac", ".aac", ".psd", ".raw"},
        "icon": "🎬",
        "description": "High-definition video, audio, and raw media"
    },
    "Virtual Machines & Disks": {
        "extensions": {".vmdk", ".vdi", ".vhdx", ".vhd", ".qcow2", ".hdd", ".ova", ".ovf"},
        "icon": "💻",
        "description": "Virtual machine hard disks and container images"
    },
    "AI Models & Datasets": {
        "extensions": {".safetensors", ".gguf", ".bin", ".pt", ".pth", ".onnx", ".ckpt", ".h5", ".arrow", ".parquet"},
        "icon": "🧠",
        "description": "Machine learning weights, checkpoints, and datasets"
    },
    "Development Caches": {
        "extensions": {".jar", ".aar", ".whl", ".gem", ".apk", ".ipa", ".lib", ".a", ".pdb", ".log"},
        "icon": "🛠️",
        "description": "Build artifacts, libraries, and debug caches"
    },
    "System / Virtual Memory": {
        "extensions": {".sys", ".dmp", ".tm", ".blf"},
        "icon": "⚙️",
        "description": "Windows system, swap, hibernation, or crash dump files"
    },
    "Documents & Data": {
        "extensions": {".pdf", ".docx", ".xlsx", ".pptx", ".csv", ".tsv", ".sqlite", ".db", ".sql"},
        "icon": "📄",
        "description": "Documents, spreadsheets, presentations, and databases"
    }
}

SYSTEM_PROTECTED_FILES = {
    "pagefile.sys", "hiberfil.sys", "swapfile.sys", "dumpstack.log", "dumpstack.log.tmp",
    "bootmgr", "bootnxt", "boottel.dat", "ntuser.dat"
}

def get_file_category(filename: str, filepath: str) -> str:
    name_lower = filename.lower()
    if name_lower in SYSTEM_PROTECTED_FILES:
        return "System / Virtual Memory"
    
    _, ext = os.path.splitext(name_lower)
    for cat_name, info in CATEGORIES.items():
        if ext in info["extensions"]:
            return cat_name
            
    # Check directory path heuristics
    path_lower = filepath.lower()
    if any(k in path_lower for k in [r"\.gradle", r"\.m2", r"\npm-cache", r"\.conda", r"\site-packages", r"\node_modules"]):
        return "Development Caches"
    if any(k in path_lower for k in [r"\modelfiles", r"\.ollama"]):
        return "AI Models & Datasets"
        
    return "Other Files"

def assess_safety(filepath: str, filename: str) -> Dict[str, str]:
    path_lower = filepath.lower()
    name_lower = filename.lower()
    
    # 1. System protected files
    if name_lower in SYSTEM_PROTECTED_FILES or r"\windows" in path_lower or r"\recovery" in path_lower or r"\system volume information" in path_lower:
        return {
            "level": "system",
            "badge": "System Protected",
            "color": "amber",
            "advice": "Windows OS managed file. Do not manually delete! (Use Windows Storage Sense or powercfg)"
        }
    
    # 2. Installed applications / program files
    if r"\program files" in path_lower or r"\programdata" in path_lower or r"\xboxgames" in path_lower:
        return {
            "level": "caution",
            "badge": "Installed App / Caution",
            "color": "orange",
            "advice": "Part of an installed program or game. Uninstall properly via Settings or Control Panel."
        }
        
    # 3. Downloads, temp, and standalone archives
    if r"\downloads" in path_lower or r"\temp" in path_lower or r"\.tmp" in path_lower:
        return {
            "level": "safe",
            "badge": "Safe to Clean",
            "color": "emerald",
            "advice": "Located in Downloads/Temp directory. Highly safe to delete or archive if no longer needed."
        }
        
    # 4. Old build caches
    if any(k in path_lower for k in [r"\.gradle\caches", r"\.m2\repository", r"\npm-cache"]):
        return {
            "level": "safe",
            "badge": "Safe Cache",
            "color": "emerald",
            "advice": "Build/package cache. Can be safely pruned or cleared using its package tool."
        }
        
    # 5. General user review
    return {
        "level": "review",
        "badge": "Review Needed",
        "color": "blue",
        "advice": "User file or application document. Review contents before deleting or moving."
    }

class DriveScanner:
    def __init__(self):
        self.is_scanning = False
        self.stop_requested = False
        self.progress = {
            "is_scanning": False,
            "target_path": "C:\\",
            "files_scanned": 0,
            "dirs_scanned": 0,
            "total_bytes_scanned": 0,
            "dormant_found": 0,
            "dormant_bytes": 0,
            "current_dir": "",
            "elapsed_seconds": 0,
            "scan_rate_fps": 0,
            "status_message": "Idle"
        }
        self.results: List[Dict[str, Any]] = []
        self.analytics: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._start_time = 0.0

    def get_c_drive_info(self) -> Dict[str, Any]:
        """Gets overall C: drive storage statistics."""
        try:
            usage = shutil.disk_usage("C:\\")
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            used_pct = round((usage.used / usage.total) * 100, 1)
            free_pct = round((usage.free / usage.total) * 100, 1)
            return {
                "drive": "C:",
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "used_pct": used_pct,
                "free_pct": free_pct
            }
        except Exception as e:
            return {
                "drive": "C:",
                "error": str(e),
                "total_gb": 0,
                "used_gb": 0,
                "free_gb": 0,
                "used_pct": 0,
                "free_pct": 0
            }

    def get_presets(self) -> List[Dict[str, str]]:
        """Returns helpful preset scan paths for Windows users."""
        user_dir = os.environ.get("USERPROFILE", r"C:\Users")
        presets = [
            {
                "id": "c_root",
                "name": "Full C:\\ Drive (Comprehensive)",
                "path": "C:\\",
                "description": "Deep scan of all reachable files across the entire C: drive"
            },
            {
                "id": "user_profile",
                "name": f"User Profile ({os.path.basename(user_dir)})",
                "path": user_dir,
                "description": "Scans your entire user profile including Downloads, Documents, Caches, & AppData"
            },
            {
                "id": "user_downloads",
                "name": "Downloads & Documents",
                "path": os.path.join(user_dir, "Downloads"),
                "description": "Fast scan of personal downloaded files and documents"
            },
            {
                "id": "user_caches",
                "name": "Developer & App Caches",
                "path": user_dir,
                "description": "Scans for dormant .gradle, .m2, .cache, modelfiles, and build artifacts"
            }
        ]
        return presets

    def start_scan(self, 
                   target_path: str = "C:\\", 
                   min_size_mb: float = 25.0, 
                   min_dormant_days: int = 60,
                   date_basis: str = "effective", # "effective" (max of mtime, atime), "mtime", "atime"
                   skip_system_dirs: bool = True,
                   max_results: int = 5000) -> bool:
        """Starts scanning in a background thread."""
        with self._lock:
            if self.is_scanning:
                return False
            self.is_scanning = True
            self.stop_requested = False
            self.results = []
            self.analytics = {}
            self._start_time = time.time()
            self.progress = {
                "is_scanning": True,
                "target_path": target_path,
                "files_scanned": 0,
                "dirs_scanned": 0,
                "total_bytes_scanned": 0,
                "dormant_found": 0,
                "dormant_bytes": 0,
                "current_dir": target_path,
                "elapsed_seconds": 0,
                "scan_rate_fps": 0,
                "status_message": f"Scanning {target_path}..."
            }

        self._thread = threading.Thread(
            target=self._scan_worker,
            args=(target_path, min_size_mb, min_dormant_days, date_basis, skip_system_dirs, max_results),
            daemon=True
        )
        self._thread.start()
        return True

    def stop_scan(self):
        """Signals the background scanner to stop."""
        with self._lock:
            self.stop_requested = True
            self.progress["status_message"] = "Stopping..."

    def get_status(self) -> Dict[str, Any]:
        """Returns the current scan status and progress."""
        with self._lock:
            p = dict(self.progress)
            if self.is_scanning and self._start_time > 0:
                elapsed = max(0.1, time.time() - self._start_time)
                p["elapsed_seconds"] = round(elapsed, 1)
                p["scan_rate_fps"] = int(p["files_scanned"] / elapsed)
            return p

    def get_results(self) -> Dict[str, Any]:
        """Returns results and aggregated analytics."""
        with self._lock:
            return {
                "progress": dict(self.progress),
                "drive_info": self.get_c_drive_info(),
                "analytics": self.analytics,
                "results": self.results
            }

    def delete_file(self, filepath: str, permanent: bool = False) -> tuple[bool, str, int, bool]:
        """
        Deletes a file, verifies safety, and updates in-memory analytics.
        Returns: (success: bool, message: str, freed_bytes: int, is_access_denied: bool)
        """
        norm_target = os.path.normpath(filepath).lower()
        filename = os.path.basename(norm_target)
        safety = assess_safety(norm_target, filename)

        if safety["level"] == "system":
            return False, f"Cannot delete Windows System file ({safety['badge']}). Operating system files are protected.", 0, True

        with self._lock:
            # Check if file exists in our results
            matching_idx = None
            freed_bytes = 0
            for idx, f in enumerate(self.results):
                if os.path.normpath(f["path"]).lower() == norm_target:
                    matching_idx = idx
                    freed_bytes = f["size_bytes"]
                    break

        # Perform physical delete on disk
        ok, msg, is_access_denied = delete_file_from_disk(filepath, permanent=permanent)
        if not ok:
            return False, msg, 0, is_access_denied

        # Update in-memory state
        with self._lock:
            if matching_idx is not None:
                self.results.pop(matching_idx)
                dormant_bytes = sum(f["size_bytes"] for f in self.results)
                self.progress["dormant_found"] = len(self.results)
                self.progress["dormant_bytes"] = dormant_bytes
                self.analytics = self._compute_analytics(self.results, dormant_bytes)

        return True, msg, freed_bytes, False

    def _scan_worker(self, target_path: str, min_size_mb: float, min_dormant_days: int, 
                     date_basis: str, skip_system_dirs: bool, max_results: int):
        now = time.time()
        min_size_bytes = int(min_size_mb * 1024 * 1024)
        found_files = []
        files_scanned = 0
        dirs_scanned = 0
        total_bytes_scanned = 0
        dormant_bytes = 0

        # Directories to skip when skip_system_dirs is True
        system_skip_names = {
            '$recycle.bin', 'system volume information', 'recovery',
            'windows', 'winsxs', 'servicing', 'assembly'
        }

        # Prioritize high-value user data folders first
        high_priority_names = {
            'downloads', 'documents', 'desktop', 'videos', 'music', 'pictures',
            'modelfiles', '.ollama', 'projects', 'pycharmprojects', 'ideaprojects',
            'saved games', 'temp', '.gradle'
        }

        # Directories known for millions of tiny files that users rarely want to clear individually
        # unless specifically targeted
        cache_noise_skips = {
            'node_modules', '.git', 'winsxs', 'envs', 'venv', '.venv',
            'site-packages', '__pycache__', '.pytest_cache', '.mypy_cache',
            '.npm', '.cargo', '.rustup', 'packages',
            'microsoft\\windows', 'edge\\user data', 'google\\chrome\\user data'
        }

        # Queue for breadth-first scan (deque-like with priority)
        queue = [os.path.abspath(target_path)]

        try:
            while queue and not self.stop_requested:
                current_dir = queue.pop(0)
                dirs_scanned += 1
                
                # Update progress periodically
                if dirs_scanned % 50 == 0:
                    with self._lock:
                        self.progress["dirs_scanned"] = dirs_scanned
                        self.progress["files_scanned"] = files_scanned
                        self.progress["total_bytes_scanned"] = total_bytes_scanned
                        self.progress["dormant_found"] = len(found_files)
                        self.progress["dormant_bytes"] = dormant_bytes
                        self.progress["current_dir"] = current_dir
                        elapsed = max(0.1, time.time() - self._start_time)
                        self.progress["elapsed_seconds"] = round(elapsed, 1)
                        self.progress["scan_rate_fps"] = int(files_scanned / elapsed)

                subdirs_high = []
                subdirs_low = []
                try:
                    with os.scandir(current_dir) as iterator:
                        for entry in iterator:
                            if self.stop_requested:
                                break

                            try:
                                # Check symlink/reparse point
                                if entry.is_symlink():
                                    continue

                                if entry.is_file(follow_symlinks=False):
                                    files_scanned += 1
                                    st = entry.stat(follow_symlinks=False)
                                    file_size = st.st_size
                                    total_bytes_scanned += file_size

                                    # Fast size check first
                                    if file_size < min_size_bytes:
                                        continue

                                    # Calculate dormancy
                                    mtime = st.st_mtime
                                    atime = st.st_atime
                                    ctime = getattr(st, 'st_ctime', mtime)

                                    if date_basis == "mtime":
                                        effective_time = mtime
                                    elif date_basis == "atime":
                                        effective_time = atime
                                    else: # effective
                                        effective_time = max(mtime, atime)

                                    days_dormant = int((now - effective_time) / 86400.0)
                                    days_since_mtime = int((now - mtime) / 86400.0)
                                    days_since_atime = int((now - atime) / 86400.0)

                                    if days_dormant >= min_dormant_days:
                                        category = get_file_category(entry.name, entry.path)
                                        safety = assess_safety(entry.path, entry.name)

                                        # Reclaim score = Size in GB * (Days Dormant / 30)
                                        reclaim_score = round((file_size / (1024**3)) * (days_dormant / 30.0), 2)

                                        file_record = {
                                            "id": f"file_{len(found_files)+1}",
                                            "name": entry.name,
                                            "path": entry.path,
                                            "folder": os.path.dirname(entry.path),
                                            "size_bytes": file_size,
                                            "size_mb": round(file_size / (1024*1024), 2),
                                            "size_gb": round(file_size / (1024**3), 3),
                                            "formatted_size": self._format_bytes(file_size),
                                            "mtime": mtime,
                                            "atime": atime,
                                            "ctime": ctime,
                                            "mtime_str": datetime.fromtimestamp(mtime).strftime("%b %d, %Y"),
                                            "atime_str": datetime.fromtimestamp(atime).strftime("%b %d, %Y"),
                                            "days_dormant": days_dormant,
                                            "days_since_mtime": days_since_mtime,
                                            "days_since_atime": days_since_atime,
                                            "category": category,
                                            "safety": safety,
                                            "reclaim_score": reclaim_score
                                        }

                                        found_files.append(file_record)
                                        dormant_bytes += file_size

                                        if len(found_files) >= max_results:
                                            break

                                elif entry.is_dir(follow_symlinks=False):
                                    dirname_lower = entry.name.lower()
                                    
                                    # Skip system directories if flagged
                                    if skip_system_dirs and dirname_lower in system_skip_names:
                                        continue
                                    if dirname_lower in cache_noise_skips or any(k in entry.path.lower() for k in cache_noise_skips):
                                        continue
                                        
                                    if dirname_lower in high_priority_names:
                                        subdirs_high.append(entry.path)
                                    else:
                                        subdirs_low.append(entry.path)

                            except (PermissionError, FileNotFoundError, OSError):
                                continue

                    # High priority subdirectories processed first
                    queue = subdirs_high + queue + subdirs_low
                except (PermissionError, FileNotFoundError, OSError):
                    continue

        except Exception as e:
            with self._lock:
                self.progress["status_message"] = f"Scan stopped: {str(e)}"
        finally:
            # Sort files descending by size
            found_files.sort(key=lambda x: x["size_bytes"], reverse=True)
            
            # Compute analytics
            analytics = self._compute_analytics(found_files, dormant_bytes)

            with self._lock:
                self.is_scanning = False
                self.results = found_files
                self.analytics = analytics
                self.progress["is_scanning"] = False
                self.progress["files_scanned"] = files_scanned
                self.progress["dirs_scanned"] = dirs_scanned
                self.progress["total_bytes_scanned"] = total_bytes_scanned
                self.progress["dormant_found"] = len(found_files)
                self.progress["dormant_bytes"] = dormant_bytes
                elapsed = max(0.1, time.time() - self._start_time)
                self.progress["elapsed_seconds"] = round(elapsed, 1)
                self.progress["scan_rate_fps"] = int(files_scanned / elapsed) if elapsed > 0 else 0
                if self.stop_requested:
                    self.progress["status_message"] = f"Scan canceled. Found {len(found_files)} dormant files ({self._format_bytes(dormant_bytes)})."
                else:
                    self.progress["status_message"] = f"Scan complete! Found {len(found_files)} dormant files ({self._format_bytes(dormant_bytes)})."

    def _compute_analytics(self, files: List[Dict[str, Any]], total_dormant_bytes: int) -> Dict[str, Any]:
        """Calculates rich metrics for presentation and charts."""
        drive_info = self.get_c_drive_info()
        total_dormant_gb = round(total_dormant_bytes / (1024**3), 2)
        
        # Age distribution
        age_buckets = {
            "> 2 Years": {"count": 0, "bytes": 0, "color": "#ef4444"},
            "1 - 2 Years": {"count": 0, "bytes": 0, "color": "#f97316"},
            "6 - 12 Months": {"count": 0, "bytes": 0, "color": "#f59e0b"},
            "3 - 6 Months": {"count": 0, "bytes": 0, "color": "#10b981"},
            "1 - 3 Months": {"count": 0, "bytes": 0, "color": "#3b82f6"}
        }

        # Category breakdown
        category_stats: Dict[str, Dict[str, Any]] = {}
        
        # Folder breakdown (Top parent folders)
        folder_stats: Dict[str, int] = {}

        # Safety breakdown
        safety_stats = {
            "safe": {"label": "Safe to Clean", "count": 0, "bytes": 0, "color": "#10b981"},
            "review": {"label": "Review Needed", "count": 0, "bytes": 0, "color": "#3b82f6"},
            "caution": {"label": "Installed Application", "count": 0, "bytes": 0, "color": "#f97316"},
            "system": {"label": "System Protected", "count": 0, "bytes": 0, "color": "#ef4444"}
        }

        for f in files:
            d = f["days_dormant"]
            sz = f["size_bytes"]

            # Age
            if d >= 730:
                age_buckets["> 2 Years"]["count"] += 1
                age_buckets["> 2 Years"]["bytes"] += sz
            elif d >= 365:
                age_buckets["1 - 2 Years"]["count"] += 1
                age_buckets["1 - 2 Years"]["bytes"] += sz
            elif d >= 180:
                age_buckets["6 - 12 Months"]["count"] += 1
                age_buckets["6 - 12 Months"]["bytes"] += sz
            elif d >= 90:
                age_buckets["3 - 6 Months"]["count"] += 1
                age_buckets["3 - 6 Months"]["bytes"] += sz
            else:
                age_buckets["1 - 3 Months"]["count"] += 1
                age_buckets["1 - 3 Months"]["bytes"] += sz

            # Category
            cat = f["category"]
            if cat not in category_stats:
                category_stats[cat] = {"count": 0, "bytes": 0, "icon": CATEGORIES.get(cat, {}).get("icon", "📁")}
            category_stats[cat]["count"] += 1
            category_stats[cat]["bytes"] += sz

            # Folder (shorten to top 2-3 levels)
            folder_parts = f["path"].split(os.sep)
            if len(folder_parts) > 3:
                top_folder = os.sep.join(folder_parts[:3])
            else:
                top_folder = os.path.dirname(f["path"])
            folder_stats[top_folder] = folder_stats.get(top_folder, 0) + sz

            # Safety
            lvl = f["safety"]["level"]
            if lvl in safety_stats:
                safety_stats[lvl]["count"] += 1
                safety_stats[lvl]["bytes"] += sz

        # Convert age buckets to list for charts
        age_list = []
        for name, data in age_buckets.items():
            age_list.append({
                "label": name,
                "count": data["count"],
                "bytes": data["bytes"],
                "gb": round(data["bytes"] / (1024**3), 2),
                "formatted": self._format_bytes(data["bytes"]),
                "color": data["color"]
            })

        # Convert category to sorted list
        cat_list = []
        for name, data in category_stats.items():
            cat_list.append({
                "category": name,
                "icon": data["icon"],
                "count": data["count"],
                "bytes": data["bytes"],
                "gb": round(data["bytes"] / (1024**3), 2),
                "formatted": self._format_bytes(data["bytes"]),
                "pct": round((data["bytes"] / total_dormant_bytes * 100), 1) if total_dormant_bytes > 0 else 0
            })
        cat_list.sort(key=lambda x: x["bytes"], reverse=True)

        # Convert folders to sorted list
        folder_list = []
        for fld, b in folder_stats.items():
            folder_list.append({
                "folder": fld,
                "bytes": b,
                "gb": round(b / (1024**3), 2),
                "formatted": self._format_bytes(b),
                "pct": round((b / total_dormant_bytes * 100), 1) if total_dormant_bytes > 0 else 0
            })
        folder_list.sort(key=lambda x: x["bytes"], reverse=True)

        # Convert safety to list
        safety_list = []
        for key, data in safety_stats.items():
            safety_list.append({
                "key": key,
                "label": data["label"],
                "count": data["count"],
                "bytes": data["bytes"],
                "gb": round(data["bytes"] / (1024**3), 2),
                "formatted": self._format_bytes(data["bytes"]),
                "color": data["color"],
                "pct": round((data["bytes"] / total_dormant_bytes * 100), 1) if total_dormant_bytes > 0 else 0
            })

        # Top 10 space wasters
        top_10 = files[:10]

        # Potential space reclaim percentage of C: drive used space
        c_used = drive_info.get("used_bytes", 1)
        reclaim_of_used_pct = round((total_dormant_bytes / c_used) * 100, 1) if c_used > 0 else 0

        # Safe immediate savings (safe level files only)
        safe_bytes = safety_stats["safe"]["bytes"]
        safe_gb = round(safe_bytes / (1024**3), 2)

        return {
            "total_dormant_files": len(files),
            "total_dormant_bytes": total_dormant_bytes,
            "total_dormant_gb": total_dormant_gb,
            "total_dormant_formatted": self._format_bytes(total_dormant_bytes),
            "safe_bytes": safe_bytes,
            "safe_gb": safe_gb,
            "safe_formatted": self._format_bytes(safe_bytes),
            "reclaim_of_used_pct": reclaim_of_used_pct,
            "age_distribution": age_list,
            "category_distribution": cat_list,
            "folder_distribution": folder_list[:8],
            "safety_distribution": safety_list,
            "top_space_wasters": top_10
        }

    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024**2:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024**3:
            return f"{bytes_val / (1024**2):.1f} MB"
        else:
            return f"{bytes_val / (1024**3):.2f} GB"
