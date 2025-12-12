from __future__ import annotations
from config import POWERSHELL_51_X64
from process import run_command


def run_storage_sense(ctx):
    ctx.logger.info("\n🧹 STORAGE SENSE")

    if ctx.dry_run:
        ctx.logger.info("(dry-run) Would trigger Storage Sense")
        return

    cmd = [
        r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-Command", "Start-StorageSense"
    ]

    res = ctx.run(cmd, allow_fail=True)

    if res.returncode == 0:
        ctx.logger.info("✔ Storage Sense triggered")
    else:
        ctx.logger.warn(
            "Storage Sense not available on this system (safe to ignore)"
        )
