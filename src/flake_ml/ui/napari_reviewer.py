from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from ..annotation.manual import (
    ManualImageAnnotation,
    ManualObjectAnnotation,
    VALID_OBJECT_LABELS,
    VALID_PRIORITY_CLASSES,
    VALID_SHAPE_CLASSES,
    VALID_SIZE_CLASSES,
    VALID_THICKNESS_BINS,
    VALID_TILE_LABELS,
    discover_images,
    load_manual_annotations,
    normalize_choice,
    save_manual_annotations,
)
from ..utils import timestamp_utc


OBJECT_LABEL_COLORS = {
    "graphene": "#33d17a",
    "hbn": "#3584e4",
    "other_flake": "#f6d32d",
    "artifact": "#f66151",
}

TILE_LABEL_SHORTCUTS = (
    ("1", "empty_substrate"),
    ("2", "flake_present"),
    ("3", "off_target"),
    ("4", "bad_focus"),
    ("5", "artifact"),
    ("6", "unsure"),
)


def _normalize_object_label(value: object, fallback: str) -> str:
    return normalize_choice(value, VALID_OBJECT_LABELS, fallback)


def _sanitize_shape_labels(raw_labels: list[object], count: int, fallback: str) -> list[str]:
    return [
        _normalize_object_label(raw_labels[index] if index < len(raw_labels) else None, fallback)
        for index in range(count)
    ]


OBJECT_PROPERTY_ORDER = (
    "label",
    "thickness_bin",
    "size_class",
    "shape_class",
    "priority",
)

OBJECT_PROPERTY_OPTIONS = {
    "label": VALID_OBJECT_LABELS,
    "thickness_bin": VALID_THICKNESS_BINS,
    "size_class": VALID_SIZE_CLASSES,
    "shape_class": VALID_SHAPE_CLASSES,
    "priority": VALID_PRIORITY_CLASSES,
}

OBJECT_PROPERTY_LABELS = {
    "label": "Flake Label",
    "thickness_bin": "Thickness",
    "size_class": "Size",
    "shape_class": "Shape",
    "priority": "Priority",
}


def _normalize_feature_value(key: str, value: object, fallback: str) -> str:
    return normalize_choice(value, OBJECT_PROPERTY_OPTIONS[key], fallback)


def _sanitize_feature_values(key: str, raw_values: list[object], count: int, fallback: str) -> list[str]:
    return [
        _normalize_feature_value(key, raw_values[index] if index < len(raw_values) else None, fallback)
        for index in range(count)
    ]


def _image_key(image_path: str | Path) -> str:
    return str(Path(image_path).resolve())


def _annotation_is_reviewed(annotation: ManualImageAnnotation | None) -> bool:
    if annotation is None:
        return False
    return annotation.tile_label != "unreviewed" or bool(annotation.objects) or bool(annotation.notes.strip())


def _find_resume_index(images: list[Path], annotations: dict[str, ManualImageAnnotation]) -> int:
    if not images:
        return 0
    keyed_annotations = {
        _image_key(image_path): annotation
        for image_path, annotation in annotations.items()
    }
    latest_index = 0
    latest_updated = ""
    for index, image_path in enumerate(images):
        annotation = keyed_annotations.get(_image_key(image_path))
        if annotation is None:
            continue
        updated = str(annotation.updated_utc or "")
        if updated and updated >= latest_updated:
            latest_updated = updated
            latest_index = index
    if latest_updated:
        return latest_index
    for index, image_path in enumerate(images):
        if _annotation_is_reviewed(keyed_annotations.get(_image_key(image_path))):
            latest_index = index
    return latest_index


def _resolve_jump_index(images: list[Path], query: str) -> tuple[int | None, str | None]:
    if not images:
        return None, "No images are loaded."
    value = str(query or "").strip()
    if not value:
        return None, "Type an image number or part of a filename."
    if value.isdigit():
        requested = int(value)
        if 1 <= requested <= len(images):
            return requested - 1, None
        return None, f"Image number {requested} is outside 1-{len(images)}."

    normalized = value.lower()
    matches = [
        index
        for index, image_path in enumerate(images)
        if normalized in image_path.name.lower()
    ]
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, f"'{value}' matches {len(matches)} images. Use a more specific filename fragment."
    return None, f"No image name contains '{value}'."


def _import_napari_modules():
    try:
        import napari
        from qtpy.QtGui import QKeySequence, QShortcut
        from qtpy.QtWidgets import (
            QComboBox,
            QHBoxLayout,
            QLabel,
            QLineEdit,
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
        "QLineEdit": QLineEdit,
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


def _feature_values_from_layer(layer, key: str) -> list[object]:
    features = getattr(layer, "features", None)
    if features is None:
        return []
    values = None
    if isinstance(features, dict):
        values = features.get(key, [])
    else:
        try:
            values = features[key]
        except Exception:
            getter = getattr(features, "get", None)
            if getter is not None:
                values = getter(key, [])
    if values is None:
        return []
    if hasattr(values, "tolist"):
        values = values.tolist()
    return list(values)


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
        self.index = _find_resume_index(self.images, self.annotations)
        self.resume_index = self.index
        self.current_image_path: Path | None = None
        self.image_layer = None
        self.shapes_layer = None
        self._is_loading_layer = False
        self.object_property_widgets: dict[str, object] = {}

        self.dock_widget = self._build_ui()
        self._install_shortcuts()
        self._load_current_image(reset_view=True)

    def _build_ui(self):
        QWidget = self.widgets["QWidget"]
        QVBoxLayout = self.widgets["QVBoxLayout"]
        QHBoxLayout = self.widgets["QHBoxLayout"]
        QLabel = self.widgets["QLabel"]
        QLineEdit = self.widgets["QLineEdit"]
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

        jump_row = QHBoxLayout()
        self.jump_input = QLineEdit()
        self.jump_input.setPlaceholderText("Image # or filename")
        self.jump_input.returnPressed.connect(self._jump_to_query)
        jump_row.addWidget(self.jump_input)
        self.jump_button = QPushButton("Jump")
        self.jump_button.clicked.connect(self._jump_to_query)
        jump_row.addWidget(self.jump_button)
        self.resume_button = QPushButton("Resume")
        self.resume_button.clicked.connect(self.jump_to_resume)
        jump_row.addWidget(self.resume_button)
        layout.addLayout(jump_row)

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

        for key in OBJECT_PROPERTY_ORDER:
            property_label = QLabel(OBJECT_PROPERTY_LABELS[key])
            layout.addWidget(property_label)
            combo = QComboBox()
            combo.addItems(list(OBJECT_PROPERTY_OPTIONS[key]))
            combo.currentTextChanged.connect(lambda _value, property_key=key: self._on_object_property_changed(property_key))
            layout.addWidget(combo)
            self.object_property_widgets[key] = combo

        self.apply_label_button = QPushButton("Apply Metadata To Selected")
        self.apply_label_button.clicked.connect(self._apply_metadata_to_selected)
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
            "Tile labels distinguish empty substrate from off-target and bad-focus frames.\n"
            "napari keys: P polygon, R rectangle, S select, Delete removes selected shapes.\n"
            "Review keys: 1 empty_substrate, 2 flake_present, 3 off_target, 4 bad_focus, 5 artifact, 6 unsure.\n"
            "Set label, thickness, size, shape, and priority in the dock, then click Apply Metadata To Selected.\n"
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
        focus_jump_shortcut = QShortcut(QKeySequence("Ctrl+L"), parent)
        focus_jump_shortcut.activated.connect(self.jump_input.setFocus)
        execute_jump_shortcut = QShortcut(QKeySequence("Ctrl+G"), parent)
        execute_jump_shortcut.activated.connect(self._jump_to_query)
        resume_shortcut = QShortcut(QKeySequence("Ctrl+J"), parent)
        resume_shortcut.activated.connect(self.jump_to_resume)
        for key, label in TILE_LABEL_SHORTCUTS:
            label_shortcut = QShortcut(QKeySequence(key), parent)
            label_shortcut.activated.connect(lambda tile_label=label: self._set_tile_label(tile_label))
            setattr(self, f"_tile_shortcut_{key}", label_shortcut)
        self._focus_jump_shortcut = focus_jump_shortcut
        self._execute_jump_shortcut = execute_jump_shortcut
        self._resume_shortcut = resume_shortcut

    def _annotation_for(self, image_path: Path) -> ManualImageAnnotation:
        key = str(image_path.resolve())
        if key not in self.annotations:
            self.annotations[key] = ManualImageAnnotation(image_path=key)
        return self.annotations[key]

    def _property_widget_value(self, key: str) -> str:
        widget = self.object_property_widgets[key]
        return str(widget.currentText())

    def _current_shape_feature_values(self, key: str) -> list[str]:
        if self.shapes_layer is None:
            return []
        values = _feature_values_from_layer(self.shapes_layer, key)
        count = len(self.shapes_layer.data)
        return _sanitize_feature_values(key, values, count, self._property_widget_value(key))

    def _current_shape_features(self) -> dict[str, list[str]]:
        if self.shapes_layer is None:
            return {key: [] for key in OBJECT_PROPERTY_ORDER}
        return {
            key: self._current_shape_feature_values(key)
            for key in OBJECT_PROPERTY_ORDER
        }

    def _set_shape_features(self, feature_values: dict[str, list[str]]) -> None:
        if self.shapes_layer is None:
            return
        count = len(self.shapes_layer.data)
        sanitized = {
            key: _sanitize_feature_values(key, feature_values.get(key, []), count, self._property_widget_value(key))
            for key in OBJECT_PROPERTY_ORDER
        }
        try:
            self.shapes_layer.features = {
                key: np.asarray(values, dtype=object)
                for key, values in sanitized.items()
            }
        except Exception:
            pass

    def _set_property_widget_value(self, key: str, value: object) -> None:
        widget = self.object_property_widgets[key]
        normalized = _normalize_feature_value(key, value, OBJECT_PROPERTY_OPTIONS[key][0])
        widget.blockSignals(True)
        widget.setCurrentText(normalized)
        widget.blockSignals(False)

    def _current_property_defaults(self) -> dict[str, np.ndarray]:
        return {
            key: np.asarray([self._property_widget_value(key)], dtype=object)
            for key in OBJECT_PROPERTY_ORDER
        }

    def _set_current_feature_defaults(self) -> None:
        if self.shapes_layer is None:
            return
        defaults = self._current_property_defaults()
        try:
            self.shapes_layer.current_properties = defaults
        except Exception:
            pass
        try:
            self.shapes_layer.feature_defaults = defaults
        except Exception:
            pass

    def _refresh_shape_styles(self) -> None:
        if self.shapes_layer is None:
            return
        feature_values = self._current_shape_features()
        labels = feature_values.get("label", [])
        self._set_shape_features(feature_values)
        if labels:
            colors = [OBJECT_LABEL_COLORS.get(label, "#ffffff") for label in labels]
            self.shapes_layer.edge_color = colors
        else:
            self.shapes_layer.edge_color = OBJECT_LABEL_COLORS.get(self._property_widget_value("label"), "#ffffff")
        try:
            self.shapes_layer.face_color = "transparent"
        except Exception:
            pass
        try:
            self.shapes_layer.text = "{label}"
        except Exception:
            pass

    def _annotation_objects_to_layer_payload(
        self,
        objects: list[ManualObjectAnnotation],
    ) -> tuple[list[np.ndarray], list[str], dict[str, list[str]]]:
        data: list[np.ndarray] = []
        shape_types: list[str] = []
        feature_values = {key: [] for key in OBJECT_PROPERTY_ORDER}
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
            feature_values["label"].append(item.label)
            feature_values["thickness_bin"].append(item.thickness_bin)
            feature_values["size_class"].append(item.size_class)
            feature_values["shape_class"].append(item.shape_class)
            feature_values["priority"].append(item.priority)
        return data, shape_types, feature_values

    def _rebuild_shapes_layer(self) -> None:
        if self.current_image_path is None:
            return
        annotation = self._annotation_for(self.current_image_path)
        shape_data, shape_types, feature_values = self._annotation_objects_to_layer_payload(annotation.objects)
        shape_labels = feature_values["label"]

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
                else OBJECT_LABEL_COLORS.get(self._property_widget_value("label"), "#ffffff"),
                face_color="transparent",
                features={
                    key: np.asarray(values, dtype=object)
                    for key, values in feature_values.items()
                },
                property_choices={
                    key: np.asarray(options, dtype=object)
                    for key, options in OBJECT_PROPERTY_OPTIONS.items()
                },
            )
            self.shapes_layer.events.data.connect(self._on_shapes_changed)
            self._set_current_feature_defaults()
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
        first_object = annotation.objects[0] if annotation.objects else None
        for key in OBJECT_PROPERTY_ORDER:
            default_value = getattr(first_object, key, OBJECT_PROPERTY_OPTIONS[key][0]) if first_object else OBJECT_PROPERTY_OPTIONS[key][0]
            self._set_property_widget_value(key, default_value)
        self.path_label.setText(
            f"Image root: {self.image_dir}\n"
            f"Current image ({self.index + 1}/{len(self.images)}): {image_path.name}\n"
            f"Full path: {image_path}"
        )
        self._rebuild_shapes_layer()
        self._update_status()

    def _fit_view(self) -> None:
        self.viewer.reset_view()

    def _set_tile_label(self, label: str) -> None:
        if label not in VALID_TILE_LABELS:
            return
        self.tile_label_combo.setCurrentText(label)
        self._update_status(extra=f"Tile label: {label}")

    def _set_shape_mode(self, mode: str) -> None:
        if self.shapes_layer is None:
            return
        self.shapes_layer.mode = mode
        self._update_status(extra=f"Mode: {mode}")

    def _on_object_property_changed(self, key: str) -> None:
        self._set_current_feature_defaults()
        self._update_status(extra=f"New shapes will use {OBJECT_PROPERTY_LABELS[key].lower()}: {self._property_widget_value(key)}")

    def _apply_metadata_to_selected(self) -> None:
        if self.shapes_layer is None:
            return
        self.shapes_layer.mode = "select"
        feature_values = self._current_shape_features()
        selected = sorted(int(index) for index in self.shapes_layer.selected_data)
        if selected:
            for key in OBJECT_PROPERTY_ORDER:
                selected_value = self._property_widget_value(key)
                values = feature_values[key]
                for index in selected:
                    if 0 <= index < len(values):
                        values[index] = selected_value
            self._set_shape_features(feature_values)
        self._set_current_feature_defaults()
        self._refresh_shape_styles()
        if selected:
            summary = ", ".join(f"{OBJECT_PROPERTY_LABELS[key].lower()}={self._property_widget_value(key)}" for key in OBJECT_PROPERTY_ORDER)
            self._update_status(extra=f"Applied metadata ({summary}) to {len(selected)} selected shape(s).")
        else:
            self._update_status(extra="Updated defaults for new shapes.")

    def _on_shapes_changed(self, _event=None) -> None:
        if self._is_loading_layer:
            return
        self._refresh_shape_styles()
        self._update_status()

    def _objects_from_layer(self) -> list[ManualObjectAnnotation]:
        if self.shapes_layer is None:
            return []
        feature_values = self._current_shape_features()
        shape_types = _shape_types_from_layer(self.shapes_layer)
        objects: list[ManualObjectAnnotation] = []
        for index, raw_vertices in enumerate(list(self.shapes_layer.data)):
            vertices_xy = _from_napari_vertices(np.asarray(raw_vertices, dtype=np.float32))
            label = feature_values["label"][index] if index < len(feature_values["label"]) else self._property_widget_value("label")
            shape_type = shape_types[index] if index < len(shape_types) else "polygon"
            objects.append(
                ManualObjectAnnotation(
                    label=label,
                    shape_type=shape_type,
                    vertices_xy=vertices_xy,
                    thickness_bin=feature_values["thickness_bin"][index] if index < len(feature_values["thickness_bin"]) else "unknown",
                    size_class=feature_values["size_class"][index] if index < len(feature_values["size_class"]) else "unknown",
                    shape_class=feature_values["shape_class"][index] if index < len(feature_values["shape_class"]) else "unknown",
                    priority=feature_values["priority"][index] if index < len(feature_values["priority"]) else "unknown",
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
        self.resume_index = self.index
        save_manual_annotations(self.output_path, self.annotations, self.image_dir)
        self._update_status(extra="Saved.")

    def _jump_to_index(self, index: int, extra: str = "", reset_view: bool = False) -> None:
        if not (0 <= index < len(self.images)):
            self._update_status(extra=f"Image {index + 1} is outside 1-{len(self.images)}.")
            return
        if self.current_image_path is not None:
            self.save_all()
        self.index = index
        self._load_current_image(reset_view=reset_view)
        if extra:
            self._update_status(extra=extra)

    def _jump_to_query(self) -> None:
        index, error = _resolve_jump_index(self.images, self.jump_input.text())
        if error is not None:
            self._update_status(extra=error)
            return
        assert index is not None
        self._jump_to_index(index, extra=f"Jumped to image {index + 1}.")

    def jump_to_resume(self) -> None:
        self._jump_to_index(self.resume_index, extra=f"Resumed at image {self.resume_index + 1}.")

    def prev_image(self) -> None:
        if self.index <= 0:
            return
        self._jump_to_index(self.index - 1)

    def next_image(self) -> None:
        if self.index >= len(self.images) - 1:
            self.save_all()
            return
        self._jump_to_index(self.index + 1)

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
            f"Resume target: {self.resume_index + 1}/{len(self.images)}\n"
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
