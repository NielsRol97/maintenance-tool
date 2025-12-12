from __future__ import annotations
from process import run_command


def run_dism(ctx) -> None:
    ctx.logger.info("\n🧠 DISM RestoreHealth")
    ctx.logger.info("Note: Cancel will stop AFTER DISM completes (safe).")

    cmd = ["dism", "/Online", "/Cleanup-Image", "/RestoreHealth"]

    if ctx.dry_run:
        ctx.logger.info("(dry-run) Would run DISM")
        ctx.logger.info("▶ " + " ".join(cmd))
        return

    # Do NOT terminate DISM mid-run
    res = run_command(cmd, logger=ctx.logger,
                      cancel_event=ctx.cancel_event, allow_terminate=False)
    ctx.logger.info(f"DISM exit code: {res.returncode}")
