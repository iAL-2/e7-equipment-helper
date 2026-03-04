# src/adb_control.py
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass(frozen=True)
class ADBConfig:
    adb_path: Optional[str] = None          # None => auto-detect
    host: str = "127.0.0.1"
    port: int = 5555                        # LDPlayer commonly
    prefer_serial: Optional[str] = "127.0.0.1:5555"  # your known good serial


class ADBError(RuntimeError):
    pass


def _find_adb(adb_path: Optional[str]) -> str:
    if adb_path and Path(adb_path).exists():
        return adb_path

    which = shutil.which("adb")
    if which:
        return which

    # common install location in your setup
    fallback = r"C:\Android\platform-tools\adb.exe"
    if Path(fallback).exists():
        return fallback

    raise ADBError("adb not found. Put adb on PATH or set ADBConfig.adb_path to adb.exe")


def _run(adb: str, args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run([adb, *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=check)


def adb_start_server(cfg: ADBConfig) -> str:
    adb = _find_adb(cfg.adb_path)
    _run(adb, ["start-server"], check=True)
    return adb


def adb_connect(cfg: ADBConfig) -> None:
    adb = _find_adb(cfg.adb_path)
    _run(adb, ["kill-server"], check=False)
    _run(adb, ["start-server"], check=True)

    target = f"{cfg.host}:{cfg.port}"
    cp = _run(adb, ["connect", target], check=False)
    # connected / already connected are both fine
    out = (cp.stdout + cp.stderr).lower()
    if "connected" not in out and "already connected" not in out:
        raise ADBError(f"adb connect failed for {target}: {cp.stdout}{cp.stderr}")


def adb_list_devices(cfg: ADBConfig) -> List[str]:
    adb = _find_adb(cfg.adb_path)
    cp = _run(adb, ["devices"], check=True)
    lines = [ln.strip() for ln in cp.stdout.splitlines() if ln.strip()]
    # first line is header: "List of devices attached"
    serials: List[str] = []
    for ln in lines[1:]:
        parts = ln.split()
        if len(parts) >= 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def adb_pick_serial(cfg: ADBConfig) -> str:
    serials = adb_list_devices(cfg)
    if not serials:
        raise ADBError("No adb devices. Ensure LDPlayer is running and ADB is enabled, then retry.")

    if cfg.prefer_serial and cfg.prefer_serial in serials:
        return cfg.prefer_serial

    # If you have multiple, prefer localhost serials
    for s in serials:
        if s.startswith("127.0.0.1:"):
            return s
    return serials[0]


def adb_screencap_png(cfg: ADBConfig, out_path: Path) -> str:
    """
    Writes a valid PNG screenshot to out_path. Returns the device serial used.
    Uses binary stdout capture to avoid PowerShell redirection issues.
    """
    adb = _find_adb(cfg.adb_path)
    serial = adb_pick_serial(cfg)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cp = subprocess.run(
        [adb, "-s", serial, "exec-out", "screencap", "-p"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    if not cp.stdout or len(cp.stdout) < 8:
        raise ADBError(f"screencap returned empty output: {cp.stderr.decode(errors='ignore')}")

    out_path.write_bytes(cp.stdout)

    # PNG magic bytes check
    if out_path.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
        raise ADBError(f"Screenshot is not a valid PNG (magic bytes mismatch): {out_path}")

    return serial