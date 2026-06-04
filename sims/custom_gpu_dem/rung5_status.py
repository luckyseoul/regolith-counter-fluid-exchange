#!/usr/bin/env python3
"""
Rung 0 Status Bar - quick check for the live GPU DEM backfill.

Usage:
  python rung5_status.py
  watch -n 5 python rung5_status.py     # auto-refresh every 5s
  cat /tmp/rung5_status.txt             # even faster one-shot check

Also writes a fresh /tmp/rung5_status.txt every run.

Only post-containment (inside=100.0%, zmin>=0) numbers are citable.
"""

import os
import re
import glob
import subprocess
import time
from pathlib import Path

import numpy as np

TARGET = 500000
BASE = Path(__file__).resolve().parent
CKPT_DIR = BASE / "rung5_checkpoints"
LOG_PATH = Path("/tmp/rung5_slice.log")

def format_bar(pct: float, width: int = 50) -> str:
    if pct >= 100:
        return "[" + "=" * width + "]"
    filled = int(pct / 100 * (width - 1))
    return "[" + "=" * filled + ">" + " " * (width - 1 - filled) + "]"

def get_latest_ckpt():
    files = list(CKPT_DIR.glob("rung5_step*.npz"))
    if not files:
        return None, 0
    def sn(p):
        m = re.search(r"step(\d+)", p.name)
        return int(m.group(1)) if m else 0
    latest = max(files, key=sn)
    return latest, sn(latest)

def compute_ckpt_stats(ckpt_path: Path):
    try:
        data = np.load(ckpt_path)
        pos = data["pos"]
        vel = data.get("vel", np.zeros_like(pos))
        bed = float(np.mean(pos[:, 2]) * 1000)
        bed_std = float(np.std(pos[:, 2]) * 1000)
        zmin = float(np.min(pos[:, 2]) * 1000)
        zmax = float(np.max(pos[:, 2]) * 1000)
        inside_mask = (
            (pos[:, 0] >= 0) & (pos[:, 0] <= 0.016) &
            (pos[:, 1] >= 0) & (pos[:, 1] <= 0.016) &
            (pos[:, 2] >= 0)
        )
        inside = 100.0 * float(np.sum(inside_mask)) / len(pos)
        vel_norm = np.linalg.norm(vel, axis=1)
        low_v = float(np.sum(vel_norm < 0.8))
        dead = (low_v / len(pos)) * 100.0
        contained = (inside >= 99.9 and zmin >= 0.0)
        return {
            "bed": bed, "bed_std": bed_std,
            "zmin": zmin, "zmax": zmax,
            "inside": inside, "dead": dead,
            "contained": contained,
            "n": len(pos)
        }
    except Exception as e:
        return {"error": str(e)}

def parse_log():
    if not LOG_PATH.exists():
        return {"current_step": 0, "last_bed_line": "", "is_done": False, "resumed_from": 0}

    try:
        with open(LOG_PATH, "r", errors="ignore") as f:
            lines = f.readlines()[-300:]  # recent tail for speed
    except Exception:
        lines = []

    current_step = 0
    last_bed_line = ""
    is_done = False
    resumed_from = 0

    for line in lines:
        if "rung5 done" in line.lower():
            is_done = True
        m_res = re.search(r"Resuming Rung 0 from .* \(step (\d+)\)", line)
        if m_res:
            resumed_from = int(m_res.group(1))
        m = re.search(r"step\s+(\d+)", line)
        if m:
            s = int(m.group(1))
            if s > current_step:
                current_step = s
        if "bed=" in line and "step " in line:
            last_bed_line = line.strip()

    # fallback to highest seen
    if not current_step and resumed_from:
        current_step = resumed_from

    return {
        "current_step": current_step,
        "last_bed_line": last_bed_line,
        "is_done": is_done,
        "resumed_from": resumed_from
    }

def get_process_and_gpu():
    pid = None
    etime = "?"
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,etime,cmd", "--no-headers"],
            text=True, stderr=subprocess.DEVNULL
        )
        for line in out.splitlines():
            if "run_rung5_sensitivity_stub" in line and "python" in line and "grep" not in line.lower():
                parts = line.split(None, 2)
                if len(parts) >= 2:
                    pid = parts[0]
                    etime = parts[1]
                break
    except Exception:
        pass

    gpu_line = "n/a"
    try:
        g = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        parts = [x.strip() for x in g.split(",")]
        if len(parts) >= 3:
            util = parts[0]
            used = float(parts[1]) / 1024.0
            total = float(parts[2]) / 1024.0
            gpu_line = f"{util}%  {used:.1f}/{total:.1f} GB"
        else:
            gpu_line = g
    except Exception:
        pass

    alive = pid is not None
    return {"pid": pid, "etime": etime, "alive": alive, "gpu": gpu_line}

def compute_rate_and_eta(ckpt_files):
    if len(ckpt_files) < 2:
        return 0.0, "n/a (need more ckpts)"
    def sn(p):
        m = re.search(r"step(\d+)", p.name)
        return int(m.group(1)) if m else 0
    sorted_c = sorted(ckpt_files, key=sn)
    # Use last up to 4 ckpts for a more stable window (avoids tiny mtime deltas)
    window = sorted_c[-4:] if len(sorted_c) >= 4 else sorted_c[-2:]
    if len(window) < 2:
        return 0.0, "n/a"
    s1, s2 = sn(window[0]), sn(window[-1])
    t1 = window[0].stat().st_mtime
    t2 = window[-1].stat().st_mtime
    if t2 <= t1 or s2 <= s1:
        return 0.0, "n/a"
    rate = (s2 - s1) / (t2 - t1) * 60.0  # steps/min
    log_info = parse_log()
    cur = max(s2, log_info["current_step"])
    remain = TARGET - cur
    if rate > 5:  # realistic floor
        eta_min = remain / rate
        if eta_min > 90:
            eta = f"{eta_min/60:.1f} h"
        else:
            eta = f"{eta_min:.0f} min"
    else:
        eta = "n/a (rate stabilizing / early phase)"
    return rate, eta

def main():
    log_info = parse_log()
    latest_ckpt, ckpt_step = get_latest_ckpt()
    stats = compute_ckpt_stats(latest_ckpt) if latest_ckpt else {}

    ckpt_files = list(CKPT_DIR.glob("rung5_step*.npz"))
    rate, eta = compute_rate_and_eta(ckpt_files)

    proc = get_process_and_gpu()

    cur_step = max(ckpt_step, log_info["current_step"])
    pct = (cur_step / TARGET) * 100.0 if TARGET > 0 else 0.0
    bar = format_bar(pct)

    remain = TARGET - cur_step

    # Build output
    lines = []
    lines.append("Rung 5 Real DEM Sensitivity — Status Bar (identical physics to Rung 0/1/2)")
    lines.append("=" * 72)
    lines.append(f"Progress: {bar} {pct:5.2f}%   ({cur_step:,} / {TARGET:,})   remain: {remain:,}")
    lines.append(f"ETA (rough from recent ckpt rate): {eta}   ~{rate:.0f} steps/min")
    lines.append("")

    if log_info["last_bed_line"]:
        lines.append("Latest printed (log):")
        lines.append("  " + log_info["last_bed_line"])
        lines.append("")

    if stats and "error" not in stats:
        c = "✅ YES — Citable (contained)" if stats["contained"] else "❌ NO — do not cite"
        lines.append(f"Latest ckpt {latest_ckpt.name} (step {ckpt_step}):")
        lines.append(f"  bed = {stats['bed']:.2f}±{stats['bed_std']:.2f} mm")
        lines.append(f"  zmin={stats['zmin']:.2f}mm  zmax={stats['zmax']:.0f}mm  inside={stats['inside']:.1f}%  dead%={stats['dead']:.1f}")
        lines.append(f"  CONTAINED: {c}")
        lines.append("")

    alive_str = "✅ ALIVE" if proc["alive"] else "❌ NOT RUNNING"
    lines.append(f"Process: {alive_str}  pid={proc['pid']}  etime={proc['etime']}")
    lines.append(f"GPU: {proc['gpu']}")
    monitor_note = "(run complete, no active monitor)" if log_info["is_done"] else "(monitor active)"
    lines.append(f"Log: {LOG_PATH}   {monitor_note}")
    lines.append("")

    if log_info["is_done"]:
        lines.append("*** RUN COMPLETE — check final 'rung5 done' line ***")
    else:
        lines.append("Only 100.0% inside + zmin>=0 numbers are citable for patent evidence.")
        lines.append("Run this often:  python rung5_status.py   |   watch -n 5 python rung5_status.py")
        lines.append("Fast check:  cat /tmp/rung5_status.txt")

    output = "\n".join(lines)
    print(output)

    # Also write the file for instant cat
    try:
        with open("/tmp/rung5_status.txt", "w") as f:
            f.write(output + "\n")
            f.write(f"\n(updated {time.strftime('%Y-%m-%d %H:%M:%S')})\n")
    except Exception:
        pass

if __name__ == "__main__":
    main()
