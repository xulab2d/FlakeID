"""Build static figures for the July 2026 FlakeID pass performance report.

The script intentionally uses only Pillow and the standard library so it can run
in the bundled Codex runtime without downloading plotting packages.
"""

from __future__ import annotations

import json
import math
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "docs" / "assets" / "pass_performance_2026_07_13"

BG = "#ffffff"
PANEL = "#ffffff"
INK = "#2c2a29"
MUTED = "#5f6062"
GRID = "#e3e3e3"
UW_PURPLE = "#4b2e83"
UW_GOLD = "#b7a57a"
UW_METALLIC_GOLD = "#85754d"
UW_LAVENDER = "#8f7bb8"
UW_GRAY = "#6c6d6f"
COLORS = [UW_PURPLE, UW_GOLD, UW_METALLIC_GOLD, UW_GRAY, UW_LAVENDER, "#c8c9c7"]


def load_json(rel_path: str) -> Any:
    with (ROOT / rel_path).open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_assets() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = [
        ASSET_DIR / "fonts" / ("OpenSans-Bold.ttf" if bold else "OpenSans-Regular.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


FONT = {
    "title": font(34, True),
    "subtitle": font(18),
    "axis": font(15),
    "small": font(13),
    "tiny": font(11),
    "label": font(17, True),
    "value": font(15, True),
}


def text_size(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> tuple[int, int]:
    box = draw.textbbox((0, 0), text, font=fnt)
    return box[2] - box[0], box[3] - box[1]


def draw_centered(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    fnt: ImageFont.ImageFont,
    fill: str = INK,
) -> None:
    w, h = text_size(draw, text, fnt)
    draw.text((xy[0] - w / 2, xy[1] - h / 2), text, font=fnt, fill=fill)


def draw_right(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    fnt: ImageFont.ImageFont,
    fill: str = INK,
) -> None:
    w, _ = text_size(draw, text, fnt)
    draw.text((xy[0] - w, xy[1]), text, font=fnt, fill=fill)


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    fnt: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        words = para.split()
        line = ""
        for word in words:
            candidate = word if not line else f"{line} {word}"
            if text_size(draw, candidate, fnt)[0] <= max_width:
                line = candidate
            else:
                if line:
                    lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


def pct(v: float | None) -> str:
    if v is None:
        return "--"
    return f"{100.0 * v:.1f}%"


def rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, outline: str | None = None) -> None:
    draw.rectangle(box, fill=fill, outline=outline)


def draw_legend(
    draw: ImageDraw.ImageDraw,
    items: list[tuple[str, str]],
    x: int,
    y: int,
    gap: int = 22,
) -> None:
    cx = x
    for label, color in items:
        draw.rectangle((cx, y + 4, cx + 18, y + 18), fill=color, outline=color)
        draw.text((cx + 26, y), label, font=FONT["axis"], fill=INK)
        cx += text_size(draw, label, FONT["axis"])[0] + gap + 44


def save_canvas(img: Image.Image, name: str) -> None:
    path = ASSET_DIR / name
    img.save(path, quality=94)
    print(path)


def grouped_metric_chart() -> None:
    rows = [
        ("Graphene\nfirst ML\nflake", [0.965517, 0.952941, 0.952941, 0.952941]),
        ("Graphene\nfirst ML\nusable", [0.877778, 0.945455, 0.866667, 0.904348]),
        ("Graphene\nsecond\npass", [0.912281, 0.604167, 0.725000, 0.659091]),
        ("HBN\nlogistic\nbaseline", [0.964744, 0.888889, 0.640000, 0.744186]),
        ("HBN first\npass torch", [0.993590, 1.000000, 0.920000, 0.958333]),
        ("HBN second\npass region", [0.919118, 0.900000, 0.473684, 0.620690]),
    ]
    metrics = ["Accuracy", "Precision", "Recall", "F1"]

    width, height = 1680, 1020
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((56, 34), "Held-out validation metrics by pass", font=FONT["title"], fill=INK)
    draw.text(
        (58, 82),
        "Bars show validation metrics from saved model summaries; deterministic proposal stages are covered by funnel/yield plots.",
        font=FONT["subtitle"],
        fill=MUTED,
    )

    left, top, right, bottom = 110, 150, 1620, 780
    draw.line((left, bottom, right, bottom), fill=INK, width=2)
    draw.line((left, top, left, bottom), fill=INK, width=2)
    for i in range(6):
        value = i / 5
        y = bottom - int(value * (bottom - top))
        draw.line((left, y, right, y), fill=GRID, width=1)
        draw_right(draw, (left - 12, y - 10), f"{int(value * 100)}%", FONT["small"], MUTED)

    group_w = (right - left) / len(rows)
    bar_w = min(40, group_w / 7)
    for gi, (label, values) in enumerate(rows):
        base_x = left + group_w * gi
        center_x = base_x + group_w / 2
        start_x = center_x - (len(metrics) * bar_w + (len(metrics) - 1) * 8) / 2
        for mi, value in enumerate(values):
            x0 = int(start_x + mi * (bar_w + 8))
            x1 = int(x0 + bar_w)
            y0 = bottom - int(value * (bottom - top))
            draw.rectangle((x0, y0, x1, bottom), fill=COLORS[mi])
            if value >= 0.93 or (mi in (2, 3) and value <= 0.66):
                draw_centered(draw, ((x0 + x1) / 2, y0 - 14), f"{value:.2f}", FONT["tiny"], INK)
        for li, line in enumerate(label.split("\n")):
            draw_centered(draw, (center_x, bottom + 28 + li * 20), line, FONT["small"], INK)

    draw_legend(draw, [(m, COLORS[i]) for i, m in enumerate(metrics)], left, height - 106)
    draw.text(
        (left, height - 52),
        "HBN region-domain second pass trades recall for high precision at threshold 0.95; HBN first-pass torch sharply improves recall over the logistic baseline.",
        font=FONT["small"],
        fill=MUTED,
    )
    save_canvas(img, "validation_metrics_by_pass.png")


def ranking_metric_chart() -> None:
    rows = [
        ("Graphene\nsecond pass", [0.702935, 0.939983, 0.900000]),
        ("HBN combined\nsecond pass", [0.433163, 0.770995, 0.400000]),
        ("HBN region\nsecond pass", [0.609880, 0.763427, 0.900000]),
        ("HBN region\ngate v2", [0.231827, 0.399461, 0.300000]),
    ]
    metrics = ["Average precision", "ROC AUC", "Precision@10"]

    width, height = 1380, 820
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((54, 34), "Second-pass ranking behavior", font=FONT["title"], fill=INK)
    draw.text(
        (56, 82),
        "Ranking metrics matter because the post-scan workflow reviews the top candidates first, not a random sample.",
        font=FONT["subtitle"],
        fill=MUTED,
    )
    left, top, right, bottom = 110, 150, 1320, 660
    draw.line((left, bottom, right, bottom), fill=INK, width=2)
    draw.line((left, top, left, bottom), fill=INK, width=2)
    for i in range(6):
        value = i / 5
        y = bottom - int(value * (bottom - top))
        draw.line((left, y, right, y), fill=GRID, width=1)
        draw_right(draw, (left - 12, y - 10), f"{value:.1f}", FONT["small"], MUTED)

    group_w = (right - left) / len(rows)
    bar_w = min(58, group_w / 5.3)
    for gi, (label, values) in enumerate(rows):
        base_x = left + group_w * gi
        center_x = base_x + group_w / 2
        start_x = center_x - (len(metrics) * bar_w + (len(metrics) - 1) * 10) / 2
        for mi, value in enumerate(values):
            x0 = int(start_x + mi * (bar_w + 10))
            x1 = int(x0 + bar_w)
            y0 = bottom - int(value * (bottom - top))
            draw.rectangle((x0, y0, x1, bottom), fill=COLORS[mi])
            draw_centered(draw, ((x0 + x1) / 2, y0 - 14), f"{value:.2f}", FONT["tiny"], INK)
        for li, line in enumerate(label.split("\n")):
            draw_centered(draw, (center_x, bottom + 28 + li * 20), line, FONT["small"], INK)
    draw_legend(draw, [(m, COLORS[i]) for i, m in enumerate(metrics)], left, height - 86)
    draw.text(
        (left, height - 44),
        "The HBN region-domain model is the best high-precision review sorter; the region-gate-only variant overcorrects and is not the preferred model.",
        font=FONT["small"],
        fill=MUTED,
    )
    save_canvas(img, "good_bad_ranking_metrics.png")


def funnel_chart() -> None:
    rows = [
        ("Graphene 2026-05-14", [("detector candidates", 7023), ("first-pass selected", 30), ("second-pass good", 3)]),
        ("HBN BN1r2 2026-05-15", [("detector candidates", 8350), ("first-pass selected", 660), ("second-pass good", 67)]),
        ("HBN AutoBN 2026-05-20", [("detector candidates", 7858), ("first-pass at 0.5", 0), ("second-pass good", 0)]),
    ]
    width, height = 1480, 860
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((54, 32), "Application funnels on full scans", font=FONT["title"], fill=INK)
    draw.text(
        (56, 82),
        "Log-scaled bars compare detector volume, first-pass triage, and second-pass final picks.",
        font=FONT["subtitle"],
        fill=MUTED,
    )
    left, top, right = 460, 150, 1370
    row_h = 180
    max_count = max(v for _, stages in rows for _, v in stages)
    log_max = math.log10(max_count + 1)
    for ri, (label, stages) in enumerate(rows):
        y = top + ri * row_h
        draw.text((56, y + 8), label, font=FONT["label"], fill=INK)
        for si, (stage, count) in enumerate(stages):
            yy = y + 50 + si * 42
            draw.text((left - 18 - text_size(draw, stage, FONT["small"])[0], yy + 2), stage, font=FONT["small"], fill=MUTED)
            bar_len = 4 if count == 0 else int((math.log10(count + 1) / log_max) * (right - left))
            draw.rectangle((left, yy, left + bar_len, yy + 24), fill=COLORS[si])
            draw.text((left + bar_len + 12, yy + 1), f"{count:,}", font=FONT["value"], fill=INK)
        draw.line((56, y + row_h - 18, right, y + row_h - 18), fill=GRID, width=1)
    draw_legend(draw, [("detector", COLORS[0]), ("first ML", COLORS[1]), ("second pass", COLORS[2])], left, height - 92)
    draw.text(
        (56, height - 48),
        "AutoBN was a stress case: first-pass threshold 0.5 produced zero positives, so the run fell back to the top 1,500 near-zero scores and still produced zero good flakes.",
        font=FONT["small"],
        fill=MUTED,
    )
    save_canvas(img, "application_funnel_counts.png")


def autofocus_winners_chart() -> None:
    summary = load_json("outputs/autofocus_benchmark_summary.json")
    metrics = [
        ("Boundary", "current_chip_corner_boundary"),
        ("Focus score", "current_chip_corner_focus_score"),
        ("Corner Tenengrad", "corner_crop_tenengrad"),
        ("Corner mod. Lap.", "corner_crop_modified_laplacian"),
        ("Edge Tenengrad", "edge_hmean_tenengrad"),
        ("Edge mod. Lap.", "edge_hmean_modified_laplacian"),
    ]
    width, height = 1520, 820
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((54, 34), "Autofocus benchmark: coarse winners out of 14 stacks", font=FONT["title"], fill=INK)
    draw.text(
        (56, 82),
        "A coarse winner means the metric selected a frame from the coarse sweep instead of chasing a later fine-frame failure.",
        font=FONT["subtitle"],
        fill=MUTED,
    )
    left, top, right, bottom = 110, 150, 1450, 650
    draw.line((left, bottom, right, bottom), fill=INK, width=2)
    draw.line((left, top, left, bottom), fill=INK, width=2)
    for value in range(0, 15, 2):
        y = bottom - int((value / 14) * (bottom - top))
        draw.line((left, y, right, y), fill=GRID, width=1)
        draw_right(draw, (left - 12, y - 10), str(value), FONT["small"], MUTED)

    group_w = (right - left) / len(metrics)
    bar_w = 52
    for gi, (label, key) in enumerate(metrics):
        center_x = left + group_w * gi + group_w / 2
        values = [
            ("crop 0.35", summary["crop035"][key]["coarse_winners"], COLORS[0]),
            ("crop 0.50", summary["crop05"][key]["coarse_winners"], COLORS[2]),
        ]
        start_x = center_x - 62
        for bi, (_, value, color) in enumerate(values):
            x0 = int(start_x + bi * 70)
            x1 = x0 + bar_w
            y0 = bottom - int((value / 14) * (bottom - top))
            draw.rectangle((x0, y0, x1, bottom), fill=color)
            draw_centered(draw, ((x0 + x1) / 2, y0 - 15), str(value), FONT["small"], INK)
        lines = wrap_text(draw, label, FONT["small"], int(group_w) - 20)
        for li, line in enumerate(lines):
            draw_centered(draw, (center_x, bottom + 28 + li * 18), line, FONT["small"], INK)
    draw_legend(draw, [("corner crop 0.35", COLORS[0]), ("corner crop 0.50", COLORS[2])], left, height - 84)
    draw.text(
        (left, height - 44),
        "The larger ROI improves the chip-boundary metric and edge aggregates, while corner Tenengrad stays strong across both crops.",
        font=FONT["small"],
        fill=MUTED,
    )
    save_canvas(img, "autofocus_coarse_winners.png")


def autofocus_curve_chart() -> None:
    data = load_json("outputs/autofocus_benchmark_top_left_failures_crop05.json")
    stack = None
    for candidate in data["stacks"]:
        if "20260502T014737Z" in candidate["autofocus_result_path"]:
            stack = candidate
            break
    if stack is None:
        stack = data["stacks"][0]
    rows = stack["rows"]
    series = [
        ("Boundary", "current_chip_corner_boundary", COLORS[0]),
        ("Corner Tenengrad", "corner_crop_tenengrad", COLORS[1]),
        ("Corner mod. Lap.", "corner_crop_modified_laplacian", COLORS[2]),
    ]
    width, height = 1460, 820
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((54, 34), "Autofocus failure-stack metric curves", font=FONT["title"], fill=INK)
    draw.text(
        (56, 82),
        "Scores are normalized per metric for the 2026-05-02 top-left failure stack with crop fraction 0.50.",
        font=FONT["subtitle"],
        fill=MUTED,
    )
    left, top, right, bottom = 110, 150, 1370, 650
    draw.line((left, bottom, right, bottom), fill=INK, width=2)
    draw.line((left, top, left, bottom), fill=INK, width=2)
    for i in range(6):
        value = i / 5
        y = bottom - int(value * (bottom - top))
        draw.line((left, y, right, y), fill=GRID, width=1)
        draw_right(draw, (left - 12, y - 10), f"{value:.1f}", FONT["small"], MUTED)
    indices = [row["linear_index"] for row in rows]
    min_i, max_i = min(indices), max(indices)

    def x_of(idx: float) -> int:
        if max_i == min_i:
            return left
        return left + int(((idx - min_i) / (max_i - min_i)) * (right - left))

    for row in rows:
        x = x_of(row["linear_index"])
        if row["phase"] == "fine":
            draw.line((x, top, x, bottom), fill="#f0f0f0", width=1)
    for label, key, color in series:
        values = [float(row[key]) for row in rows]
        lo, hi = min(values), max(values)
        pts = []
        for row, value in zip(rows, values):
            norm = 0.5 if hi == lo else (value - lo) / (hi - lo)
            pts.append((x_of(row["linear_index"]), bottom - int(norm * (bottom - top))))
        draw.line(pts, fill=color, width=4)
        for row, pt in zip(rows, pts):
            r = 5 if row["phase"] == "coarse" else 4
            draw.ellipse((pt[0] - r, pt[1] - r, pt[0] + r, pt[1] + r), fill=color, outline=PANEL, width=2)
    draw.text((left, bottom + 24), "sample index: coarse sweep first, fine sweep shaded", font=FONT["small"], fill=MUTED)
    draw.text((left, height - 48), "The key operational lesson was to avoid flat or unstable local fine-frame preferences and preserve robust chip-corner context.", font=FONT["small"], fill=MUTED)
    draw_legend(draw, [(label, color) for label, _, color in series], left, height - 88)
    save_canvas(img, "autofocus_problem_stack_curve.png")


def safe_path(path_text: str | None) -> Path | None:
    if not path_text:
        return None
    path = Path(path_text)
    if path.exists():
        return path
    # If the repo was moved, recover by replacing everything before .repo_push.
    parts = list(path.parts)
    if ".repo_push" in parts:
        rel = Path(*parts[parts.index(".repo_push") + 1 :])
        candidate = ROOT / rel
        if candidate.exists():
            return candidate
    return None


def crop_candidate(row: dict[str, Any], thumb_size: tuple[int, int]) -> Image.Image:
    image_path = safe_path(row.get("image_path"))
    bbox = row.get("bbox_xywh")
    if image_path is not None and bbox:
        with Image.open(image_path) as original:
            original = ImageOps.exif_transpose(original).convert("RGB")
            x, y, w, h = [float(v) for v in bbox]
            cx, cy = x + w / 2, y + h / 2
            crop_side = max(w, h) * 3.0
            crop_side = max(crop_side, 260.0)
            left = max(0, int(cx - crop_side / 2))
            top = max(0, int(cy - crop_side / 2))
            right = min(original.width, int(cx + crop_side / 2))
            bottom = min(original.height, int(cy + crop_side / 2))
            crop = original.crop((left, top, right, bottom))
            crop = ImageOps.pad(crop, thumb_size, method=Image.Resampling.LANCZOS, color=(255, 255, 255))
            scale_x = thumb_size[0] / max(1, right - left)
            scale_y = thumb_size[1] / max(1, bottom - top)
            rx0 = int((x - left) * scale_x)
            ry0 = int((y - top) * scale_y)
            rx1 = int((x + w - left) * scale_x)
            ry1 = int((y + h - top) * scale_y)
            d = ImageDraw.Draw(crop)
            d.rectangle((rx0, ry0, rx1, ry1), outline=UW_GOLD, width=3)
            d.rectangle((rx0 + 1, ry0 + 1, rx1 - 1, ry1 - 1), outline=INK, width=1)
            return crop
    crop_path = safe_path(row.get("crop_path"))
    if crop_path is not None:
        with Image.open(crop_path) as original:
            return ImageOps.pad(ImageOps.exif_transpose(original).convert("RGB"), thumb_size, method=Image.Resampling.LANCZOS)
    return Image.new("RGB", thumb_size, "#f2f2f2")


def select_rows(
    rows: list[dict[str, Any]],
    predicate,
    score_key: str,
    n: int = 3,
    excluded_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    excluded_ids = excluded_ids or set()
    candidates = [r for r in rows if predicate(r) and r.get("candidate_id") not in excluded_ids]
    candidates.sort(key=lambda r: float(r.get(score_key, 0.0) or 0.0), reverse=True)
    picked: list[dict[str, Any]] = []
    used_tiles: set[str] = set()
    for row in candidates:
        tile = row.get("tile_name") or row.get("image_path") or row.get("candidate_id")
        if tile in used_tiles and len(candidates) > n * 2:
            continue
        picked.append(row)
        used_tiles.add(tile)
        if len(picked) == n:
            break
    if len(picked) < n:
        for row in candidates:
            if row not in picked:
                picked.append(row)
                if len(picked) == n:
                    break
    return picked


def label_for(row: dict[str, Any], kind: str) -> list[str]:
    cid = row.get("candidate_index")
    tile = row.get("tile_name", "")
    short_tile = tile.replace(".jpg", "")
    if len(short_tile) > 26:
        short_tile = short_tile[:23] + "..."
    first = f"{short_tile} c{cid}" if cid is not None else short_tile
    if kind == "det":
        second = f"detector {float(row.get('detector_score', 0.0) or 0.0):.2f}"
    elif kind == "first":
        second = f"flake p={float(row.get('flake_probability', 0.0) or 0.0):.2f}"
    else:
        second = f"good p={float(row.get('good_probability', 0.0) or 0.0):.2f}"
    size = row.get("bbox_long_um")
    third = f"long {float(size):.1f} um" if size else ""
    return [part for part in [first, second, third] if part]


def category_grid(
    material: str,
    all_rows: list[dict[str, Any]],
    good_rows: list[dict[str, Any]],
    out_name: str,
) -> None:
    good_ids = {r.get("candidate_id") for r in good_rows if r.get("predicted_good")}
    columns = [
        (
            "deterministic feature",
            select_rows(all_rows, lambda r: not bool(r.get("predicted_flake")), "detector_score", n=3),
            "det",
        ),
        (
            "first ML flake",
            select_rows(all_rows, lambda r: bool(r.get("predicted_flake")), "flake_probability", n=3, excluded_ids=good_ids),
            "first",
        ),
        (
            "second pass good",
            select_rows(good_rows, lambda r: bool(r.get("predicted_good")), "good_probability", n=3),
            "good",
        ),
    ]
    cell_w, cell_h = 330, 252
    rows_n = 3
    margin_x, title_h, header_h = 42, 62, 56
    width = margin_x * 2 + cell_w * 3
    height = 38 + title_h + header_h + rows_n * cell_h + 34
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    draw.text((42, 28), f"{material}: examples by pass category", font=FONT["title"], fill=INK)
    draw.text((44, 74), "Each crop is centered on the saved detector bbox; gold box marks the candidate.", font=FONT["small"], fill=MUTED)
    start_y = 38 + title_h
    thumb_size = (292, 166)
    for ci, (header, rows, kind) in enumerate(columns):
        x = margin_x + ci * cell_w
        draw_centered(draw, (x + cell_w / 2, start_y + 22), header, FONT["label"], INK)
        for ri in range(rows_n):
            y = start_y + header_h + ri * cell_h
            rounded_rect(draw, (x + 10, y + 10, x + cell_w - 10, y + cell_h - 12), PANEL, "#e0e4e8")
            if ri < len(rows):
                row = rows[ri]
                crop = crop_candidate(row, thumb_size)
                img.paste(crop, (x + 19, y + 20))
                labels = label_for(row, kind)
                label_y = y + 196
                for li, line in enumerate(labels[:3]):
                    draw_centered(draw, (x + cell_w / 2, label_y + li * 18), line, FONT["tiny" if li == 0 else "small"], MUTED if li == 0 else INK)
            else:
                draw_centered(draw, (x + cell_w / 2, y + cell_h / 2), "no additional thresholded example", FONT["small"], MUTED)
    save_canvas(img, out_name)


def build_grids() -> None:
    graphene_all = load_json(
        "photos/scans/20260514T014605Z_flake_grid_001/qc/post_scan/baseline/all_candidate_predictions.json"
    )
    graphene_good = load_json(
        "photos/scans/20260514T014605Z_flake_grid_001/qc/post_scan/good_bad/ranked_good_bad_candidates.json"
    )
    hbn_all = load_json(
        "photos/scans/20260515T051601Z_Isaac_BN1r2/qc/post_scan/hbn_first_pass_torch/first_pass_torch_predictions.json"
    )
    hbn_good = load_json(
        "photos/scans/20260515T051601Z_Isaac_BN1r2/qc/post_scan/hbn_good_bad/ranked_good_bad_candidates.json"
    )
    category_grid("Graphene", graphene_all, graphene_good, "flake_category_grid_graphene.png")
    category_grid("HBN", hbn_all, hbn_good, "flake_category_grid_hbn.png")


def copy_autofocus_contact() -> None:
    src = ROOT / "outputs" / "autofocus_contacts" / "20260502T014737Z_flake_grid_001_top_left_contact.jpg"
    dst = ASSET_DIR / "autofocus_top_left_failure_contact.jpg"
    if src.exists():
        with Image.open(src) as img:
            img = ImageOps.exif_transpose(img).convert("RGB")
            img.thumbnail((1600, 1000), Image.Resampling.LANCZOS)
            img.save(dst, quality=92)
            print(dst)
    else:
        fallback = ROOT / "outputs" / "autofocus_contacts" / "20260501T014219Z_flake_grid_001_top_left_contact.jpg"
        if fallback.exists():
            shutil.copyfile(fallback, dst)
            print(dst)


def report_data() -> None:
    data = {
        "generated_from": {
            "graphene_first_pass": "outputs/candidate_baseline_20260508/candidate_baseline_summary.json",
            "graphene_second_pass": "outputs/candidate_good_bad_torch_20260511_run3/good_bad_torch_summary.json",
            "hbn_logistic_baseline": "outputs/candidate_baseline_hbn_20260515_first_pass/candidate_baseline_summary.json",
            "hbn_first_pass_torch": "outputs/first_pass_torch_hbn_20260515/first_pass_torch_summary.json",
            "hbn_second_pass_region": "outputs/candidate_good_bad_torch_hbn_20260519_region_domains/good_bad_torch_summary.json",
            "autofocus": "outputs/autofocus_benchmark_summary.json",
        },
        "figures": [
            "validation_metrics_by_pass.png",
            "good_bad_ranking_metrics.png",
            "application_funnel_counts.png",
            "flake_category_grid_graphene.png",
            "flake_category_grid_hbn.png",
            "autofocus_coarse_winners.png",
            "autofocus_problem_stack_curve.png",
            "autofocus_top_left_failure_contact.jpg",
        ],
    }
    with (ASSET_DIR / "report_data.json").open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def main() -> None:
    ensure_assets()
    grouped_metric_chart()
    ranking_metric_chart()
    funnel_chart()
    autofocus_winners_chart()
    autofocus_curve_chart()
    build_grids()
    copy_autofocus_contact()
    report_data()


if __name__ == "__main__":
    main()
