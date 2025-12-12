from __future__ import annotations
from config import CLEANMGR_PROFILE_ID
from process import run_command


def run_disk_cleanup(ctx) -> None:
    ctx.logger.info("\n🗑 DISK CLEANUP (cleanmgr)")
    cmd = ["cleanmgr", f"/sagerun:{CLEANMGR_PROFILE_ID}"]

    if ctx.dry_run:
        ctx.logger.info("(dry-run) Would run Disk Cleanup")
        ctx.logger.info("▶ " + " ".join(cmd))
        return

    res = run_command(cmd, logger=ctx.logger,
                      cancel_event=ctx.cancel_event, allow_terminate=True)
    ctx.logger.info(f"Disk Cleanup exit code: {res.returncode}")
