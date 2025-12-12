from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List


@dataclass
class Context:
    logger: any
    cancel_event: any
    dry_run: bool


TaskFn = Callable[[Context], None]


@dataclass
class Task:
    name: str
    fn: TaskFn
    allow_terminate: bool  # for subprocess tasks (policy)
    slow: bool = False


def run_tasks(ctx: Context, tasks: List[Task], on_progress: Callable[[float, str], None]) -> None:
    total = len(tasks)
    if total == 0:
        ctx.logger.warn("No tasks selected.")
        return

    ctx.logger.info("\n=== MAINTENANCE START ===")
    ctx.logger.info(f"Dry-run: {ctx.dry_run}")

    for i, task in enumerate(tasks, start=1):
        if ctx.cancel_event.is_set():
            ctx.logger.warn("⏹ Cancel requested — stopping before next task.")
            break

        on_progress((i - 1) / total, f"Running: {task.name} ({i}/{total})")
        ctx.logger.info(f"\n--- {task.name} ({i}/{total}) ---")

        try:
            task.fn(ctx)
        except Exception as e:
            ctx.logger.error(f"Task crashed: {task.name}", error=str(e))

    on_progress(1.0, "Ready")
    if ctx.cancel_event.is_set():
        ctx.logger.warn("\n=== MAINTENANCE CANCELLED ===\n")
    else:
        ctx.logger.info("\n=== MAINTENANCE COMPLETE ===\n")
