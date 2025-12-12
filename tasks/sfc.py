from __future__ import annotations
from process import run_command


def run_sfc(ctx) -> None:
    ctx.logger.info("\n🧠 SFC /scannow")
    ctx.logger.info("Note: Cancel will stop AFTER SFC completes (safe).")

    cmd = ["sfc", "/scannow"]

    if ctx.dry_run:
        ctx.logger.info("(dry-run) Would run SFC")
        ctx.logger.info("▶ " + " ".join(cmd))
        return

    # Do NOT terminate SFC mid-run
    res = run_command(cmd, logger=ctx.logger,
                      cancel_event=ctx.cancel_event, allow_terminate=False)
    ctx.logger.info(f"SFC exit code: {res.returncode}")
