from __future__ import annotations
from config import POWERSHELL_51_X64
from process import run_command


def run_windows_update(ctx) -> None:
    ctx.logger.info("\n🔄 WINDOWS UPDATE (PSWindowsUpdate)")
    ctx.logger.info(
        "Note: Cancel will stop AFTER the update command completes (safe).")

    check_cmd = [
        POWERSHELL_51_X64, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
        "Get-Module -ListAvailable PSWindowsUpdate | Select-Object -First 1"
    ]

    if ctx.dry_run:
        ctx.logger.info(
            "(dry-run) Would check PSWindowsUpdate and install updates")
        ctx.logger.info("▶ " + " ".join(check_cmd))
        return

    check = run_command(check_cmd, logger=ctx.logger,
                        cancel_event=ctx.cancel_event, allow_terminate=True)
    if check.returncode != 0 or not check.stdout.strip():
        ctx.logger.error(
            "PSWindowsUpdate module not found in 64-bit PowerShell.")
        ctx.logger.error(
            "Fix: Install it in *64-bit* PowerShell (Run as Admin):")
        ctx.logger.info(
            "Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force")
        ctx.logger.info("Install-Module PSWindowsUpdate -Force")
        return

    update_cmd = [
        POWERSHELL_51_X64, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
        "Import-Module PSWindowsUpdate -Force; Install-WindowsUpdate -AcceptAll -IgnoreReboot"
    ]

    # Do NOT terminate updates mid-flight
    res = run_command(update_cmd, logger=ctx.logger,
                      cancel_event=ctx.cancel_event, allow_terminate=False)
    ctx.logger.info(f"Windows Update exit code: {res.returncode}")
