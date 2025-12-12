from __future__ import annotations
import os
import sys
from process import run_command

TASK_NAME = "MaintenanceTool"


def _target():
    if getattr(sys, "frozen", False):
        return sys.executable, ""
    return sys.executable, f'"{os.path.abspath(sys.argv[0])}"'


def install_daily(ctx, hhmm: str) -> None:
    exe, args = _target()
    tr = f'"{exe}" {args}'.strip()
    cmd = [
        "schtasks", "/Create", "/F",
        "/TN", TASK_NAME,
        "/SC", "DAILY",
        "/ST", hhmm,
        "/RL", "HIGHEST",
        "/TR", tr
    ]
    if ctx.dry_run:
        ctx.logger.info(
            f"(dry-run) Would create scheduled task: {TASK_NAME} at {hhmm}")
        ctx.logger.info("▶ " + " ".join(cmd))
        return

    res = run_command(cmd, logger=ctx.logger,
                      cancel_event=ctx.cancel_event, allow_terminate=False)
    ctx.logger.info(f"Task Scheduler exit code: {res.returncode}")


def remove(ctx) -> None:
    cmd = ["schtasks", "/Delete", "/F", "/TN", TASK_NAME]
    if ctx.dry_run:
        ctx.logger.info(f"(dry-run) Would remove scheduled task: {TASK_NAME}")
        ctx.logger.info("▶ " + " ".join(cmd))
        return

    res = run_command(cmd, logger=ctx.logger,
                      cancel_event=ctx.cancel_event, allow_terminate=False)
    ctx.logger.info(f"Task Scheduler exit code: {res.returncode}")
