# tasks/recycle_bin.py
import ctypes

SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004


def empty_recycle_bin(ctx):
    ctx.logger.info("\n🗑 RECYCLE BIN")

    if ctx.dry_run:
        ctx.logger.info("(dry-run) Would empty Recycle Bin")
        return

    try:
        res = ctypes.windll.shell32.SHEmptyRecycleBinW(
            None,
            None,
            SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        )

        if res == 0:
            ctx.logger.info("✔ Recycle Bin emptied")
        else:
            ctx.logger.warn(f"Recycle Bin returned code {res}")

    except Exception as e:
        ctx.logger.error(f"Recycle Bin failed: {e}")
