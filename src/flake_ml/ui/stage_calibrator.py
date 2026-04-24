from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from ..config import LabConfig, load_lab_config
from ..config_store import update_toml_section
from ..motion.grbl_bridge import GrblStatus, PowerShellGrblBridge


@dataclass(slots=True)
class PendingBounds:
    min_x_um: float | None = None
    min_y_um: float | None = None
    max_x_um: float | None = None
    max_y_um: float | None = None


class StageCalibrationUI:
    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self.config: LabConfig = load_lab_config(self.config_path)
        self.bridge = PowerShellGrblBridge(
            port=self.config.motion.port,
            baud=self.config.motion.baud,
            startup_delay_ms=self.config.motion.startup_delay_ms,
        )
        self.root = tk.Tk()
        self.root.title("FlakeID Stage Calibration")
        self.root.geometry("920x760")

        self.pending_bounds = PendingBounds(
            min_x_um=self.config.motion.min_x_um,
            min_y_um=self.config.motion.min_y_um,
            max_x_um=self.config.motion.max_x_um,
            max_y_um=self.config.motion.max_y_um,
        )
        self.busy = False
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self.status_text = tk.StringVar(value="Disconnected")
        self.machine_pos_text = tk.StringVar(value="MPos: --, --")
        self.work_pos_text = tk.StringVar(value="WPos: --, --")
        self.raw_text = tk.StringVar(value="")
        self.step_um_var = tk.StringVar(value="500")
        self.feed_var = tk.StringVar(value=f"{self.config.motion.jog_feed_mm_min:.1f}")
        self.x_rate_var = tk.StringVar(value=self._format_optional(self.config.motion.x_max_rate_mm_min, "200.0"))
        self.y_rate_var = tk.StringVar(value=self._format_optional(self.config.motion.y_max_rate_mm_min, "200.0"))
        self.x_accel_var = tk.StringVar(value=self._format_optional(self.config.motion.x_accel_mm_s2, "2.0"))
        self.y_accel_var = tk.StringVar(value=self._format_optional(self.config.motion.y_accel_mm_s2, "2.0"))
        self.margin_um_var = tk.StringVar(value=f"{self.config.motion.safety_margin_um:.0f}")
        self.bounds_text = tk.StringVar()
        self._refresh_bounds_text()

        self._build_layout()
        self.root.after(200, self._poll_queue)
        self.root.after(300, self.refresh_status)

    @staticmethod
    def _format_optional(value: float | None, fallback: str) -> str:
        return fallback if value is None else f"{value:.3f}".rstrip("0").rstrip(".")

    def _build_layout(self) -> None:
        outer = ttk.Frame(self.root, padding=12)
        outer.pack(fill="both", expand=True)

        top = ttk.LabelFrame(outer, text="Connection")
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text=f"Config: {self.config_path}").grid(row=0, column=0, sticky="w", padx=8, pady=4, columnspan=3)
        ttk.Label(top, text=f"Port: {self.config.motion.port}").grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Label(top, text=f"Baud: {self.config.motion.baud}").grid(row=1, column=1, sticky="w", padx=8, pady=4)
        ttk.Button(top, text="Refresh Status", command=self.refresh_status).grid(row=1, column=2, sticky="e", padx=8, pady=4)
        ttk.Label(top, textvariable=self.status_text).grid(row=2, column=0, sticky="w", padx=8, pady=4)
        ttk.Label(top, textvariable=self.machine_pos_text).grid(row=2, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(top, textvariable=self.work_pos_text).grid(row=2, column=2, sticky="w", padx=8, pady=4)
        ttk.Label(top, textvariable=self.raw_text, foreground="#555555").grid(row=3, column=0, sticky="w", padx=8, pady=(0, 8), columnspan=3)

        motion = ttk.LabelFrame(outer, text="Motion")
        motion.pack(fill="x", pady=(0, 10))
        ttk.Label(motion, text="Jog step (um)").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(motion, textvariable=self.step_um_var, width=10).grid(row=0, column=1, sticky="w", padx=8, pady=6)
        ttk.Label(motion, text="Jog feed (mm/min)").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        ttk.Entry(motion, textvariable=self.feed_var, width=10).grid(row=0, column=3, sticky="w", padx=8, pady=6)

        for column, preset in enumerate(("50", "100", "500", "1000", "5000")):
            ttk.Button(motion, text=f"{preset} um", command=lambda value=preset: self.step_um_var.set(value)).grid(
                row=1, column=column, padx=6, pady=(0, 8), sticky="ew"
            )

        jogs = ttk.Frame(motion)
        jogs.grid(row=2, column=0, columnspan=5, pady=8)
        ttk.Button(jogs, text="+Y", command=lambda: self.jog(0.0, +1.0), width=12).grid(row=0, column=1, padx=8, pady=4)
        ttk.Button(jogs, text="-X", command=lambda: self.jog(-1.0, 0.0), width=12).grid(row=1, column=0, padx=8, pady=4)
        ttk.Button(jogs, text="+X", command=lambda: self.jog(+1.0, 0.0), width=12).grid(row=1, column=2, padx=8, pady=4)
        ttk.Button(jogs, text="-Y", command=lambda: self.jog(0.0, -1.0), width=12).grid(row=2, column=1, padx=8, pady=4)

        control = ttk.Frame(motion)
        control.grid(row=3, column=0, columnspan=5, pady=(8, 4), sticky="w")
        ttk.Button(control, text="Unlock", command=self.unlock).pack(side="left", padx=(0, 8))
        ttk.Button(control, text="Set Work Zero", command=self.set_work_zero).pack(side="left", padx=(0, 8))
        ttk.Button(control, text="Feed Hold", command=self.feed_hold).pack(side="left", padx=(0, 8))
        ttk.Button(control, text="Resume", command=self.resume).pack(side="left", padx=(0, 8))
        ttk.Button(control, text="Soft Reset", command=self.soft_reset).pack(side="left", padx=(0, 8))

        tuning = ttk.LabelFrame(outer, text="Speed And Acceleration")
        tuning.pack(fill="x", pady=(0, 10))
        ttk.Label(tuning, text="X max rate (mm/min)").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(tuning, textvariable=self.x_rate_var, width=12).grid(row=0, column=1, sticky="w", padx=8, pady=6)
        ttk.Label(tuning, text="Y max rate (mm/min)").grid(row=0, column=2, sticky="w", padx=8, pady=6)
        ttk.Entry(tuning, textvariable=self.y_rate_var, width=12).grid(row=0, column=3, sticky="w", padx=8, pady=6)
        ttk.Label(tuning, text="X accel (mm/s^2)").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(tuning, textvariable=self.x_accel_var, width=12).grid(row=1, column=1, sticky="w", padx=8, pady=6)
        ttk.Label(tuning, text="Y accel (mm/s^2)").grid(row=1, column=2, sticky="w", padx=8, pady=6)
        ttk.Entry(tuning, textvariable=self.y_accel_var, width=12).grid(row=1, column=3, sticky="w", padx=8, pady=6)
        ttk.Button(tuning, text="Read GRBL Settings", command=self.read_settings).grid(row=2, column=0, padx=8, pady=8, sticky="w")
        ttk.Button(tuning, text="Apply Rates/Accel", command=self.apply_motion_settings).grid(row=2, column=1, padx=8, pady=8, sticky="w")

        bounds = ttk.LabelFrame(outer, text="Safe Bounds")
        bounds.pack(fill="x", pady=(0, 10))
        ttk.Label(bounds, textvariable=self.bounds_text).grid(row=0, column=0, columnspan=4, sticky="w", padx=8, pady=8)
        ttk.Button(bounds, text="Mark Min X", command=lambda: self.capture_bound("min_x_um")).grid(row=1, column=0, padx=8, pady=6, sticky="ew")
        ttk.Button(bounds, text="Mark Max X", command=lambda: self.capture_bound("max_x_um")).grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        ttk.Button(bounds, text="Mark Min Y", command=lambda: self.capture_bound("min_y_um")).grid(row=1, column=2, padx=8, pady=6, sticky="ew")
        ttk.Button(bounds, text="Mark Max Y", command=lambda: self.capture_bound("max_y_um")).grid(row=1, column=3, padx=8, pady=6, sticky="ew")
        ttk.Label(bounds, text="Safety margin (um)").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        ttk.Entry(bounds, textvariable=self.margin_um_var, width=12).grid(row=2, column=1, sticky="w", padx=8, pady=6)
        ttk.Button(bounds, text="Save Bounds To Config", command=self.save_bounds_to_config).grid(row=2, column=3, padx=8, pady=6, sticky="e")

        bottom = ttk.LabelFrame(outer, text="Notes")
        bottom.pack(fill="both", expand=True)
        notes = (
            "Suggested starting values while belts are skipping:\n"
            "- Jog feed: 20-40 mm/min\n"
            "- X/Y max rate: 40-80 mm/min\n"
            "- X/Y acceleration: 1-3 mm/s^2\n\n"
            "Use manual motion only before re-zeroing. Mark bounds at backed-off safe points, not at hard stops."
        )
        ttk.Label(bottom, text=notes, justify="left").pack(anchor="w", padx=8, pady=8)

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        self.root.config(cursor="watch" if busy else "")

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.result_queue.get_nowait()
                if kind == "status":
                    self._apply_status(payload)  # type: ignore[arg-type]
                elif kind == "settings":
                    self._apply_settings(payload)  # type: ignore[arg-type]
                elif kind == "info":
                    self.raw_text.set(str(payload))
                elif kind == "error":
                    messagebox.showerror("FlakeID Stage Calibration", str(payload))
                elif kind == "saved":
                    messagebox.showinfo("FlakeID Stage Calibration", str(payload))
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self._poll_queue)

    def _run_async(self, worker, *, on_done=None) -> None:
        if self.busy:
            return
        self._set_busy(True)

        def _task() -> None:
            try:
                result = worker()
                if on_done is not None:
                    on_done(result)
            except Exception as exc:  # pragma: no cover - UI path
                self.result_queue.put(("error", exc))
            finally:
                self.root.after(0, lambda: self._set_busy(False))

        threading.Thread(target=_task, daemon=True).start()

    def _apply_status(self, status: GrblStatus) -> None:
        self.status_text.set(f"State: {status.state}")
        self.machine_pos_text.set(f"MPos: {status.machine_x_mm:.3f}, {status.machine_y_mm:.3f} mm")
        self.work_pos_text.set(f"WPos: {status.work_x_mm:.3f}, {status.work_y_mm:.3f} mm")
        self.raw_text.set(status.raw)

    def _apply_settings(self, settings: dict[str, float]) -> None:
        if not settings:
            self.raw_text.set(
                "Controller did not echo GRBL settings in a parseable form. "
                "Use the values shown here as the intended lab-side settings and verify by motion behavior."
            )
            return
        if "110" in settings:
            self.x_rate_var.set(f"{settings['110']:.3f}".rstrip("0").rstrip("."))
        if "111" in settings:
            self.y_rate_var.set(f"{settings['111']:.3f}".rstrip("0").rstrip("."))
        if "120" in settings:
            self.x_accel_var.set(f"{settings['120']:.3f}".rstrip("0").rstrip("."))
        if "121" in settings:
            self.y_accel_var.set(f"{settings['121']:.3f}".rstrip("0").rstrip("."))
        self.raw_text.set("Pulled current GRBL settings from controller.")

    def _refresh_bounds_text(self) -> None:
        self.bounds_text.set(
            "Current pending bounds: "
            f"min_x={self._format_bound(self.pending_bounds.min_x_um)}, "
            f"max_x={self._format_bound(self.pending_bounds.max_x_um)}, "
            f"min_y={self._format_bound(self.pending_bounds.min_y_um)}, "
            f"max_y={self._format_bound(self.pending_bounds.max_y_um)}"
        )

    @staticmethod
    def _format_bound(value: float | None) -> str:
        return "--" if value is None else f"{value:.0f} um"

    def refresh_status(self) -> None:
        self._run_async(self.bridge.status, on_done=lambda result: self.result_queue.put(("status", result)))

    def unlock(self) -> None:
        self._run_async(self.bridge.unlock, on_done=lambda result: self.result_queue.put(("info", f"Unlock response: {result or 'ok'}")))

    def set_work_zero(self) -> None:
        def worker():
            self.bridge.set_work_origin()
            return self.bridge.status()

        self._run_async(worker, on_done=lambda result: self.result_queue.put(("status", result)))

    def feed_hold(self) -> None:
        self._run_async(self.bridge.feed_hold, on_done=lambda result: self.result_queue.put(("info", "Feed hold sent.")))

    def resume(self) -> None:
        self._run_async(self.bridge.resume, on_done=lambda result: self.result_queue.put(("info", "Resume sent.")))

    def soft_reset(self) -> None:
        self._run_async(self.bridge.soft_reset, on_done=lambda result: self.result_queue.put(("info", "Soft reset sent.")))

    def read_settings(self) -> None:
        self._run_async(self.bridge.read_settings, on_done=lambda result: self.result_queue.put(("settings", result)))

    def apply_motion_settings(self) -> None:
        x_rate = float(self.x_rate_var.get())
        y_rate = float(self.y_rate_var.get())
        x_accel = float(self.x_accel_var.get())
        y_accel = float(self.y_accel_var.get())

        def worker():
            self.bridge.set_max_rates(x_rate, y_rate)
            self.bridge.set_acceleration(x_accel, y_accel)
            return self.bridge.read_settings()

        self._run_async(worker, on_done=lambda result: self.result_queue.put(("settings", result)))

    def jog(self, x_direction: float, y_direction: float) -> None:
        step_um = float(self.step_um_var.get())
        feed_mm_min = float(self.feed_var.get())

        def worker():
            self.bridge.jog_relative(dx_um=x_direction * step_um, dy_um=y_direction * step_um, feed_mm_min=feed_mm_min)
            return self.bridge.status()

        self._run_async(worker, on_done=lambda result: self.result_queue.put(("status", result)))

    def capture_bound(self, field_name: str) -> None:
        def worker():
            return self.bridge.status()

        def on_done(result: GrblStatus) -> None:
            if field_name in ("min_x_um", "max_x_um"):
                value_um = result.machine_x_mm * 1000.0
            else:
                value_um = result.machine_y_mm * 1000.0
            setattr(self.pending_bounds, field_name, value_um)
            self._refresh_bounds_text()
            self.result_queue.put(("status", result))

        self._run_async(worker, on_done=on_done)

    def save_bounds_to_config(self) -> None:
        updates = {
            "min_x_um": self.pending_bounds.min_x_um if self.pending_bounds.min_x_um is not None else 0.0,
            "min_y_um": self.pending_bounds.min_y_um if self.pending_bounds.min_y_um is not None else 0.0,
            "max_x_um": self.pending_bounds.max_x_um if self.pending_bounds.max_x_um is not None else self.config.motion.max_x_um,
            "max_y_um": self.pending_bounds.max_y_um if self.pending_bounds.max_y_um is not None else self.config.motion.max_y_um,
            "safety_margin_um": float(self.margin_um_var.get()),
            "jog_feed_mm_min": float(self.feed_var.get()),
            "travel_rate_um_s": float(self.feed_var.get()) * (1000.0 / 60.0),
            "x_max_rate_mm_min": float(self.x_rate_var.get()),
            "y_max_rate_mm_min": float(self.y_rate_var.get()),
            "x_accel_mm_s2": float(self.x_accel_var.get()),
            "y_accel_mm_s2": float(self.y_accel_var.get()),
        }
        if updates["max_x_um"] is None or updates["max_y_um"] is None:
            messagebox.showwarning("FlakeID Stage Calibration", "Capture both max bounds before saving.")
            return
        update_toml_section(self.config_path, "motion", updates)
        self.result_queue.put(("saved", f"Saved motion bounds and tuning values to {self.config_path}"))

    def run(self) -> None:
        self.root.mainloop()


def launch_stage_calibration_ui(config_path: str | Path) -> None:
    ui = StageCalibrationUI(config_path)
    ui.run()
