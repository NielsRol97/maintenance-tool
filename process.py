from __future__ import annotations
import subprocess
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class ProcResult:
    returncode: int
    stdout: str
    stderr: str


def run_command(
    cmd: list[str],
    *,
    logger,
    cancel_event,
    allow_terminate: bool,
    shell: bool = False,
) -> ProcResult:
    """
    Runs a command and streams output line-by-line to the logger.
    Cancel behavior:
      - If allow_terminate=True: we try to terminate/kill on cancel.
      - If False: we log cancel request but let the command finish safely.
    """
    logger.info("▶ " + " ".join(cmd))

    p = subprocess.Popen(
        cmd,
        shell=shell,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    out_lines: list[str] = []
    err_lines: list[str] = []

    # Non-blocking-ish read loop
    while True:
        if cancel_event.is_set() and allow_terminate:
            logger.warn("⏹ Cancel requested — terminating current process…")
            try:
                p.terminate()
                time.sleep(0.8)
                if p.poll() is None:
                    p.kill()
            except Exception:
                pass

        # Read available output without blocking too hard
        if p.stdout:
            line = p.stdout.readline()
            if line:
                line = line.rstrip("\n")
                out_lines.append(line)
                logger.info(line)
        if p.stderr:
            eline = p.stderr.readline()
            if eline:
                eline = eline.rstrip("\n")
                err_lines.append(eline)
                logger.warn(eline)

        rc = p.poll()
        if rc is not None:
            # Drain remainder
            try:
                rest_out, rest_err = p.communicate(timeout=5)
                if rest_out:
                    for ln in rest_out.splitlines():
                        out_lines.append(ln)
                if rest_err:
                    for ln in rest_err.splitlines():
                        err_lines.append(ln)
            except Exception:
                pass
            break

        time.sleep(0.05)

    rc = p.returncode if p.returncode is not None else 1
    return ProcResult(rc, "\n".join(out_lines), "\n".join(err_lines))
