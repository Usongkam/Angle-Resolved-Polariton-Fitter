import csv
import json
from datetime import datetime
from pathlib import Path


def build_points_payload(current_file, feature_text, fit_mode_text, start_point, branch_points):
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source_file": current_file,
        "feature": feature_text,
        "fit_mode": fit_mode_text,
        "start_point": start_point,
        "points": branch_points,
    }


def save_points_payload(path, payload):
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_points_payload(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_report_lines(current_file, feature_text, fit_mode, branch_points, formatted_summary):
    return [
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"Data file: {current_file}",
        f"Feature: {feature_text}",
        f"Fit mode: {fit_mode}",
        f"Points: cavity={len(branch_points['cavity'])}, lp={len(branch_points['lp'])}, up={len(branch_points['up'])}",
        "",
        formatted_summary,
    ]


def write_fit_csv(path, mode, last_fit):
    with open(path, "w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        if mode == "coupled" and last_fit:
            writer.writerow(["branch", "k", "energy", "prediction", "residual"])
            for k_value, energy, pred in zip(last_fit["k_lp"], last_fit["e_lp"], last_fit["pred_lp"]):
                writer.writerow(["lp", k_value, energy, pred, pred - energy])
            for k_value, energy, pred in zip(last_fit["k_up"], last_fit["e_up"], last_fit["pred_up"]):
                writer.writerow(["up", k_value, energy, pred, pred - energy])
        elif last_fit:
            writer.writerow(["k", "energy", "prediction", "residual"])
            for k_value, energy, pred, residual in zip(
                last_fit["k"],
                last_fit["e"],
                last_fit["pred"],
                last_fit["residual"],
            ):
                writer.writerow([k_value, energy, pred, residual])
