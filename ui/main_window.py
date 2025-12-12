from __future__ import annotations

import threading
import re
import customtkinter as ctk

from logger import Logger
from runner import Context, Task, run_tasks
from scheduler import install_daily, remove as remove_schedule

from tasks.temp_cleanup import clear_temp
from tasks.recycle_bin import empty_recycle_bin
from tasks.disk_cleanup import run_disk_cleanup
from tasks.storage_sense import run_storage_sense
from tasks.sfc import run_sfc
from tasks.dism import run_dism
from tasks.windows_update import run_windows_update

HHMM_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")


class MainWindow(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()

        self.title("System Maintenance")
        self.geometry("920x720")

        self.cancel_event = threading.Event()
        self.worker: threading.Thread | None = None

        self.logger = Logger()
        self.logger.attach_ui_sink(
            lambda msg: self.after(0, lambda: self._log_to_ui(msg))
        )

        # --------------------------------------------------
        # STATE
        # --------------------------------------------------

        self.dry_run = ctk.BooleanVar(value=True)

        self.do_temp = ctk.BooleanVar(value=True)
        self.do_recycle = ctk.BooleanVar(value=True)
        self.do_cleanmgr = ctk.BooleanVar(value=True)
        self.do_storagesense = ctk.BooleanVar(value=True)
        self.do_sfc = ctk.BooleanVar(value=False)
        self.do_dism = ctk.BooleanVar(value=False)
        self.do_updates = ctk.BooleanVar(value=True)

        self.schedule_time = ctk.StringVar(value="03:00")

        self._build_ui()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------

    def _build_ui(self):
        header = ctk.CTkFrame(self)
        header.pack(fill="x", padx=16, pady=(16, 10))

        ctk.CTkLabel(
            header,
            text="System Maintenance",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(anchor="w", padx=12, pady=(12, 2))

        ctk.CTkLabel(
            header,
            text=f"Logs: {self.logger.paths.text.name} + {self.logger.paths.jsonl.name}",
            text_color="gray",
        ).pack(anchor="w", padx=12, pady=(0, 12))

        content = ctk.CTkFrame(self)
        content.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        left = ctk.CTkFrame(content)
        left.pack(side="left", fill="y", padx=(12, 8), pady=12)

        right = ctk.CTkFrame(content)
        right.pack(side="right", fill="both",
                   expand=True, padx=(8, 12), pady=12)

        # ---------------- Tasks ----------------

        ctk.CTkLabel(
            left, text="Tasks", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 8))

        self.cb_temp = ctk.CTkCheckBox(
            left,
            text="Clear %TEMP% (safe, skips locked files)",
            variable=self.do_temp,
        )

        self.cb_recycle = ctk.CTkCheckBox(
            left,
            text="Recycle Bin (current user)",
            variable=self.do_recycle,
        )

        self.cb_cleanmgr = ctk.CTkCheckBox(
            left,
            text="Disk Cleanup (cleanmgr /sagerun:100)",
            variable=self.do_cleanmgr,
        )

        self.cb_storagesense = ctk.CTkCheckBox(
            left,
            text="Storage Sense (Windows-managed)",
            variable=self.do_storagesense,
        )

        self.cb_sfc = ctk.CTkCheckBox(
            left,
            text="SFC /scannow (slow)",
            variable=self.do_sfc,
        )

        self.cb_dism = ctk.CTkCheckBox(
            left,
            text="DISM RestoreHealth (slow)",
            variable=self.do_dism,
        )

        self.cb_updates = ctk.CTkCheckBox(
            left,
            text="Windows Update (PSWindowsUpdate)",
            variable=self.do_updates,
        )

        for cb in (
            self.cb_temp,
            self.cb_recycle,
            self.cb_cleanmgr,
            self.cb_storagesense,
            self.cb_sfc,
            self.cb_dism,
            self.cb_updates,
        ):
            cb.pack(anchor="w", padx=12, pady=6)

        self.cb_dry = ctk.CTkCheckBox(
            left,
            text="Dry-run (recommended)",
            variable=self.dry_run,
        )
        self.cb_dry.pack(anchor="w", padx=12, pady=(12, 6))

        # ---------------- Run ----------------

        ctk.CTkLabel(
            left, text="Run", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=12, pady=(16, 8))

        self.run_button = ctk.CTkButton(
            left, text="▶ Run Maintenance", command=self.run_async
        )
        self.run_button.pack(fill="x", padx=12, pady=(0, 8))

        self.cancel_button = ctk.CTkButton(
            left,
            text="⏹ Cancel (graceful)",
            command=self.cancel,
            state="disabled",
        )
        self.cancel_button.pack(fill="x", padx=12, pady=(0, 12))

        self.status = ctk.CTkLabel(left, text="Ready", text_color="gray")
        self.status.pack(anchor="w", padx=12, pady=(0, 8))

        ctk.CTkLabel(left, text="Overall progress", text_color="gray").pack(
            anchor="w", padx=12, pady=(0, 4)
        )

        self.progress = ctk.CTkProgressBar(left)
        self.progress.set(0.0)
        self.progress.pack(fill="x", padx=12, pady=(0, 12))

        # ---------------- Scheduler ----------------

        ctk.CTkLabel(
            left, text="Scheduler", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=12, pady=(8, 6))

        row = ctk.CTkFrame(left)
        row.pack(fill="x", padx=12, pady=(0, 8))

        ctk.CTkLabel(row, text="Daily at (HH:MM)", text_color="gray").pack(
            side="left", padx=(0, 8)
        )

        self.time_entry = ctk.CTkEntry(
            row, textvariable=self.schedule_time, width=90)
        self.time_entry.pack(side="left")

        self.btn_sched_install = ctk.CTkButton(
            left, text="🗓 Install daily scheduled task", command=self.install_schedule
        )
        self.btn_sched_remove = ctk.CTkButton(
            left, text="🧹 Remove scheduled task", command=self.remove_schedule
        )

        self.btn_sched_install.pack(fill="x", padx=12, pady=(0, 6))
        self.btn_sched_remove.pack(fill="x", padx=12, pady=(0, 12))

        # ---------------- Log ----------------

        ctk.CTkLabel(
            right, text="Log", font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 8))

        self.logbox = ctk.CTkTextbox(right, height=520)
        self.logbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.logbox.configure(state="disabled")

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------

    def _log_to_ui(self, msg: str):
        self.logbox.configure(state="normal")
        self.logbox.insert("end", msg + "\n")
        self.logbox.see("end")
        self.logbox.configure(state="disabled")

    def _set_controls_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        for w in (
            self.cb_temp,
            self.cb_recycle,
            self.cb_cleanmgr,
            self.cb_storagesense,
            self.cb_sfc,
            self.cb_dism,
            self.cb_updates,
            self.cb_dry,
            self.run_button,
            self.btn_sched_install,
            self.btn_sched_remove,
            self.time_entry,
        ):
            w.configure(state=state)
        self.cancel_button.configure(state="disabled" if enabled else "normal")

    def _progress_cb(self, value: float, status_text: str):
        self.after(0, lambda: self.progress.set(value))
        self.after(0, lambda: self.status.configure(text=status_text))

    # --------------------------------------------------
    # Task wiring
    # --------------------------------------------------

    def build_tasks(self) -> list[Task]:
        tasks: list[Task] = []

        if self.do_temp.get():
            tasks.append(
                Task("TEMP cleanup", clear_temp, allow_terminate=False))

        if self.do_recycle.get():
            tasks.append(
                Task("Recycle Bin", empty_recycle_bin, allow_terminate=False)
            )

        if self.do_cleanmgr.get():
            tasks.append(
                Task("Disk Cleanup", run_disk_cleanup, allow_terminate=True))

        if self.do_storagesense.get():
            tasks.append(
                Task("Storage Sense", run_storage_sense, allow_terminate=True)
            )

        if self.do_sfc.get():
            tasks.append(Task("SFC scan", run_sfc,
                         allow_terminate=False, slow=True))

        if self.do_dism.get():
            tasks.append(Task("DISM repair", run_dism,
                         allow_terminate=False, slow=True))

        if self.do_updates.get():
            tasks.append(
                Task(
                    "Windows Update",
                    run_windows_update,
                    allow_terminate=False,
                    slow=True,
                )
            )

        return tasks

    # --------------------------------------------------
    # Execution
    # --------------------------------------------------

    def run_async(self):
        if self.worker and self.worker.is_alive():
            return

        self.cancel_event.clear()
        self._set_controls_enabled(False)
        self.progress.set(0.0)
        self.status.configure(text="Starting…")

        ctx = Context(
            logger=self.logger,
            cancel_event=self.cancel_event,
            dry_run=self.dry_run.get(),
        )

        tasks = self.build_tasks()

        def worker():
            try:
                run_tasks(ctx, tasks, self._progress_cb)
            finally:
                self.after(0, lambda: self._set_controls_enabled(True))
                self.after(0, lambda: self.status.configure(text="Ready"))

        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def cancel(self):
        self.cancel_event.set()
        self.logger.warn(
            "⏹ Cancel requested — finishing current step safely, then stopping…"
        )
        self.cancel_button.configure(state="disabled")

    # --------------------------------------------------
    # Scheduler
    # --------------------------------------------------

    def install_schedule(self):
        hhmm = self.schedule_time.get().strip()
        if not HHMM_RE.match(hhmm):
            self.logger.error("Invalid time. Use HH:MM (e.g. 03:00).")
            return
        ctx = Context(
            logger=self.logger,
            cancel_event=self.cancel_event,
            dry_run=self.dry_run.get(),
        )
        install_daily(ctx, hhmm)

    def remove_schedule(self):
        ctx = Context(
            logger=self.logger,
            cancel_event=self.cancel_event,
            dry_run=self.dry_run.get(),
        )
        remove_schedule(ctx)
