"""
Warp — send files between PC and phone over Wi-Fi.
Run: python app.py
Zero external dependencies.
"""
import os, sys, socket, threading, webbrowser, mimetypes, json, subprocess
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

PORT     = 645
SAVE_DIR = Path.home() / "Warp"
STATIC   = Path(__file__).parent / "static"
SAVE_DIR.mkdir(exist_ok=True)

def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def file_list():
    return [{"name": f.name, "size": f.stat().st_size}
            for f in sorted(SAVE_DIR.iterdir()) if f.is_file()]

def parse_multipart(data: bytes, boundary: bytes):
    parts = []
    for seg in data.split(b"--" + boundary)[1:]:
        if seg.startswith(b"--") or len(seg) < 4: continue
        sep = seg.find(b"\r\n\r\n")
        if sep == -1: continue
        headers = seg[:sep].decode("utf-8", errors="replace")
        body    = seg[sep+4:]
        if body.endswith(b"\r\n"): body = body[:-2]
        for line in headers.splitlines():
            if "filename=" in line:
                fname = line.split("filename=")[-1].strip().strip('"')
                if fname: parts.append((fname, body)); break
    return parts

def safe_path(name):
    dest = SAVE_DIR / Path(name).name
    if dest.exists():
        stem, suf, i = dest.stem, dest.suffix, 1
        while dest.exists(): dest = SAVE_DIR / f"{stem}_{i}{suf}"; i += 1
    return dest

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def json(self, data, code=200):
        b = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(b))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers(); self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        p = urlparse(self.path).path.rstrip("/") or "/"

        if p == "/api/info":
            ip = local_ip()
            self.json({"ip": ip, "port": PORT,
                       "url": f"http://{ip}:{PORT}",
                       "files": file_list()}); return

        if p.startswith("/api/download/"):
            name   = unquote(p.removeprefix("/api/download/"))
            target = (SAVE_DIR / name).resolve()
            if not str(target).startswith(str(SAVE_DIR)) or not target.is_file():
                self.json({"error": "not found"}, 404); return
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", f'attachment; filename="{name}"')
            self.send_header("Content-Length", len(data))
            self.end_headers(); self.wfile.write(data); return

        if p == "/api/open-folder":
            d = str(SAVE_DIR)
            if sys.platform == "win32":    os.startfile(d)
            elif sys.platform == "darwin": subprocess.Popen(["open", d])
            else:                          subprocess.Popen(["xdg-open", d])
            self.json({"ok": True}); return

        f = STATIC / "index.html" if p in ("/", "/index.html") else STATIC / p.lstrip("/")
        if f.exists() and f.is_file():
            data = f.read_bytes()
            mime = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", len(data))
            self.end_headers(); self.wfile.write(data); return

        self.json({"error": "not found"}, 404)

    def do_POST(self):
        if urlparse(self.path).path != "/api/upload":
            self.json({"error": "not found"}, 404); return
        ct  = self.headers.get("Content-Type", "")
        if "boundary=" not in ct:
            self.json({"error": "bad request"}, 400); return
        body     = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        boundary = ct.split("boundary=")[-1].strip().encode()
        saved = []
        for fname, data in parse_multipart(body, boundary):
            dest = safe_path(fname)
            dest.write_bytes(data)
            saved.append({"name": dest.name, "size": len(data)})
            print(f"  ✓  {dest.name}  ({len(data):,} B)")
        self.json({"saved": saved})

    def do_DELETE(self):
        p = urlparse(self.path).path
        if not p.startswith("/api/delete/"):
            self.json({"error": "not found"}, 404); return
        name   = unquote(p.removeprefix("/api/delete/"))
        target = (SAVE_DIR / name).resolve()
        if not str(target).startswith(str(SAVE_DIR)):
            self.json({"error": "forbidden"}, 403); return
        if target.exists(): target.unlink(); print(f"  🗑  {name}")
        self.json({"ok": True})

if __name__ == "__main__":
    ip  = local_ip()
    pc  = f"http://localhost:{PORT}"
    mob = f"http://{ip}:{PORT}"
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║              Warp                        ║")
    print("  ╠══════════════════════════════════════════╣")
    print(f"  ║  PC     →  {pc:<30}║")
    print(f"  ║  Phone  →  {mob:<30}║")
    print(f"  ║  Files  →  {str(SAVE_DIR):<30}║")
    print("  ╠══════════════════════════════════════════╣")
    print("  ║  Ctrl+C to stop                          ║")
    print("  ╚══════════════════════════════════════════╝")
    print()
    threading.Timer(1.2, lambda: webbrowser.open(pc)).start()
    try:
        HTTPServer(("0.0.0.0", PORT), H).serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
