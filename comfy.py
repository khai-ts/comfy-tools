"""Comfy Cloud client shared by the generators: API key, HTTP with retries, queue + wait + download,
and a usage log.

The key comes from the COMFY_CLOUD_API_KEY environment variable (or a gitignored .env file next to
this script, for local use). Never commit it.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMFY = os.environ.get("COMFY_CLOUD_URL", "https://cloud.comfy.org")
# rough credit estimate per GPU second (check your Comfy Cloud billing page for the real numbers)
CREDITS_PER_SECOND = 0.266


def api_key():
    key = os.environ.get("COMFY_CLOUD_API_KEY")
    env = HERE / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("=")
            if k.strip() == "COMFY_CLOUD_API_KEY":
                key = v.strip().strip('"').strip("'")
    if not key and sys.platform == "win32":
        import winreg  # a user env var set with setx, before the shell was restarted
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                key = winreg.QueryValueEx(k, "COMFY_CLOUD_API_KEY")[0]
        except OSError:
            key = None
    if not key:
        sys.exit("COMFY_CLOUD_API_KEY is not set (see README: API key)")
    return key.strip()


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_opener = urllib.request.build_opener(_NoRedirect)


def http(path, payload=None, timeout=60):
    """GET (or POST JSON) an /api path, retrying network blips. Downloads that redirect to a
    signed storage URL are followed without sending the key."""
    for attempt in range(4):
        try:
            return _http_once(path, payload, timeout)
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            if isinstance(e, urllib.error.HTTPError) or attempt == 3:
                raise
            print(f"  network hiccup ({e}); retrying", flush=True)
            time.sleep(2 * (attempt + 1))


def _http_once(path, payload, timeout):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"X-API-Key": api_key()}
    if data:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(COMFY + "/api" + path, data=data, headers=headers)
    try:
        with _opener.open(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 303, 307, 308) and e.headers.get("Location"):
            with urllib.request.urlopen(e.headers["Location"], timeout=timeout) as r:
                return r.read()
        sys.exit(f"Comfy Cloud HTTP {e.code} on {path}: {e.read().decode('utf-8', 'replace')[:500]}")


def gpu_seconds(info):
    ts = {m[0]: m[1].get("timestamp") for m in (info.get("execution_status") or {}).get("messages") or []
          if isinstance(m, list) and len(m) == 2 and isinstance(m[1], dict)}
    s, e = ts.get("execution_start"), ts.get("execution_success") or ts.get("execution_error")
    return (e - s) / 1000 if s and e else None


def log_usage(out_dir, name, secs):
    """Append a row to <out_dir>/usage.json: what ran, GPU seconds, estimated credits."""
    path = Path(out_dir) / "usage.json"
    rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    rows.append({"at": time.strftime("%Y-%m-%d %H:%M"), "job": name, "seconds": round(secs or 15, 1),
                 "credits": round((secs or 15) * CREDITS_PER_SECOND, 2), "estimated": secs is None})
    path.write_text(json.dumps(rows, indent=1), encoding="utf-8", newline="\n")


def run(jobs, out_dir, kind, timeout=900):
    """Queue every (name, workflow) job, wait for them, and download each output of `kind`
    ("images" or "audio") to <out_dir>/<name>_<n>.<ext>. Returns the saved paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ids = {}
    for name, wf in jobs:
        res = json.loads(http("/prompt", {"prompt": wf, "client_id": "comfy-tools"}))
        if "prompt_id" not in res:
            sys.exit(f"{name}: rejected: {json.dumps(res)[:500]}")
        ids[name] = res["prompt_id"]
    print(f"queued {len(ids)} job(s)", flush=True)
    saved = []
    deadline = time.time() + timeout
    while ids and time.time() < deadline:
        time.sleep(3)
        for name, jid in list(ids.items()):
            info = json.loads(http(f"/jobs/{jid}"))
            status = info.get("status")
            if status in ("pending", "in_progress", None):
                continue
            del ids[name]
            log_usage(out_dir, name, gpu_seconds(info))
            files = [f for out in (info.get("outputs") or {}).values() if isinstance(out, dict)
                     for f in out.get(kind) or [] if f.get("type", "output") == "output"]
            if status != "completed" or not files:
                print(f"  {name}: FAILED ({status}) {json.dumps(info.get('error') or '')[:300]}")
                continue
            for n, f in enumerate(files, 1):
                q = urllib.parse.urlencode({"filename": f["filename"], "subfolder": f.get("subfolder", ""),
                                            "type": "output"})
                dest = out_dir / f"{name}_{n}{Path(f['filename']).suffix}"
                dest.write_bytes(http(f"/view?{q}", timeout=180))
                saved.append(dest)
                print(f"  saved {dest}", flush=True)
    if ids:
        print(f"  still running after {timeout // 60} min: {', '.join(ids)} (check Comfy Cloud)")
    return saved
