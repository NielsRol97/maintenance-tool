import os
import shutil
import tempfile


def clear_temp(ctx):
    temp_path = tempfile.gettempdir()
    ctx.logger.info("\n🧹 TEMP CLEANUP")
    ctx.logger.info(f"Target: {temp_path}")

    deleted = skipped = errors = 0

    for entry in os.scandir(temp_path):
        if ctx.cancel_event.is_set():
            ctx.logger.warn("⏹ Cancel requested — stopping TEMP cleanup.")
            break

        try:
            if entry.is_file(follow_symlinks=False):
                if ctx.dry_run:
                    deleted += 1
                else:
                    os.remove(entry.path)
                    deleted += 1
            elif entry.is_dir(follow_symlinks=False):
                if entry.is_symlink():
                    skipped += 1
                    ctx.logger.warn(f"⚠ Skipped symlink dir: {entry.path}")
                    continue

                if ctx.dry_run:
                    deleted += 1
                else:
                    shutil.rmtree(entry.path)
                    deleted += 1

        except PermissionError:
            skipped += 1
            ctx.logger.warn(f"⚠ Skipped (in use): {entry.path}")
        except Exception as e:
            errors += 1
            ctx.logger.error(f"❌ Error deleting {entry.path}", error=str(e))

    ctx.logger.info(
        f"Summary → Deleted: {deleted}, Skipped: {skipped}, Errors: {errors}"
    )
