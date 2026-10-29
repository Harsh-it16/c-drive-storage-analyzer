"""
C-Drive Dormant File Analyzer - Main Application & Server
Runs a lightweight local web server with full REST APIs, Windows File Explorer integration,
and executive presentation reporting.
"""

import os
import sys
import json
import time
import urllib.parse
import subprocess
import webbrowser
import ctypes
from ctypes import wintypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import csv
import io

from scanner import DriveScanner

PORT = 8765
scanner = DriveScanner()
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

def reveal_in_explorer(target_path: str, mode: str = "select") -> tuple[bool, str, dict]:
    """
    Opens Windows File Explorer and selects/highlights the target file.
    If mode == 'folder', or if the file does not exist, or if the file is a system/hidden
    protected file (hiberfil, pagefile, etc. where /select causes Explorer to open This PC),
    reliably redirects and opens the containing folder directly.
    Uses AllowSetForegroundWindow and ShellExecuteW with full binary path and working directory.
    """
    if not target_path:
        return False, "No path provided.", {}

    norm = os.path.normpath(os.path.abspath(target_path))
    folder = norm if os.path.isdir(norm) else os.path.dirname(norm)
    
    # If folder doesn't exist on disk, walk up to the nearest valid parent folder
    curr = folder
    while curr and not os.path.exists(curr):
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent
    if not curr or not os.path.exists(curr):
        curr = "C:\\"
    folder = curr

    file_exists = os.path.isfile(norm)
    norm_lower = norm.lower()
    is_system_protected = any(k in norm_lower for k in [
        "hiberfil.sys", "pagefile.sys", "swapfile.sys", "dumpstack.log", "bootmgr", "ntuser.dat"
    ])

    metadata = {
        "path": norm,
        "folder": folder,
        "file_url": f"file:///{norm.replace(os.sep, '/')}",
        "folder_url": f"file:///{folder.replace(os.sep, '/')}",
        "exists": file_exists,
        "is_system": is_system_protected
    }

    explorer_bin = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "explorer.exe")

    # If folder mode requested, or file is missing, or file is a hidden/system OS file:
    # Always open folder directly so Windows Explorer reliably navigates to the target folder!
    if mode == "folder" or not file_exists or is_system_protected:
        args = f'"{folder}"'
        action_desc = f"Redirected to folder in File Explorer: {folder}"
        metadata["mode"] = "folder"
    else:
        args = f'/select,"{norm}"'
        action_desc = f"Revealed and selected in File Explorer: {norm}"
        metadata["mode"] = "select"

    # Allow newly created or existing Explorer window to take the foreground over the browser
    try:
        ctypes.windll.user32.AllowSetForegroundWindow(0xFFFFFFFF)
    except Exception:
        pass

    # Method 1: ShellExecuteW with working directory set to target folder
    try:
        ret = ctypes.windll.shell32.ShellExecuteW(None, "open", explorer_bin, args, folder, 1)
        if ret > 32:
            return True, action_desc, metadata
    except Exception:
        pass

    # Method 2: Subprocess with full binary path and cwd
    try:
        subprocess.Popen(f'"{explorer_bin}" {args}', cwd=folder)
        return True, action_desc, metadata
    except Exception as e:
        # Method 3: Fallback to os.startfile on the folder
        try:
            os.startfile(folder)
            return True, f"Opened containing folder: {folder}", metadata
        except Exception as e2:
            return False, f"Failed to launch File Explorer: {str(e2)}", metadata

class ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class AnalyzerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Clean logging
        return

    def _send_json(self, data: dict, status_code: int = 200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._serve_file(os.path.join(STATIC_DIR, "index.html"), "text/html; charset=utf-8")
        elif path == "/style.css":
            self._serve_file(os.path.join(STATIC_DIR, "style.css"), "text/css; charset=utf-8")
        elif path == "/app.js":
            self._serve_file(os.path.join(STATIC_DIR, "app.js"), "application/javascript; charset=utf-8")
        elif path == "/api/drive-info":
            self._send_json(scanner.get_c_drive_info())
        elif path == "/api/presets":
            self._send_json({"presets": scanner.get_presets()})
        elif path == "/api/scan/status":
            self._send_json(scanner.get_status())
        elif path == "/api/scan/results":
            self._send_json(scanner.get_results())
        elif path == "/api/export/csv":
            self._handle_export_csv()
        elif path == "/api/export/presentation":
            self._handle_export_presentation()
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        
        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}

        if path == "/api/scan/start":
            target_path = data.get("target_path", "C:\\")
            min_size_mb = float(data.get("min_size_mb", 25.0))
            min_dormant_days = int(data.get("min_dormant_days", 60))
            date_basis = data.get("date_basis", "effective")
            skip_system_dirs = bool(data.get("skip_system_dirs", True))
            max_results = int(data.get("max_results", 5000))

            success = scanner.start_scan(
                target_path=target_path,
                min_size_mb=min_size_mb,
                min_dormant_days=min_dormant_days,
                date_basis=date_basis,
                skip_system_dirs=skip_system_dirs,
                max_results=max_results
            )
            self._send_json({"success": success, "message": "Scan started" if success else "Scan already in progress"})

        elif path == "/api/scan/stop":
            scanner.stop_scan()
            self._send_json({"success": True, "message": "Stopping scan"})

        elif path == "/api/open-explorer":
            file_path = data.get("path", "")
            mode = data.get("mode", "select")
            if not file_path:
                self._send_json({"success": False, "error": "No file path provided"}, 400)
                return

            ok, msg, meta = reveal_in_explorer(file_path, mode=mode)
            if ok:
                self._send_json({
                    "success": True,
                    "message": msg,
                    "path": meta.get("path", file_path),
                    "folder": meta.get("folder", ""),
                    "file_url": meta.get("file_url", ""),
                    "folder_url": meta.get("folder_url", "")
                })
            else:
                self._send_json({"success": False, "error": msg, "meta": meta}, 400)

        elif path == "/api/delete-file":
            file_path = data.get("path", "")
            permanent = bool(data.get("permanent", False))
            if not file_path:
                self._send_json({"success": False, "error": "No file path specified"}, 400)
                return

            ok, msg, freed_bytes, is_access_denied = scanner.delete_file(file_path, permanent=permanent)
            if ok:
                self._send_json({
                    "success": True,
                    "message": msg,
                    "freed_bytes": freed_bytes,
                    "path": file_path,
                    "analytics": scanner.analytics,
                    "drive_info": scanner.get_c_drive_info()
                })
            else:
                self._send_json({
                    "success": False,
                    "error": msg,
                    "is_access_denied": is_access_denied,
                    "path": file_path,
                    "folder": os.path.dirname(file_path),
                    "suggestion": "Windows blocked deletion because this file requires elevated administrator permissions or is locked by a running process. Open the location in Windows File Explorer to delete or unlock it manually."
                }, 403 if is_access_denied else 400)
        else:
            self.send_error(404, "Unknown endpoint")

    def _serve_file(self, filepath: str, content_type: str):
        if not os.path.exists(filepath):
            self.send_error(404, "File Not Found")
            return
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading file: {str(e)}")

    def _handle_export_csv(self):
        results = scanner.get_results().get("results", [])
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["File Name", "Full C: Path", "Folder", "Size (MB)", "Size (GB)", "Days Dormant", "Last Modified", "Last Accessed", "Category", "Safety Level", "Recommendation"])

        for f in results:
            writer.writerow([
                f.get("name", ""),
                f.get("path", ""),
                f.get("folder", ""),
                f.get("size_mb", 0),
                f.get("size_gb", 0),
                f.get("days_dormant", 0),
                f.get("mtime_str", ""),
                f.get("atime_str", ""),
                f.get("category", ""),
                f.get("safety", {}).get("level", ""),
                f.get("safety", {}).get("advice", "")
            ])

        csv_bytes = output.getvalue().encode("utf-8-sig") # with BOM for Excel
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="C_Drive_Dormant_Files_Report.csv"')
        self.send_header("Content-Length", str(len(csv_bytes)))
        self.end_headers()
        self.wfile.write(csv_bytes)

    def _handle_export_presentation(self):
        """Generates a standalone, presentation-ready executive HTML report."""
        res_data = scanner.get_results()
        html = generate_standalone_presentation_html(res_data)
        html_bytes = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Disposition", 'attachment; filename="C_Drive_Executive_Presentation.html"')
        self.send_header("Content-Length", str(len(html_bytes)))
        self.end_headers()
        self.wfile.write(html_bytes)

def generate_standalone_presentation_html(data: dict) -> str:
    """Creates a beautiful self-contained slide presentation document from scanned data."""
    drive = data.get("drive_info", {})
    analytics = data.get("analytics", {})
    results = data.get("results", [])
    top_wasters = analytics.get("top_space_wasters", [])[:10]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>C: Drive Disk Audit - Executive Presentation</title>
<style>
  :root {{
    --bg: #090d16;
    --card: #111827;
    --border: #1f293d;
    --text: #f3f4f6;
    --muted: #9ca3af;
    --primary: #3b82f6;
    --accent: #8b5cf6;
    --emerald: #10b981;
    --amber: #f59e0b;
    --rose: #ef4444;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.5;
    padding: 24px;
    min-height: 100vh;
  }}
  .container {{ max-width: 1200px; margin: 0 auto; }}
  header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 32px;
  }}
  .brand {{ display: flex; align-items: center; gap: 12px; }}
  .brand h1 {{ font-size: 24px; font-weight: 700; background: linear-gradient(135deg, #60a5fa, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  .tag {{ font-size: 12px; padding: 4px 10px; background: rgba(59,130,246,0.15); color: #60a5fa; border-radius: 9999px; border: 1px solid rgba(59,130,246,0.3); font-weight: 600; }}
  
  .slide {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 32px;
    margin-bottom: 32px;
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.4);
  }}
  .slide-header {{ display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 24px; }}
  .slide-num {{ font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--primary); }}
  .slide-title {{ font-size: 22px; font-weight: 700; }}
  
  .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .stat-card {{ background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
  .stat-label {{ font-size: 13px; color: var(--muted); margin-bottom: 6px; }}
  .stat-value {{ font-size: 28px; font-weight: 800; color: #fff; }}
  .stat-sub {{ font-size: 12px; color: var(--muted); margin-top: 4px; }}
  
  .progress-wrap {{ background: rgba(255,255,255,0.06); height: 14px; border-radius: 9999px; overflow: hidden; display: flex; margin: 16px 0 8px 0; }}
  .progress-bar {{ height: 100%; transition: width 0.3s; }}
  
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 13px; }}
  th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border); }}
  th {{ color: var(--muted); font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em; }}
  tr:hover td {{ background: rgba(255,255,255,0.02); }}
  .path-cell {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 12px; color: #93c5fd; word-break: break-all; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; }}
  .badge-safe {{ background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }}
  .badge-review {{ background: rgba(59,130,246,0.15); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); }}
  .badge-caution {{ background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }}
  .badge-system {{ background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }}
  
  .recommendations {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px; }}
  .rec-card {{ background: rgba(255,255,255,0.02); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
  .rec-title {{ font-size: 15px; font-weight: 700; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }}
  .rec-body {{ font-size: 13px; color: var(--muted); }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="brand">
      <span style="font-size:28px;">💽</span>
      <div>
        <h1>C: Drive Dormant Space Presentation</h1>
        <p style="font-size:13px; color:var(--muted);">Executive Storage Audit & Reclaim Intelligence</p>
      </div>
    </div>
    <span class="tag">Generated Live Report</span>
  </header>

  <!-- Slide 1 -->
  <div class="slide">
    <div class="slide-header">
      <h2 class="slide-title">Executive Storage Overview</h2>
      <span class="slide-num">Slide 1 of 4</span>
    </div>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">C: Drive Capacity</div>
        <div class="stat-value">{drive.get('total_gb', 0)} GB</div>
        <div class="stat-sub">{drive.get('used_gb', 0)} GB Used ({drive.get('used_pct', 0)}%) &bull; {drive.get('free_gb', 0)} GB Free</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Identified Dormant Waste</div>
        <div class="stat-value" style="color:#60a5fa;">{analytics.get('total_dormant_formatted', '0 B')}</div>
        <div class="stat-sub">{analytics.get('reclaim_of_used_pct', 0)}% of current used space can be reviewed</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Immediate Safe Reclaim</div>
        <div class="stat-value" style="color:#34d399;">{analytics.get('safe_formatted', '0 B')}</div>
        <div class="stat-sub">From downloads, build caches, and old temp archives</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Dormant Files</div>
        <div class="stat-value">{analytics.get('total_dormant_files', len(results))}</div>
        <div class="stat-sub">Untouched space-consuming items on C: drive</div>
      </div>
    </div>

    <div style="margin-top: 24px;">
      <div style="display:flex; justify-content:space-between; font-size:12px; color:var(--muted);">
        <span>C: Drive Consumption Breakdown</span>
        <span>{drive.get('used_pct', 0)}% Occupied</span>
      </div>
      <div class="progress-wrap">
        <div class="progress-bar" style="width: {drive.get('used_pct', 0)}%; background: linear-gradient(90deg, #3b82f6, #8b5cf6);"></div>
      </div>
    </div>
  </div>

  <!-- Slide 2 -->
  <div class="slide">
    <div class="slide-header">
      <h2 class="slide-title">Dormancy Age Spectrum</h2>
      <span class="slide-num">Slide 2 of 4</span>
    </div>
    <p style="font-size:14px; color:var(--muted); margin-bottom:20px;">
      Files categorized by the duration they have sat dormant without modification or user interaction:
    </p>
    <div class="stats-grid">
      {"".join([f'''
      <div class="stat-card" style="border-top: 3px solid {b['color']};">
        <div class="stat-label">{b['label']} Inactive</div>
        <div class="stat-value">{b['formatted']}</div>
        <div class="stat-sub">{b['count']} files untouched</div>
      </div>''' for b in analytics.get('age_distribution', [])])}
    </div>
  </div>

  <!-- Slide 3 -->
  <div class="slide">
    <div class="slide-header">
      <h2 class="slide-title">Top Dormant Culprits &amp; Locations in C:\\</h2>
      <span class="slide-num">Slide 3 of 4</span>
    </div>
    <p style="font-size:14px; color:var(--muted); margin-bottom:12px;">
      The largest inactive files occupying valuable solid-state storage:
    </p>
    <table>
      <thead>
        <tr>
          <th>File Name</th>
          <th>Location on C: Drive</th>
          <th>Size</th>
          <th>Inactive For</th>
          <th>Category</th>
          <th>Safety</th>
        </tr>
      </thead>
      <tbody>
        {"".join([f'''
        <tr>
          <td style="font-weight:600;">{f.get('name')}</td>
          <td class="path-cell">{f.get('path')}</td>
          <td style="font-weight:700; color:#fff;">{f.get('formatted_size')}</td>
          <td><span style="color:#f59e0b; font-weight:600;">{f.get('days_dormant')} days</span></td>
          <td>{f.get('category')}</td>
          <td><span class="badge badge-{f.get('safety', {}).get('level', 'review')}">{f.get('safety', {}).get('badge', 'Review')}</span></td>
        </tr>''' for f in top_wasters])}
      </tbody>
    </table>
  </div>

  <!-- Slide 4 -->
  <div class="slide">
    <div class="slide-header">
      <h2 class="slide-title">Recommended Cleanup Roadmap</h2>
      <span class="slide-num">Slide 4 of 4</span>
    </div>
    <div class="recommendations">
      <div class="rec-card" style="border-left: 4px solid #10b981;">
        <div class="rec-title">
          <span>✅</span>
          <span style="color:#34d399;">Phase 1: Quick Wins (Downloads & Caches)</span>
        </div>
        <div class="rec-body">
          Prune old installers, compressed zip files, and build artifacts (.gradle/caches, .m2) untouched for over 90 days. Estimated savings: <strong>{analytics.get('safe_formatted', '0 B')}</strong>.
        </div>
      </div>
      <div class="rec-card" style="border-left: 4px solid #3b82f6;">
        <div class="rec-title">
          <span>🔍</span>
          <span style="color:#60a5fa;">Phase 2: User Media & Virtual Disks</span>
        </div>
        <div class="rec-body">
          Review dormant high-definition videos, VM disk images (.vmdk, .vhdx), and AI weights (.gguf, .safetensors). Relocate to external storage or cloud archives.
        </div>
      </div>
      <div class="rec-card" style="border-left: 4px solid #f59e0b;">
        <div class="rec-title">
          <span>⚙️</span>
          <span style="color:#fbbf24;">Phase 3: System & Game Storage</span>
        </div>
        <div class="rec-body">
          For hibernation file (hiberfil.sys) or large games, use Windows 11 Storage Sense or uninstall via Windows Settings rather than manual deletion.
        </div>
      </div>
    </div>
  </div>
</div>
</body>
</html>"""

def run_server(port: int = PORT, auto_open: bool = True):
    server_address = ("127.0.0.1", port)
    try:
        httpd = ThreadingSimpleServer(server_address, AnalyzerHandler)
    except OSError:
        # Fallback to alternative port if 8765 is taken
        port = port + 1
        server_address = ("127.0.0.1", port)
        httpd = ThreadingSimpleServer(server_address, AnalyzerHandler)

    url = f"http://127.0.0.1:{port}"
    print("=" * 60)
    print(f" C: Drive Dormant Space Analyzer Server Started!")
    print(f" Dashboard & Presentation View: {url}")
    print("=" * 60)
    print("Press Ctrl+C to stop the server.")

    if auto_open:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="C: Drive Dormant Space Analyzer")
    parser.add_argument("--port", type=int, default=PORT, help="Port to run web server on")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    parser.add_argument("--cli", action="store_true", help="Run a quick scan directly in CLI")
    parser.add_argument("--target", type=str, default="C:\\", help="Target path to scan")
    parser.add_argument("--min-mb", type=float, default=25.0, help="Minimum file size in MB")
    parser.add_argument("--min-days", type=int, default=60, help="Minimum dormant days")
    args = parser.parse_args()

    if args.cli:
        print(f"Starting CLI scan on {args.target} (files >= {args.min_mb} MB, dormant >= {args.min_days} days)...")
        scanner.start_scan(target_path=args.target, min_size_mb=args.min_mb, min_dormant_days=args.min_days)
        while scanner.is_scanning:
            st = scanner.get_status()
            print(f"\rScanned {st['files_scanned']} files | Found {st['dormant_found']} dormant files...", end="", flush=True)
            time.sleep(0.5)
        print("\nScan completed!")
        res = scanner.get_results()
        top = res["analytics"].get("top_space_wasters", [])
        print(f"\nTop Dormant Files found on C: drive:")
        for idx, f in enumerate(top[:10], 1):
            print(f"{idx}. {f['formatted_size']:<10} | {f['days_dormant']:<4} days old | {f['path']}")
    else:
        run_server(port=args.port, auto_open=not args.no_browser)
