from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

from PIL import Image, ImageTk

from ..annotation.manual import (
    ManualImageAnnotation,
    ManualObjectAnnotation,
    VALID_TILE_LABELS,
    discover_images,
    load_manual_annotations,
    save_manual_annotations,
)
from ..utils import timestamp_utc


OBJECT_LABELS = ("graphene", "hbn", "other_flake", "artifact")


class ManualReviewApp:
    def __init__(self, root: tk.Tk, image_dir: str | Path, output_path: str | Path) -> None:
        self.root = root
        self.image_dir = Path(image_dir).resolve()
        self.output_path = Path(output_path).resolve()
        self.images = discover_images(self.image_dir)
        if not self.images:
            raise FileNotFoundError(f"No images were found in {self.image_dir}")

        self.annotations = load_manual_annotations(self.output_path)
        self.index = 0
        self.zoom = 0.18
        self.min_zoom = 0.05
        self.max_zoom = 6.0
        self.current_image_path: Path | None = None
        self.current_pil: Image.Image | None = None
        self.current_photo: ImageTk.PhotoImage | None = None
        self.selected_box_index: int | None = None
        self.drag_start_canvas: tuple[float, float] | None = None
        self.drag_preview_id: int | None = None

        self.tile_label_var = tk.StringVar(value="unreviewed")
        self.object_label_var = tk.StringVar(value=OBJECT_LABELS[0])
        self.status_var = tk.StringVar(value="")
        self.path_var = tk.StringVar(value="")

        self._build_ui()
        self._bind_keys()
        self._load_current_image(reset_view=True)

    def _build_ui(self) -> None:
        self.root.title("FlakeID Manual Review")
        self.root.geometry("1520x980")

        outer = ttk.Frame(self.root)
        outer.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(outer)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        right = ttk.Frame(outer, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        toolbar = ttk.Frame(left)
        toolbar.pack(fill=tk.X, padx=8, pady=8)
        ttk.Button(toolbar, text="Prev", command=self.prev_image).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Next", command=self.next_image).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Zoom -", command=lambda: self._change_zoom(0.8)).pack(side=tk.LEFT, padx=12)
        ttk.Button(toolbar, text="Zoom +", command=lambda: self._change_zoom(1.25)).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Fit", command=self._fit_to_view).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Delete Box", command=self.delete_selected_box).pack(side=tk.LEFT, padx=12)
        ttk.Button(toolbar, text="Clear Boxes", command=self.clear_boxes).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Save", command=self.save_all).pack(side=tk.LEFT, padx=12)

        self.path_label = ttk.Label(left, textvariable=self.path_var)
        self.path_label.pack(fill=tk.X, padx=8)

        canvas_frame = ttk.Frame(left)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.canvas = tk.Canvas(canvas_frame, background="black", highlightthickness=0)
        x_scroll = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        y_scroll = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=x_scroll.set, yscrollcommand=y_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        self.canvas.bind("<ButtonPress-1>", self._on_left_press)
        self.canvas.bind("<B1-Motion>", self._on_left_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_left_release)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)

        ttk.Label(right, text="Tile Label").pack(anchor="w")
        for label in VALID_TILE_LABELS:
            ttk.Radiobutton(
                right,
                text=label,
                variable=self.tile_label_var,
                value=label,
                command=self._update_status,
            ).pack(anchor="w")

        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(right, text="New Box Label").pack(anchor="w")
        label_menu = ttk.OptionMenu(right, self.object_label_var, OBJECT_LABELS[0], *OBJECT_LABELS)
        label_menu.pack(fill=tk.X, pady=4)

        ttk.Label(
            right,
            text="Draw boxes with left-drag.\nClick an existing box to select it.\nUse Delete to remove the selected box.",
            justify=tk.LEFT,
        ).pack(anchor="w", pady=10)

        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        ttk.Label(right, text="Notes").pack(anchor="w")
        self.notes_box = tk.Text(right, height=8, width=34)
        self.notes_box.pack(fill=tk.X)

        ttk.Separator(right, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(right, text=f"Image root:\n{self.image_dir}", justify=tk.LEFT).pack(anchor="w")
        ttk.Label(right, text=f"Review file:\n{self.output_path}", justify=tk.LEFT).pack(anchor="w", pady=(8, 0))
        ttk.Label(right, textvariable=self.status_var, justify=tk.LEFT).pack(anchor="w", pady=(12, 0))

    def _bind_keys(self) -> None:
        self.root.bind("<Left>", lambda _event: self.prev_image())
        self.root.bind("<Right>", lambda _event: self.next_image())
        self.root.bind("<Control-s>", lambda _event: self.save_all())
        self.root.bind("<Delete>", lambda _event: self.delete_selected_box())
        self.root.bind("1", lambda _event: self._set_tile_label("no_flake"))
        self.root.bind("2", lambda _event: self._set_tile_label("graphene"))
        self.root.bind("3", lambda _event: self._set_tile_label("hbn"))
        self.root.bind("4", lambda _event: self._set_tile_label("mixed"))
        self.root.bind("5", lambda _event: self._set_tile_label("artifact"))
        self.root.bind("6", lambda _event: self._set_tile_label("unsure"))

    def _annotation_for(self, image_path: Path) -> ManualImageAnnotation:
        key = str(image_path)
        if key not in self.annotations:
            self.annotations[key] = ManualImageAnnotation(image_path=key)
        return self.annotations[key]

    def _save_current_annotation(self) -> None:
        if self.current_image_path is None:
            return
        annotation = self._annotation_for(self.current_image_path)
        annotation.tile_label = self.tile_label_var.get()
        annotation.notes = self.notes_box.get("1.0", tk.END).strip()
        annotation.updated_utc = timestamp_utc()

    def save_all(self) -> None:
        self._save_current_annotation()
        save_manual_annotations(self.output_path, self.annotations, self.image_dir)
        self._update_status(extra="Saved.")

    def _load_current_image(self, reset_view: bool = False) -> None:
        image_path = self.images[self.index]
        self.current_image_path = image_path
        self.current_pil = Image.open(image_path).convert("RGB")
        if reset_view:
            self._fit_to_view()
        else:
            self._render_canvas()

        annotation = self._annotation_for(image_path)
        self.tile_label_var.set(annotation.tile_label if annotation.tile_label in VALID_TILE_LABELS else "unreviewed")
        self.notes_box.delete("1.0", tk.END)
        self.notes_box.insert("1.0", annotation.notes)
        self.selected_box_index = None
        self.path_var.set(str(image_path))
        self._update_status()

    def _fit_to_view(self) -> None:
        if self.current_pil is None:
            return
        self.root.update_idletasks()
        canvas_width = max(self.canvas.winfo_width(), 400)
        canvas_height = max(self.canvas.winfo_height(), 300)
        width_scale = canvas_width / self.current_pil.width
        height_scale = canvas_height / self.current_pil.height
        self.zoom = max(self.min_zoom, min(self.max_zoom, min(width_scale, height_scale)))
        self._render_canvas()

    def _change_zoom(self, multiplier: float) -> None:
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * multiplier))
        self._render_canvas()

    def _render_canvas(self) -> None:
        if self.current_pil is None or self.current_image_path is None:
            return
        width = max(1, int(round(self.current_pil.width * self.zoom)))
        height = max(1, int(round(self.current_pil.height * self.zoom)))
        resized = self.current_pil.resize((width, height), Image.Resampling.BILINEAR)
        self.current_photo = ImageTk.PhotoImage(resized)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_photo, tags=("image",))
        self.canvas.configure(scrollregion=(0, 0, width, height))
        self._draw_boxes()

    def _draw_boxes(self) -> None:
        if self.current_image_path is None:
            return
        annotation = self._annotation_for(self.current_image_path)
        for index, item in enumerate(annotation.objects):
            x, y, w, h = item.bbox_xywh
            sx1 = x * self.zoom
            sy1 = y * self.zoom
            sx2 = (x + w) * self.zoom
            sy2 = (y + h) * self.zoom
            color = "#00ff88" if index != self.selected_box_index else "#ff0066"
            self.canvas.create_rectangle(sx1, sy1, sx2, sy2, outline=color, width=2)
            self.canvas.create_text(
                sx1 + 4,
                max(12, sy1 + 10),
                text=item.label,
                fill=color,
                anchor=tk.W,
            )

    def _on_mousewheel(self, event: tk.Event) -> None:
        if event.delta > 0:
            self._change_zoom(1.1)
        elif event.delta < 0:
            self._change_zoom(0.9)

    def _canvas_to_image(self, canvas_x: float, canvas_y: float) -> tuple[int, int]:
        x = int(max(0, round(self.canvas.canvasx(canvas_x) / self.zoom)))
        y = int(max(0, round(self.canvas.canvasy(canvas_y) / self.zoom)))
        if self.current_pil is not None:
            x = min(self.current_pil.width - 1, x)
            y = min(self.current_pil.height - 1, y)
        return x, y

    def _find_box_at(self, image_x: int, image_y: int) -> int | None:
        if self.current_image_path is None:
            return None
        annotation = self._annotation_for(self.current_image_path)
        for index in range(len(annotation.objects) - 1, -1, -1):
            x, y, w, h = annotation.objects[index].bbox_xywh
            if x <= image_x <= x + w and y <= image_y <= y + h:
                return index
        return None

    def _on_left_press(self, event: tk.Event) -> None:
        image_x, image_y = self._canvas_to_image(event.x, event.y)
        hit = self._find_box_at(image_x, image_y)
        if hit is not None:
            self.selected_box_index = hit
            self._render_canvas()
            self._update_status()
            return
        self.selected_box_index = None
        self.drag_start_canvas = (self.canvas.canvasx(event.x), self.canvas.canvasy(event.y))
        if self.drag_preview_id is not None:
            self.canvas.delete(self.drag_preview_id)
        self.drag_preview_id = self.canvas.create_rectangle(
            self.drag_start_canvas[0],
            self.drag_start_canvas[1],
            self.drag_start_canvas[0],
            self.drag_start_canvas[1],
            outline="#ffff00",
            width=2,
            dash=(3, 3),
        )

    def _on_left_drag(self, event: tk.Event) -> None:
        if self.drag_start_canvas is None or self.drag_preview_id is None:
            return
        current_x = self.canvas.canvasx(event.x)
        current_y = self.canvas.canvasy(event.y)
        self.canvas.coords(
            self.drag_preview_id,
            self.drag_start_canvas[0],
            self.drag_start_canvas[1],
            current_x,
            current_y,
        )

    def _on_left_release(self, event: tk.Event) -> None:
        if self.drag_start_canvas is None:
            return
        start_x, start_y = self.drag_start_canvas
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        self.drag_start_canvas = None
        if self.drag_preview_id is not None:
            self.canvas.delete(self.drag_preview_id)
            self.drag_preview_id = None

        ix1, iy1 = self._canvas_to_image(start_x, start_y)
        ix2, iy2 = self._canvas_to_image(end_x, end_y)
        x1, x2 = sorted((ix1, ix2))
        y1, y2 = sorted((iy1, iy2))
        if x2 - x1 < 8 or y2 - y1 < 8:
            self._render_canvas()
            return
        if self.current_image_path is None:
            return
        annotation = self._annotation_for(self.current_image_path)
        annotation.objects.append(
            ManualObjectAnnotation(
                label=self.object_label_var.get(),
                bbox_xywh=(x1, y1, x2 - x1, y2 - y1),
            )
        )
        annotation.updated_utc = timestamp_utc()
        self.selected_box_index = len(annotation.objects) - 1
        self._render_canvas()
        self._update_status(extra="Added box.")

    def delete_selected_box(self) -> None:
        if self.current_image_path is None or self.selected_box_index is None:
            return
        annotation = self._annotation_for(self.current_image_path)
        if 0 <= self.selected_box_index < len(annotation.objects):
            annotation.objects.pop(self.selected_box_index)
            annotation.updated_utc = timestamp_utc()
        self.selected_box_index = None
        self._render_canvas()
        self._update_status(extra="Deleted box.")

    def clear_boxes(self) -> None:
        if self.current_image_path is None:
            return
        annotation = self._annotation_for(self.current_image_path)
        annotation.objects.clear()
        annotation.updated_utc = timestamp_utc()
        self.selected_box_index = None
        self._render_canvas()
        self._update_status(extra="Cleared boxes.")

    def _set_tile_label(self, label: str) -> None:
        self.tile_label_var.set(label)
        self._update_status()

    def prev_image(self) -> None:
        if self.index <= 0:
            return
        self._save_current_annotation()
        self.index -= 1
        self._load_current_image(reset_view=False)

    def next_image(self) -> None:
        if self.index >= len(self.images) - 1:
            self._save_current_annotation()
            self.save_all()
            return
        self._save_current_annotation()
        self.index += 1
        self._load_current_image(reset_view=False)

    def _update_status(self, extra: str = "") -> None:
        reviewed = 0
        boxed = 0
        for image_path, annotation in self.annotations.items():
            if annotation.tile_label != "unreviewed" or annotation.objects:
                reviewed += 1
            boxed += len(annotation.objects)
        current = self.index + 1
        total = len(self.images)
        box_count = 0
        if self.current_image_path is not None:
            box_count = len(self._annotation_for(self.current_image_path).objects)
        text = (
            f"Image {current}/{total}\n"
            f"Reviewed tiles: {reviewed}/{total}\n"
            f"Total boxes: {boxed}\n"
            f"Current boxes: {box_count}\n"
            f"Zoom: {self.zoom:.2f}x"
        )
        if extra:
            text += f"\n{extra}"
        self.status_var.set(text)


def launch_manual_review(image_dir: str | Path, output_path: str | Path) -> None:
    root = tk.Tk()
    app = ManualReviewApp(root, image_dir=image_dir, output_path=output_path)

    def on_close() -> None:
        try:
            app.save_all()
        except Exception as exception:  # pragma: no cover - interactive fallback
            if not messagebox.askyesno("Save Failed", f"Saving annotations failed:\n{exception}\n\nClose anyway?"):
                return
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
