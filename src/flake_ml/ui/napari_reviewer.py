from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from ..annotation.manual import (
    ManualImageAnnotation,
    ManualObjectAnnotation,
    VALID_OBJECT_LABELS,
    VALID_TILE_LABELS,
    discover_images,
    load_manual_annotations,
    save_manual_annotations,
)
from ..utils import timestamp_utc


OBJECT_LABEL_COLORS = {
    "graphene": "#33d17a",
    "hbn": "#3584e4",
    "other_flake": "#f6d32d",
    "artifact": "#f66151",
}


def _import_napari_modules():
    try:
        import napari
        from qtpy.QtGui import QKeySequence, QShortcut
        from qtpy.QtWidgets import (
            QComboBox,
            QHBoxLayout,
            QLabel,
            QMessageBox,
            QPushButton,
            QTextEdit,
            QVBoxLayout,
            QWidget,
        )
    except Exception as exc:  # pragma: no cover - dependency gate
        raise ImportError(
            "Napari review requires the local napari runtime. "
            "Launch it with scripts\\launch_napari_review.ps1 so the Qt dependencies are available."
        ) from exc
    return {
        "napari": napari,
        "QComboBox": QComboBox,
        "QHBoxLayout": QHBoxLayout,
        "QKeySequence": QKeySequence,
        "QLabel": QLabel,
        "QMessageBox": QMessageBox,
        "QPushButton": QPushButton,
        "QShortcut": QShortcut,
        "QTextEdit": QTextEdit,
        "QVBoxLayout": QVBoxLayout,
        "QWidget": QWidget,
    }


def _to_napari_vertices(vertices_xy: list[tuple[float, float]]) -> np.ndarray:
    return np.asarray([[y, x] for x, y in vertices_xy], dtype=np.float32)


def _from_napari_vertices(vertices_rc: np.ndarray) -> list[tuple[float, float]]:
    vertices_xy: list[tuple[float, float]] = []
    for row, column in np.asarray(vertices_rc, dtype=np.float32):
        vertices_xy.append((float(column), float(row)))
    return vertices_xy


def _labels_from_features(layer) -> list[str]:
    features = getattr(layer, "features", None)
    if features is None:
        return []
    values = None
    if isinstance(features, dict):
        values = features.get("label", [])
    else:
        try:
            values = features["label"]
        except Exception:
            getter = getattr(features, "get", None)
            if getter is not None:
                values = getter("label", [])
    if values is None:
        return []
    if hasattr(values, "tolist"):
        values = values.tolist()
    return [str(value) for value in list(values)]


def _shape_types_from_layer(layer) -> list[str]:
    value = getattr(layer, "shape_type", [])
    if isinstance(value, str):
        return [value]
    return [str(item) for item in list(value)]


class NapariReviewApp:
    def __init__(self, viewer, widget_module, image_dir: str | Path, output_path: str | Path) -> None:
        self.viewer = viewer
        self.widgets = widget_module
        self.image_dir = Path(image_dir).resolve()
        self.output_path = Path(output_path).resolve()
        self.images = discover_images(self.image_dir)
        if not self.images:
            raise FileNotFoundError(f"No images were found in {self.image_dir}")

        self.annotations = load_manual_annotations(self.output_path)
        self.index = 0
        self.current_image_path: Path | None = None
        self.image_layer = None
        self.shapes_layer = None
        self._is_loading_layer = False

        self.dock_widget = self._build_ui()
        self._install_shortcuts()
        self._load_current_image(reset_view=True)

    def _build_ui(self):
        QWidget = self.widgets["QWidget"]
        QVBoxLayout = self.widgets["QVBoxLayout"]
        QHBoxLayout = self.widgets["QHBoxLayout"]
        QLabel = self.widgets["QLabel"]
        QPushButton = self.widgets["QPushButton"]
        QComboBox = self.widgets["QComboBox"]
        QTextEdit = self.widgets["QTextEdit"]

        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("FlakeID Napari Review")
        layout.addWidget(title)

        nav_row = QHBoxLayout()
        self.prev_button = QPushButton("Prev")
        self.prev_button.clicked.connect(self.prev_image)
        nav_row.addWidget(self.prev_button)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next_image)
        nav_row.addWidget(self.next_button)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_all)
        nav_row.addWidget(self.save_button)
        layout.addLayout(nav_row)

        mode_row = QHBoxLayout()
        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(lambda: self._set_shape_mode("select"))
        mode_row.addWidget(self.select_button)
        self.polygon_button = QPushButton("Polygon")
        self.polygon_button.clicked.connect(lambda: self._set_shape_mode("add_polygon"))
        mode_row.addWidget(self.polygon_button)
        self.rectangle_button = QPushButton("Rectangle")
        self.rectangle_button.clicked.connect(lambda: self._set_shape_mode("add_rectangle"))
        mode_row.addWidget(self.rectangle_button)
        self.fit_button = QPushButton("Fit View")
        self.fit_button.clicked.connect(self._fit_view)
        mode_row.addWidget(self.fit_button)
        layout.addLayout(mode_row)

        tile_label = QLabel("Tile Label")
        layout.addWidget(tile_label)
        self.tile_label_combo = QComboBox()
        self.tile_label_combo.addItems(list(VALID_TILE_LABELS))
        layout.addWidget(self.tile_label_combo)

        object_label = QLabel("Flake Label")
        layout.addWidget(object_label)
        self.object_label_combo = QComboBox()
        self.object_label_combo.addItems(list(VALID_OBJECT_LABELS))
        self.object_label_combo.currentTextChanged.connect(self._on_object_label_changed)
        layout.addWidget(self.object_label_combo)

        self.apply_label_button = QPushButton("Apply Label To Selected")
        self.apply_label_button.clicked.connect(self._apply_label_to_selected)
        layout.addWidget(self.apply_label_button)

        notes_label = QLabel("Notes")
        layout.addWidget(notes_label)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Optional notes for this tile.")
        layout.addWidget(self.notes_edit)

        self.path_label = QLabel("")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        help_label = QLabel(
            "Use polygon mode for precise flake outlines.\n"
            "napari keys: P polygon, R rectangle, S select, Delete removes selected shapes.\n"
            "This tool saves polygons into manual_annotations.json for later COCO export."
        )
        help_label.setWordWrap(True)
        layout.addWidget(help_label)

        layout.addStretch(1)
        return widget

    def _install_shortcuts(self) -> None:
        QShortcut = self.widgets["QShortcut"]
        QKeySequence = self.widgets["QKeySequence"]
        parent = self.viewer.window._qt_window

        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), parent)
        save_shortcut.activated.connect(self.save_all)
        next_shortcut = QShortcut(QKeySequence("]"), parent)
        next_shortcut.activated.connect(self.next_image)
        prev_shortcut = QShortcut(QKeySequence("["), parent)
        prev_shortcut.activated.connect(self.prev_image)

    def _annotation_for(self, image_path: Path) -> ManualImageAnnotation:
        key = str(image_path.resolve())
        if key not in self.annotations:
            self.annotations[key] = ManualImageAnnotation(image_path=key)
        return self.annotations[key]

    def _current_shape_labels(self) -> list[str]:
        if self.shapes_layer is None:
            return []
        labels = _labels_from_features(self.shapes_layer)
        count = len(self.shapes_layer.data)
        if len(labels) < count:
            labels.extend([self.object_label_combo.currentText()] * (count - len(labels)))
        return labels[:count]

    def _set_current_object_label(self, label: str) -> None:
        if label not in VALID_OBJECT_LABELS:
            label = VALID_OBJECT_LABELS[0]
        self.object_label_combo.blockSignals(True)
        self.object_label_combo.setCurrentText(label)
        self.object_label_combo.blockSignals(False)
        if self.shapes_layer is None:
            return
        values = np.asarray([label], dtype=object)
        try:
            self.shapes_layer.current_properties = {"label": values}
        except Exception:
            pass
        try:
            self.shapes_layer.feature_defaults = {"label": values}
        except Exception:
            pass

    def _refresh_shape_styles(self) -> None:
        if self.shapes_layer is None:
            return
        labels = self._current_shape_labels()
        try:
            self.shapes_layer.features = {"label": np.asarray(labels, dtype=object)}
        except Exception:
            pass
        if labels:
            colors = [OBJECT_LABEL_COLORS.get(label, "#ffffff") for label in labels]
            self.shapes_layer.edge_color = colors
        else:
            self.shapes_layer.edge_color = OBJECT_LABEL_COLORS.get(self.object_label_combo.currentText(), "#ffffff")
        try:
            self.shapes_layer.face_color = "transparent"
        except Exception:
            pass
        try:
            self.shapes_layer.text = "label"
        except Exception:
            pass

    def _annotation_objects_to_layer_payload(self, objects: list[ManualObjectAnnotation]) -> tuple[list[np.ndarray], list[str], list[str]]:
        data: list[np.ndarray] = []
        shape_types: list[str] = []
        labels: list[str] = []
        for item in objects:
            vertices_xy = item.display_vertices_xy
            if not vertices_xy:
                continue
            data.append(_to_napari_vertices(vertices_xy))
            if item.shape_type == "rectangle":
                shape_types.append("rectangle")
            elif item.vertices_xy:
                shape_types.append("polygon")
            else:
                shape_types.append("rectangle")
            labels.append(item.label if item.label in VALID_OBJECT_LABELS else VALID_OBJECT_LABELS[0])
        return data, shape_types, labels

    def _rebuild_shapes_layer(self) -> None:
        if self.current_image_path is None:
            return
        annotation = self._annotation_for(self.current_image_path)
        shape_data, shape_types, shape_labels = self._annotation_objects_to_layer_payload(annotation.objects)

        self._is_loading_layer = True
        try:
            if self.shapes_layer is not None and self.shapes_layer in self.viewer.layers:
                self.viewer.layers.remove(self.shapes_layer)
            self.shapes_layer = self.viewer.add_shapes(
                data=shape_data,
                shape_type=shape_types if shape_data else "polygon",
                name="flake_annotations",
                edge_width=2.0,
                edge_color=[OBJECT_LABEL_COLORS.get(label, "#ffffff") for label in shape_labels]
                if shape_labels
                else OBJECT_LABEL_COLORS.get(self.object_label_combo.currentText(), "#ffffff"),
                face_color="transparent",
                features={"label": np.asarray(shape_labels, dtype=object)},
                property_choices={"label": np.asarray(VALID_OBJECT_LABELS, dtype=object)},
            )
            self.shapes_layer.events.data.connect(self._on_shapes_changed)
            self._set_current_object_label(self.object_label_combo.currentText())
            self._refresh_shape_styles()
            self.shapes_layer.mode = "select"
        finally:
            self._is_loading_layer = False

    def _load_current_image(self, reset_view: bool = False) -> None:
        image_path = self.images[self.index]
        image_array = np.asarray(Image.open(image_path).convert("RGB"))
        self.current_image_path = image_path

        if self.image_layer is None:
            self.image_layer = self.viewer.add_image(image_array, rgb=True, name=image_path.name)
        else:
            self.image_layer.data = image_array
            self.image_layer.name = image_path.name
        if reset_view:
            self._fit_view()

        annotation = self._annotation_for(image_path)
        self.tile_label_combo.setCurrentText(
            annotation.tile_label if annotation.tile_label in VALID_TILE_LABELS else "unreviewed"
        )
        self.notes_edit.setPlainText(annotation.notes)
        self.path_label.setText(f"Image root: {self.image_dir}\nCurrent image: {image_path}")
        self._rebuild_shapes_layer()
        self._update_status()

    def _fit_view(self) -> None:
        self.viewer.reset_view()

    def _set_shape_mode(self, mode: str) -> None:
        if self.shapes_layer is None:
            return
        self.shapes_layer.mode = mode
        self._update_status(extra=f"Mode: {mode}")

    def _on_object_label_changed(self, label: str) -> None:
        self._set_current_object_label(label)
        self._update_status(extra=f"New shapes will use label: {label}")

    def _apply_label_to_selected(self) -> None:
        if self.shapes_layer is None:
            return
        self.shapes_layer.mode = "select"
        self.shapes_layer.current_properties = {"label": np.asarray([self.object_label_combo.currentText()], dtype=object)}
        self._refresh_shape_styles()
        self._update_status(extra="Applied label to the selected shape(s).")

    def _on_shapes_changed(self, _event=None) -> None:
        if self._is_loading_layer:
            return
        self._refresh_shape_styles()
        self._update_status()

    def _objects_from_layer(self) -> list[ManualObjectAnnotation]:
        if self.shapes_layer is None:
            return []
        labels = self._current_shape_labels()
        shape_types = _shape_types_from_layer(self.shapes_layer)
        objects: list[ManualObjectAnnotation] = []
        for index, raw_vertices in enumerate(list(self.shapes_layer.data)):
            vertices_xy = _from_napari_vertices(np.asarray(raw_vertices, dtype=np.float32))
            label = labels[index] if index < len(labels) else self.object_label_combo.currentText()
            shape_type = shape_types[index] if index < len(shape_types) else "polygon"
            objects.append(
                ManualObjectAnnotation(
                    label=label,
                    shape_type=shape_type,
                    vertices_xy=vertices_xy,
                )
            )
        return objects

    def _save_current_annotation(self) -> None:
        if self.current_image_path is None:
            return
        annotation = self._annotation_for(self.current_image_path)
        annotation.tile_label = self.tile_label_combo.currentText()
        annotation.notes = self.notes_edit.toPlainText().strip()
        annotation.objects = self._objects_from_layer()
        annotation.updated_utc = timestamp_utc()

    def save_all(self) -> None:
        self._save_current_annotation()
        save_manual_annotations(self.output_path, self.annotations, self.image_dir)
        self._update_status(extra="Saved.")

    def prev_image(self) -> None:
        if self.index <= 0:
            return
        self.save_all()
        self.index -= 1
        self._load_current_image(reset_view=False)

    def next_image(self) -> None:
        if self.index >= len(self.images) - 1:
            self.save_all()
            return
        self.save_all()
        self.index += 1
        self._load_current_image(reset_view=False)

    def _update_status(self, extra: str = "") -> None:
        reviewed = 0
        total_objects = 0
        for annotation in self.annotations.values():
            if annotation.tile_label != "unreviewed" or annotation.objects:
                reviewed += 1
            total_objects += len(annotation.objects)
        current_objects = len(self.shapes_layer.data) if self.shapes_layer is not None else 0
        selected = len(self.shapes_layer.selected_data) if self.shapes_layer is not None else 0
        text = (
            f"Image {self.index + 1}/{len(self.images)}\n"
            f"Reviewed tiles: {reviewed}/{len(self.images)}\n"
            f"Current annotations: {current_objects}\n"
            f"Selected shapes: {selected}\n"
            f"Total annotations: {total_objects}\n"
            f"Output: {self.output_path}"
        )
        if extra:
            text += f"\n{extra}"
        self.status_label.setText(text)


def launch_napari_review(image_dir: str | Path, output_path: str | Path) -> None:
    modules = _import_napari_modules()
    napari = modules["napari"]
    viewer = napari.Viewer(title="FlakeID Napari Review")
    app = NapariReviewApp(viewer, modules, image_dir=image_dir, output_path=output_path)
    viewer.window.add_dock_widget(app.dock_widget, area="right", name="Review")

    try:  # pragma: no branch - GUI lifecycle
        napari.run()
    finally:
        try:
            app.save_all()
        except Exception:
            QMessageBox = modules["QMessageBox"]
            QMessageBox.warning(
                viewer.window._qt_window,
                "Save Failed",
                f"Automatic save failed for {output_path}.",
            )
