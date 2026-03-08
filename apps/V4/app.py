
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QAbstractSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

import matplotlib
matplotlib.use("QtAgg")

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.widgets import RectangleSelector

from polariton_fitter import FitSummary, PolaritonFitter
from v4_export import build_points_payload, build_report_lines, load_points_payload, save_points_payload, write_fit_csv
from v4_plotting import draw_base_images, draw_fit_overlays, draw_heatmap, draw_raw_crop_preview, redraw_raw_crop_preview
from v4_session import build_session_panel_text, format_fit_summary, material_presets, parameter_tooltips, reset_session_panel_text
from v4_ui_sections import build_fit_group, build_load_group, build_process_group, build_result_group, build_trace_group


PANEL_STYLE = """
QMainWindow {
    background: #f3f5f8;
}
QGroupBox {
    font-weight: 700;
    border: 1px solid #d6dce5;
    border-radius: 10px;
    margin-top: 12px;
    padding-top: 12px;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #243446;
}
QPushButton {
    border: 1px solid #c4ceda;
    border-radius: 8px;
    background: #f7fafc;
    color: #1b2a3a;
    padding: 6px 10px;
    font-weight: 600;
}
QPushButton:hover {
    background: #edf3f8;
}
QPushButton:pressed {
    background: #e3edf6;
}
QTextEdit {
    background: #f9fbfd;
    border: 1px solid #d6dce5;
    border-radius: 8px;
}
QTabWidget::pane {
    border: 1px solid #d6dce5;
    border-radius: 8px;
    background: #ffffff;
    top: -1px;
}
QTabBar::tab {
    background: #e9eef4;
    border: 1px solid #d6dce5;
    border-bottom: none;
    padding: 7px 14px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 600;
    color: #344861;
}
QTabBar::tab:selected {
    background: #ffffff;
    color: #10233a;
}
"""


class ParamRow(QWidget):
    def __init__(self, key, label, guess, lower, upper, scientific=False, tooltip=None, parent=None):
        super().__init__(parent)
        self.key = key
        self.scientific = scientific

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(6)
        layout.setVerticalSpacing(2)

        label_widget = QLabel(label)
        label_widget.setTextFormat(Qt.TextFormat.RichText)
        if tooltip is not None:
            label_widget.setToolTip(tooltip)
        layout.addWidget(label_widget, 0, 0)

        self.guess = self._make_spinbox(guess, scientific)
        self.lower = self._make_spinbox(lower, scientific)
        self.upper = self._make_spinbox(upper, scientific)

        if tooltip is not None:
            self.guess.setToolTip(tooltip)
            self.lower.setToolTip(tooltip)
            self.upper.setToolTip(tooltip)

        layout.addWidget(QLabel("Guess"), 1, 0)
        layout.addWidget(self.guess, 1, 1)
        layout.addWidget(QLabel("Min"), 2, 0)
        layout.addWidget(self.lower, 2, 1)
        layout.addWidget(QLabel("Max"), 3, 0)
        layout.addWidget(self.upper, 3, 1)
        layout.setColumnStretch(1, 1)

    def _make_spinbox(self, value, scientific):
        box = QDoubleSpinBox()
        box.setRange(-1e9, 1e9)
        box.setDecimals(8 if scientific else 4)
        box.setSingleStep(1e-5 if scientific else 1.0)
        box.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        box.setMinimumWidth(72)
        box.setMaximumWidth(116)
        box.setValue(float(value))
        return box

    def get_values(self):
        return {
            f"{self.key}_p0": self.guess.value(),
            f"{self.key}_b_min": self.lower.value(),
            f"{self.key}_b_max": self.upper.value(),
        }


class PlotPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.workspace_tab = QWidget()
        workspace_layout = QVBoxLayout(self.workspace_tab)
        workspace_layout.setContentsMargins(8, 8, 8, 8)
        workspace_layout.setSpacing(6)
        self.figure = Figure(figsize=(9, 7), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.btn_export_workspace = QPushButton("Export Workspace Image")
        workspace_layout.addWidget(self.toolbar)
        workspace_layout.addWidget(self.canvas)
        workspace_layout.addWidget(self.btn_export_workspace)
        ((self.ax_raw, self.ax_pick), (self.ax_k, self.ax_residual)) = self.figure.subplots(2, 2)

        self.clean_tab = QWidget()
        clean_layout = QVBoxLayout(self.clean_tab)
        clean_layout.setContentsMargins(8, 8, 8, 8)
        clean_layout.setSpacing(6)
        self.clean_tabs = QTabWidget()
        self.clean_tabs.setDocumentMode(True)

        self.clean_crop_tab = QWidget()
        crop_layout = QVBoxLayout(self.clean_crop_tab)
        crop_layout.setContentsMargins(0, 0, 0, 0)
        crop_layout.setSpacing(6)
        self.clean_figure = Figure(figsize=(8, 4.8), dpi=100)
        self.clean_canvas = FigureCanvas(self.clean_figure)
        self.btn_export_clean = QPushButton("Export 2D Clean Image")
        self.clean_ax = self.clean_figure.subplots(1, 1)
        crop_layout.addWidget(self.clean_canvas)
        crop_layout.addWidget(self.btn_export_clean)

        self.clean_full_tab = QWidget()
        full_layout = QVBoxLayout(self.clean_full_tab)
        full_layout.setContentsMargins(0, 0, 0, 0)
        full_layout.setSpacing(6)
        self.full_clean_figure = Figure(figsize=(8, 4.8), dpi=100)
        self.full_clean_canvas = FigureCanvas(self.full_clean_figure)
        self.btn_export_full_clean = QPushButton("Export Full Range Image")
        self.full_clean_ax = self.full_clean_figure.subplots(1, 1)
        full_layout.addWidget(self.full_clean_canvas)
        full_layout.addWidget(self.btn_export_full_clean)

        self.clean_tabs.addTab(self.clean_crop_tab, "2D Clean")
        self.clean_tabs.addTab(self.clean_full_tab, "Full Range")
        clean_layout.addWidget(self.clean_tabs)

        self.log_tab = QWidget()
        self.log_layout = QVBoxLayout(self.log_tab)
        self.log_layout.setContentsMargins(8, 8, 8, 8)
        self.log_layout.setSpacing(6)

        self.tabs.addTab(self.workspace_tab, "Workspace")
        self.tabs.addTab(self.clean_tab, "Clean Output")
        self.tabs.addTab(self.log_tab, "Session Log")

        root.addWidget(self.tabs)
        self.reset_axes()

    def reset_axes(self):
        for ax in (self.ax_raw, self.ax_pick, self.ax_k, self.ax_residual, self.clean_ax, self.full_clean_ax):
            ax.cla()
        self.ax_raw.set_title("1. Raw / crop overview")
        self.ax_pick.set_title("2. Interactive trace")
        self.ax_k.set_title("3. k-space fit")
        self.ax_residual.set_title("4. Residuals")
        self.clean_ax.set_title("2D clean fit over cropped map")
        self.full_clean_ax.set_title("Full-range fitted branches")
        self.ax_raw.set_xlabel("Angle / deg")
        self.ax_pick.set_xlabel("Angle / deg")
        self.ax_k.set_xlabel("k / um^-1")
        self.ax_residual.set_xlabel("Point index")
        self.clean_ax.set_xlabel("Angle / deg")
        self.full_clean_ax.set_xlabel("Angle / deg")
        self.ax_raw.set_ylabel("Energy / meV")
        self.ax_pick.set_ylabel("Energy / meV")
        self.ax_k.set_ylabel("Energy / meV")
        self.ax_residual.set_ylabel("Residual / meV")
        self.clean_ax.set_ylabel("Energy / meV")
        self.full_clean_ax.set_ylabel("Energy / meV")
        self.figure.tight_layout()
        self.clean_figure.tight_layout()
        self.full_clean_figure.tight_layout()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Polariton Fitter V4")
        self.resize(1500, 960)
        self.setStyleSheet(PANEL_STYLE)

        self.fitter = PolaritonFitter()
        self.current_file = ""
        self.start_point = None
        self.branch_points = {"cavity": [], "lp": [], "up": []}
        self.branch_segments = {"cavity": [], "lp": [], "up": []}
        self.pending_segment = {"branch": None, "points": []}
        self.fit_curves = {}
        self.last_fit_mode = "coupled"
        self.param_rows = {}
        self.trace_edit_mode = ""
        self.deleted_points_history = []
        self.box_selector = None
        self.crop_drag_edge = None

        self._build_ui()
        self.rebuild_param_ui()
        self.sync_branch_controls()
        self._update_point_buttons()
        self._update_pending_segment_label()
        self._sync_objective_na()
        self.on_material_preset_changed()
        self.sync_trace_defaults()
        self._set_trace_edit_mode("")
        self._reset_session_panel()
        self._append_status("Ready.")

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMinimumWidth(260)

        controls = QWidget()
        self.left_layout = QVBoxLayout(controls)
        self.left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_layout.setSpacing(8)

        self.workflow_hint = QLabel(
            "Workflow: Load -> Apply -> Start -> Trace -> Fit -> Export"
        )
        self.workflow_hint.setWordWrap(True)
        self.workflow_hint.setStyleSheet(
            "padding: 6px 8px; border: 1px solid #d6dce5; border-radius: 8px; "
            "background: #eef4fb; color: #1e3650;"
        )
        self.left_layout.addWidget(self.workflow_hint)

        self.control_tabs = QTabWidget()
        self.control_tabs.setDocumentMode(True)

        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        data_layout.setContentsMargins(6, 6, 6, 6)
        data_layout.setSpacing(8)
        data_layout.addWidget(self._build_load_group())
        data_layout.addWidget(self._build_process_group())
        data_layout.addStretch(1)

        trace_tab = QWidget()
        trace_layout = QVBoxLayout(trace_tab)
        trace_layout.setContentsMargins(6, 6, 6, 6)
        trace_layout.setSpacing(8)
        trace_layout.addWidget(self._build_trace_group())
        trace_layout.addStretch(1)

        fit_tab = QWidget()
        fit_layout = QVBoxLayout(fit_tab)
        fit_layout.setContentsMargins(6, 6, 6, 6)
        fit_layout.setSpacing(8)
        fit_layout.addWidget(self._build_fit_group())
        fit_layout.addWidget(self._build_result_group())
        fit_layout.addStretch(1)

        self.control_tabs.addTab(data_tab, "Data")
        self.control_tabs.addTab(trace_tab, "Trace")
        self.control_tabs.addTab(fit_tab, "Fit")

        self.left_layout.addWidget(self.control_tabs)
        scroll.setWidget(controls)

        self.plot = PlotPanel(self)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("Session logs and fit summaries appear here.")
        self.plot.log_layout.addWidget(self.result_text)

        splitter.addWidget(scroll)
        splitter.addWidget(self.plot)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([340, 1100])

        self.plot.canvas.mpl_connect("button_press_event", self.on_canvas_click)
        self.plot.canvas.mpl_connect("motion_notify_event", self.on_canvas_motion)
        self.plot.canvas.mpl_connect("button_release_event", self.on_canvas_release)
        self.plot.btn_export_workspace.clicked.connect(self.export_workspace_image)
        self.plot.btn_export_clean.clicked.connect(self.export_clean_fit_image)
        self.plot.btn_export_full_clean.clicked.connect(self.export_full_clean_fit_image)
        self.box_selector = RectangleSelector(self.plot.ax_pick, self._delete_points_in_box, useblit=False, button=[1], minspanx=0.3, minspany=1.0, interactive=False)
        self.box_selector.set_active(False)

    def _build_load_group(self):
        return build_load_group(self)

    def _build_process_group(self):
        return build_process_group(self)

    def _build_trace_group(self):
        return build_trace_group(self)

    def _build_fit_group(self):
        return build_fit_group(self)

    def _build_result_group(self):
        return build_result_group(self)

    def _toggle_k0_enabled(self, checked):
        self.k0.setEnabled(not checked)

    def on_crop_mode_changed(self):
        if self.crop_drag_edge is not None:
            self._finish_crop_drag()
        self._sync_crop_controls()

    def _sync_crop_controls(self):
        manual = self._crop_mode_key() == "manual"
        self.left_boundary.setEnabled(manual)
        self.right_boundary.setEnabled(manual)
        self.crop_padding.setEnabled(not manual)

    def _apply_tooltip(self, label_widget, input_widget, tooltip):
        label_widget.setToolTip(tooltip)
        input_widget.setToolTip(tooltip)

    def _parameter_tooltip(self, key):
        return parameter_tooltips()[key]

    def on_objective_preset_changed(self):
        self._sync_objective_na()

    def _sync_objective_na(self):
        if not hasattr(self, "objective_preset"):
            return
        preset = self.objective_preset.currentText()
        if preset == "Nikon 100x (NA=0.9)":
            self.na.setValue(0.90)
            self.na.setEnabled(False)
        elif preset == "Mitutoyo 100x (NA=0.7)":
            self.na.setValue(0.70)
            self.na.setEnabled(False)
        else:
            self.na.setEnabled(True)

    def _material_presets(self):
        return material_presets()

    def on_material_preset_changed(self):
        if not hasattr(self, "material_preset"):
            return
        preset = self.material_preset.currentText()
        if preset == "Keep current values":
            return
        values = self._material_presets().get(preset, {})
        if "eex" in self.param_rows and values.get("Eex") is not None:
            self.param_rows["eex"].guess.setValue(float(values["Eex"]))
        if "g" in self.param_rows and values.get("g") is not None:
            self.param_rows["g"].guess.setValue(float(values["g"]))

    def on_edit_trace_toggled(self, checked):
        if checked and not self.trace_edit_mode:
            self._set_trace_edit_mode("pick")
            return
        if not checked:
            self._set_trace_edit_mode("")
            return
        self._set_trace_edit_mode(self.trace_edit_mode)

    def _set_trace_edit_mode(self, mode):
        if not hasattr(self, "edit_trace"):
            return
        if not self.edit_trace.isChecked():
            self.trace_edit_mode = ""
        else:
            self.trace_edit_mode = mode or "pick"
        if self.box_selector is not None:
            self.box_selector.set_active(self.trace_edit_mode == "box" and self.edit_trace.isChecked())
        if hasattr(self, "btn_pick_delete"):
            self.btn_pick_delete.setEnabled(self.edit_trace.isChecked())
        if hasattr(self, "btn_box_delete"):
            self.btn_box_delete.setEnabled(self.edit_trace.isChecked())
        if hasattr(self, "btn_undo_delete"):
            self.btn_undo_delete.setEnabled(bool(self.deleted_points_history))

    def _remove_nearest_point(self, click_angle, click_energy):
        branch = self._active_branch()
        points = list(self._merged_branch_points(branch))
        if not points:
            return False
        x_span = max(float(self.fitter.angle_deg.max() - self.fitter.angle_deg.min()), 1.0) if self.fitter.angle_deg is not None and self.fitter.angle_deg.size else 1.0
        y_span = max(float(self.fitter.energy_mev.max() - self.fitter.energy_mev.min()), 1.0) if self.fitter.energy_mev is not None and self.fitter.energy_mev.size else 1.0
        scores = [((angle - click_angle) / x_span) ** 2 + ((energy - click_energy) / y_span) ** 2 for angle, energy in points]
        index = int(np.argmin(scores))
        if scores[index] > 0.01:
            return False
        removed = [points.pop(index)]
        self._set_branch_points(branch, points)
        self.deleted_points_history.append((branch, removed))
        self._clear_fit_result()
        self._reset_session_panel()
        self._refresh_point_views()
        self._append_status(f"Removed 1 point from {branch}.")
        return True

    def _delete_points_in_box(self, eclick, erelease):
        if not self.edit_trace.isChecked() or self.trace_edit_mode != "box":
            return
        if eclick.xdata is None or eclick.ydata is None or erelease.xdata is None or erelease.ydata is None:
            return
        branch = self._active_branch()
        points = list(self._merged_branch_points(branch))
        if not points:
            return
        x0, x1 = sorted((float(eclick.xdata), float(erelease.xdata)))
        y0, y1 = sorted((float(eclick.ydata), float(erelease.ydata)))
        kept = []
        removed = []
        for point in points:
            if x0 <= point[0] <= x1 and y0 <= point[1] <= y1:
                removed.append(point)
            else:
                kept.append(point)
        if not removed:
            return
        self._set_branch_points(branch, kept)
        self.deleted_points_history.append((branch, removed))
        self._clear_fit_result()
        self._reset_session_panel()
        self._refresh_point_views()
        self._append_status(f"Removed {len(removed)} points from {branch}.")

    def undo_last_delete(self):
        if not self.deleted_points_history:
            return
        branch, removed = self.deleted_points_history.pop()
        points = list(self._merged_branch_points(branch))
        points.extend(removed)
        points = sorted(points, key=lambda item: item[0])
        self._set_branch_points(branch, points)
        self._clear_fit_result()
        self._reset_session_panel()
        self._refresh_point_views()
        self._append_status(f"Restored {len(removed)} points to {branch}.")
        self._set_trace_edit_mode(self.trace_edit_mode)

    def _clear_fit_result(self):
        self.fit_curves = {}
        self.last_fit_mode = self._fit_mode_key() if hasattr(self, "mode") else "coupled"
        self.fitter.fit_params = {}
        self.fitter.last_fit = {}
        self.fitter.fit_summary = FitSummary(mode="", success=False, text="")
        if hasattr(self, "btn_undo_delete"):
            self.btn_undo_delete.setEnabled(bool(self.deleted_points_history))

    def _reset_session_panel(self):
        state = reset_session_panel_text()
        self.session_headline.setText(state['headline'])
        self.session_metrics.setText(state['metrics'])
        self.session_params.setText(state['params'])
        self.session_export.setText(state['export'])

    def _set_export_status(self, text):
        self.session_export.setText(f"Export: {text}")

    def _update_session_panel(self):
        mode_text = self.mode.currentText() if hasattr(self, 'mode') else '--'
        state = build_session_panel_text(self.fitter, {branch: self._merged_branch_points(branch) for branch in ("cavity", "lp", "up")}, mode_text, self.session_export.text())
        self.session_headline.setText(state['headline'])
        self.session_metrics.setText(state['metrics'])
        self.session_params.setText(state['params'])
        self.session_export.setText(state['export'])

    def _crop_mode_key(self):
        return "manual" if self.crop_mode.currentText() == "Manual" else "auto"

    def _fit_mode_key(self):
        text = self.mode.currentText()
        if text == "LP only":
            return "lp"
        if text == "Cavity only":
            return "ca"
        return "coupled"

    def _feature_key(self):
        return "peak" if self.feature.currentText() == "PL peak" else "dip"

    def sync_trace_defaults(self, checked=False):
        if not hasattr(self, "search_px"):
            return
        if self.rb_lp.isChecked():
            self.search_px.setValue(40)
            return
        self.search_px.setValue(80)

    def _active_branch(self):
        if self.rb_cavity.isChecked():
            return "cavity"
        if self.rb_up.isChecked():
            return "up"
        return "lp"

    def _merged_branch_points(self, branch):
        points = []
        for segment in self.branch_segments.get(branch, []):
            points.extend(segment)
        unique_points = sorted({(float(angle), float(energy)) for angle, energy in points}, key=lambda item: item[0])
        return unique_points

    def _refresh_branch_points_cache(self):
        for branch in ("cavity", "lp", "up"):
            self.branch_points[branch] = self._merged_branch_points(branch)

    def _set_branch_points(self, branch, points):
        cleaned = sorted({(float(angle), float(energy)) for angle, energy in points}, key=lambda item: item[0])
        self.branch_segments[branch] = [cleaned] if cleaned else []
        self._refresh_branch_points_cache()

    def _all_branch_points(self):
        return {branch: self._merged_branch_points(branch) for branch in ("cavity", "lp", "up")}

    def _replace_branch_with_points(self, branch, points):
        cleaned = [tuple(item) for item in points]
        self.branch_segments[branch] = [cleaned] if cleaned else []
        self._refresh_branch_points_cache()

    def on_fit_mode_changed(self):
        self.sync_branch_controls()
        self.rebuild_param_ui()
        self.on_material_preset_changed()
        self._clear_fit_result()
        self._refresh_point_views()
        self._reset_session_panel()

    def sync_branch_controls(self):
        mode = self._fit_mode_key()
        allow_cavity = mode == "ca"
        allow_lp = mode in ("lp", "coupled")
        allow_up = mode == "coupled"

        self.rb_cavity.setVisible(allow_cavity)
        self.rb_lp.setVisible(allow_lp)
        self.rb_up.setVisible(allow_up)
        self.btn_clear_cavity.setVisible(allow_cavity)
        self.btn_clear_lp.setVisible(allow_lp)
        self.btn_clear_up.setVisible(allow_up)

        if not allow_cavity:
            self.clear_branch("cavity")
        if not allow_lp:
            self.clear_branch("lp")
        if not allow_up:
            self.clear_branch("up")

        if allow_cavity:
            self.rb_cavity.setChecked(True)
        elif allow_lp:
            self.rb_lp.setChecked(True)
        elif allow_up:
            self.rb_up.setChecked(True)

    def rebuild_param_ui(self):
        while self.param_layout.count():
            item = self.param_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.param_rows = {}

        energy_mid = 2000.0
        if self.fitter.energy_mev is not None and self.fitter.energy_mev.size:
            energy_mid = float(np.median(self.fitter.energy_mev))

        mode = self._fit_mode_key()
        if mode == "ca":
            specs = [
                ("ca_mr", "m<sub>r</sub> / m<sub>0</sub>", 7e-5, 1e-7, 1e-2, True, self._parameter_tooltip("mr")),
                ("ca_e0", "E<sub>0</sub>", energy_mid, energy_mid - 500.0, energy_mid + 500.0, False, self._parameter_tooltip("e0")),
            ]
        else:
            specs = [
                ("mr", "m<sub>r</sub> / m<sub>0</sub>", 7e-5, 1e-7, 1e-2, True, self._parameter_tooltip("mr")),
                ("e0", "E<sub>0</sub>", energy_mid, energy_mid - 500.0, energy_mid + 500.0, False, self._parameter_tooltip("e0")),
                ("kshift", "k<sub>shift</sub>", 0.0, -10.0, 10.0, False, self._parameter_tooltip("kshift")),
                ("g", "g", 120.0, 1.0, 500.0, False, self._parameter_tooltip("g")),
                ("eex", "E<sub>ex</sub>", energy_mid + 50.0, energy_mid - 500.0, energy_mid + 500.0, False, self._parameter_tooltip("eex")),
            ]

        for key, label, guess, lower, upper, scientific, tooltip in specs:
            row = ParamRow(key, label, guess, lower, upper, scientific=scientific, tooltip=tooltip)
            self.param_rows[key] = row
            self.param_layout.addWidget(row)
        self.param_layout.addStretch(1)

    def _config_values(self):
        values = {}
        for row in self.param_rows.values():
            values.update(row.get_values())
        return values
    def load_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load data", "", "Text data (*.txt *.dat *.csv);;All files (*)")
        if not path:
            return
        ok, message = self.fitter.load_data(path)
        if not ok:
            self._append_status(message)
            return
        self.current_file = path
        self.file_label.setText(path)
        self._append_status(message)
        self.apply_processing()

    def apply_processing(self):
        if self.fitter.full_intensity_matrix is None:
            return
        self.fitter.apply_processing(
            smoothing_sigma=self.smoothing.value(),
            na=self.na.value(),
            auto_k0=self.auto_k0.isChecked(),
            k0_index=self.k0.value(),
            crop_padding=self.crop_padding.value(),
            crop_mode=self._crop_mode_key(),
            left_bound=self.left_boundary.value(),
            right_bound=self.right_boundary.value(),
        )
        self.left_boundary.setValue(self.fitter.crop_min_index)
        self.right_boundary.setValue(self.fitter.crop_max_index)
        self.start_point = None
        self.branch_segments = {"cavity": [], "lp": [], "up": []}
        self.pending_segment = {"branch": None, "points": []}
        for key in ("cavity", "lp", "up"):
            self.branch_points[key] = []
        self._clear_fit_result()
        self.plot.reset_axes()
        self._draw_base_images()
        self._refresh_point_views()
        self._reset_session_panel()
        self._append_status("Processing applied.")

    def _draw_base_images(self):
        draw_base_images(self.plot, self.fitter, preview_bounds=self._preview_crop_bounds())

    def _draw_heatmap(self, ax, x, y, z):
        draw_heatmap(ax, x, y, z)

    def _toolbar_mode_active(self):
        if not hasattr(self.plot, "toolbar"):
            return False
        mode = getattr(self.plot.toolbar, "mode", "")
        if not mode:
            return False
        return getattr(mode, "name", str(mode)) != "NONE"

    def _preview_crop_bounds(self):
        if self.fitter.full_angle_deg is None or not self.fitter.full_angle_deg.size:
            return None
        last_index = int(self.fitter.full_angle_deg.size - 1)
        left_index = int(np.clip(self.left_boundary.value(), 0, last_index))
        right_index = int(np.clip(self.right_boundary.value(), 0, last_index))
        if left_index >= right_index:
            if left_index >= last_index:
                left_index = max(0, last_index - 1)
                right_index = last_index
            else:
                right_index = min(last_index, left_index + 1)
        return left_index, right_index

    def _draw_raw_crop_preview(self):
        draw_raw_crop_preview(
            self.plot.ax_raw,
            self.fitter.full_angle_deg,
            self.fitter.crop_min_index,
            self.fitter.crop_max_index,
            preview_bounds=self._preview_crop_bounds(),
        )

    def _refresh_raw_crop_preview(self):
        redraw_raw_crop_preview(self.plot, self.fitter, preview_bounds=self._preview_crop_bounds())

    def _nearest_crop_edge(self, angle_value):
        bounds = self._preview_crop_bounds()
        if bounds is None:
            return ""
        left_index, right_index = bounds
        left_angle = float(self.fitter.full_angle_deg[left_index])
        right_angle = float(self.fitter.full_angle_deg[right_index])
        span = float(np.max(self.fitter.full_angle_deg) - np.min(self.fitter.full_angle_deg))
        threshold = max(span * 0.02, 0.5)
        left_distance = abs(float(angle_value) - left_angle)
        right_distance = abs(float(angle_value) - right_angle)
        nearest = "left" if left_distance <= right_distance else "right"
        best_distance = min(left_distance, right_distance)
        if best_distance > threshold:
            return ""
        return nearest

    def _start_crop_drag(self, event):
        if event.xdata is None or self._toolbar_mode_active():
            return False
        edge = self._nearest_crop_edge(event.xdata)
        if not edge:
            return False
        self.crop_drag_edge = edge
        self._update_crop_drag(event)
        return True

    def _update_crop_drag(self, event):
        if self.crop_drag_edge is None or event.xdata is None:
            return
        if event.inaxes != self.plot.ax_raw or self.fitter.full_angle_deg is None or not self.fitter.full_angle_deg.size:
            return
        index = int(np.argmin(np.abs(self.fitter.full_angle_deg - float(event.xdata))))
        bounds = self._preview_crop_bounds()
        if bounds is None:
            return
        left_index, right_index = bounds
        last_index = int(self.fitter.full_angle_deg.size - 1)
        if self.crop_drag_edge == "left":
            new_left = int(np.clip(index, 0, max(0, right_index - 1)))
            self.left_boundary.setValue(new_left)
        else:
            new_right = int(np.clip(index, min(last_index, left_index + 1), last_index))
            self.right_boundary.setValue(new_right)
        self._refresh_raw_crop_preview()

    def _finish_crop_drag(self):
        self.crop_drag_edge = None

    def on_canvas_motion(self, event):
        self._update_crop_drag(event)

    def on_canvas_release(self, event):
        self._finish_crop_drag()

    def on_canvas_click(self, event):
        if self._toolbar_mode_active():
            return
        if event.inaxes == self.plot.ax_raw and self._crop_mode_key() == "manual":
            if self._start_crop_drag(event):
                return
        if event.inaxes != self.plot.ax_pick:
            return
        if event.xdata is None or event.ydata is None:
            return
        if self.edit_trace.isChecked() and self.trace_edit_mode == "pick":
            self._remove_nearest_point(float(event.xdata), float(event.ydata))
            return
        if self.edit_trace.isChecked() and self.trace_edit_mode == "box":
            return
        self.start_point = (float(event.xdata), float(event.ydata))
        branch = self._active_branch()
        self._append_status(f"Start point for {branch}: angle={event.xdata:.2f}, energy={event.ydata:.2f}")
        self._refresh_point_views()

    def trace_new_segment(self):
        if self.start_point is None:
            self._append_status("Set a start point first.")
            return
        if self.fitter.intensity_matrix is None:
            self._append_status("Load and process data first.")
            return
        branch = self._active_branch()
        points = self.fitter.trace_branch(
            self.start_point[0],
            self.start_point[1],
            feature=self._feature_key(),
            search_px=self.search_px.value(),
            min_prominence=self.min_prominence.value(),
            max_misses=self.max_misses.value(),
        )
        self.pending_segment = {"branch": branch, "points": list(points)}
        self._clear_fit_result()
        self._reset_session_panel()
        self._append_status(f"Traced {len(points)} points for pending {branch} segment.")
        self._refresh_point_views()

    def add_pending_segment_to_branch(self):
        points = list(self.pending_segment["points"])
        if not points:
            self._append_status("Trace a segment first.")
            return
        branch = self.pending_segment["branch"] or self._active_branch()
        self.branch_segments.setdefault(branch, []).append(points)
        self._refresh_branch_points_cache()
        committed = len(points)
        self.pending_segment = {"branch": None, "points": []}
        self._clear_fit_result()
        self._reset_session_panel()
        self._append_status(f"Added {committed} points to {branch}.")
        self._refresh_point_views()

    def trace_active_branch(self):
        self.trace_new_segment()

    def clear_branch(self, branch):
        if branch in self.branch_points:
            self.branch_points[branch] = []
        if branch in self.branch_segments:
            self.branch_segments[branch] = []
        if self.pending_segment["branch"] == branch:
            self.pending_segment = {"branch": None, "points": []}
        if self._active_branch() == branch:
            self.start_point = None
        self._clear_fit_result()
        self._reset_session_panel()
        self._refresh_point_views()

    def _refresh_point_views(self):
        self._draw_base_images()

        if self.start_point is not None:
            self.plot.ax_pick.plot(self.start_point[0], self.start_point[1], marker="o", color="#00a36c", markersize=7)

        styles = {
            "cavity": {"marker": "o", "color": "#ff8c00", "label": "Cavity points"},
            "lp": {"marker": "+", "color": "#cc0000", "label": "LP points"},
            "up": {"marker": "x", "color": "#0066cc", "label": "UP points"},
        }
        for key in ("cavity", "lp", "up"):
            points = list(self._merged_branch_points(key))
            if not points:
                continue
            angle, energy = zip(*points)
            style = styles[key]
            self.plot.ax_pick.plot(angle, energy, linestyle="None", marker=style["marker"], color=style["color"], label=style["label"], markersize=7)

        if any(self._merged_branch_points(branch) for branch in ("cavity", "lp", "up")):
            self.plot.ax_pick.legend(loc="upper right", fontsize="small")

        pending_points = self.pending_segment["points"]
        if pending_points:
            pending_angle, pending_energy = zip(*pending_points)
            self.plot.ax_pick.plot(pending_angle, pending_energy, linestyle="--", marker=".", color="#6aa9ff", label="Pending segment", alpha=0.9)
            self.plot.ax_pick.legend(loc="upper right", fontsize="small")

        self._draw_fit_overlays()
        self._update_point_buttons()
        self._update_pending_segment_label()
        self._update_session_panel()
        self.plot.canvas.draw_idle()
        self.plot.clean_canvas.draw_idle()

    def _update_point_buttons(self):
        self.counts.setText(
            f"Cavity: {len(self._merged_branch_points('cavity'))} | LP: {len(self._merged_branch_points('lp'))} | UP: {len(self._merged_branch_points('up'))}"
        )

    def _draw_fit_overlays(self):
        draw_fit_overlays(self.plot, self.fitter, self.fit_curves)

    def _update_pending_segment_label(self):
        if not hasattr(self, "pending_segment_status"):
            return
        pending_points = self.pending_segment["points"]
        if not pending_points:
            self.pending_segment_status.setText("No pending segment.")
            return
        branch = self.pending_segment["branch"] or self._active_branch()
        self.pending_segment_status.setText(f"{branch.upper()} pending segment: {len(pending_points)} point(s).")

    def _discard_pending_segment(self):
        branch = self.pending_segment["branch"] or self._active_branch()
        count = len(self.pending_segment["points"])
        self.pending_segment = {"branch": None, "points": []}
        self._clear_fit_result()
        self._reset_session_panel()
        self._append_status(f"Discarded pending {branch} segment ({count} point(s)).")
        self._refresh_point_views()

    def _resolve_pending_segment(self, action_label):
        pending_points = list(self.pending_segment["points"])
        if not pending_points:
            return True
        branch = self.pending_segment["branch"] or self._active_branch()
        message = QMessageBox(self)
        message.setWindowTitle("Pending Segment")
        message.setIcon(QMessageBox.Icon.Warning)
        message.setText(f"A pending {branch.upper()} segment has not been added to the branch.")
        message.setInformativeText(f"Choose how to resolve it before {action_label}.")
        add_button = message.addButton("Add Segment", QMessageBox.ButtonRole.AcceptRole)
        discard_button = message.addButton("Discard Pending", QMessageBox.ButtonRole.DestructiveRole)
        message.addButton(QMessageBox.StandardButton.Cancel)
        message.setDefaultButton(QMessageBox.StandardButton.Cancel)
        message.exec()
        clicked = message.clickedButton()
        if clicked is add_button:
            self.add_pending_segment_to_branch()
            return True
        if clicked is discard_button:
            self._discard_pending_segment()
            return True
        return False

    def run_fit(self):
        if not self._resolve_pending_segment("run fit"):
            return
        if self.fitter.intensity_matrix is None:
            self._append_status("Load and process data first.")
            return
        data_pack = self.fitter.prepare_data_pack(
            self._merged_branch_points("cavity"),
            self._merged_branch_points("lp"),
            self._merged_branch_points("up"),
        )
        mode = self._fit_mode_key()
        ok = self.fitter.fit_data(mode, data_pack, self._config_values())
        self.last_fit_mode = mode
        self.fit_curves = self.fitter.generate_curves()
        if not ok:
            self.fit_curves = {}
        summary_text = self._formatted_summary()
        self.result_text.append("=== Fit Summary ===")
        self.result_text.append(summary_text)
        self._update_session_panel()
        self._refresh_point_views()

    def _formatted_summary(self):
        return format_fit_summary(self.fitter.fit_summary.text or 'No fit result', self.fitter.fit_params)

    def save_points_json(self):
        if not self._resolve_pending_segment("save points"):
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Save points', 'points.json', 'JSON (*.json)')
        if not path:
            return
        payload = build_points_payload(self.current_file, self.feature.currentText(), self.mode.currentText(), self.start_point, self._all_branch_points())
        save_points_payload(path, payload)
        self._append_status(f'Saved points: {path}')

    def load_points_json(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Load points', '', 'JSON (*.json)')
        if not path:
            return
        payload = load_points_payload(path)
        self.feature.setCurrentText(payload.get('feature', self.feature.currentText()))
        self.mode.setCurrentText(payload.get('fit_mode', self.mode.currentText()))
        points = payload.get('points', {})
        self.branch_segments = {"cavity": [], "lp": [], "up": []}
        self.pending_segment = {"branch": None, "points": []}
        for key in ('cavity', 'lp', 'up'):
            self._replace_branch_with_points(key, points.get(key, []))
        start_point = payload.get('start_point')
        self.start_point = tuple(start_point) if start_point else None
        self._clear_fit_result()
        self._reset_session_panel()
        self._append_status(f'Loaded points: {path}')
        self._refresh_point_views()

    def export_report_txt(self):
        if not self._resolve_pending_segment("export report"):
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Export report', 'fit_report.txt', 'Text (*.txt)')
        if not path:
            return
        lines = build_report_lines(self.current_file, self.feature.currentText(), self.last_fit_mode, self._all_branch_points(), self._formatted_summary())
        Path(path).write_text('\n'.join(lines), encoding='utf-8')
        self._set_export_status(f'Report TXT: {path}')
        self._append_status(f'Exported report: {path}')

    def export_fit_csv(self):
        if not self._resolve_pending_segment("export fit data"):
            return
        path, _ = QFileDialog.getSaveFileName(self, 'Export fit data', 'fit_data.csv', 'CSV (*.csv)')
        if not path:
            return
        write_fit_csv(path, self.last_fit_mode, self.fitter.last_fit)
        self._set_export_status(f'Fit CSV: {path}')
        self._append_status(f'Exported CSV: {path}')

    def export_workspace_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export workspace image", "workspace.png", "PNG (*.png);;PDF (*.pdf)")
        if not path:
            return
        self.plot.figure.savefig(path, dpi=300, bbox_inches="tight")
        self._set_export_status(f"Workspace image: {path}")
        self._append_status(f"Exported workspace image: {path}")

    def export_clean_fit_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export 2D clean image", "clean_2d.png", "PNG (*.png);;PDF (*.pdf)")
        if not path:
            return
        self.plot.clean_figure.savefig(path, dpi=300, bbox_inches="tight")
        self._set_export_status(f"2D clean image: {path}")
        self._append_status(f"Exported 2D clean image: {path}")

    def export_full_clean_fit_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export full-range image", "clean_full_range.png", "PNG (*.png);;PDF (*.pdf)")
        if not path:
            return
        self.plot.full_clean_figure.savefig(path, dpi=300, bbox_inches="tight")
        self._set_export_status(f"Full-range image: {path}")
        self._append_status(f"Exported full-range image: {path}")

    def _append_status(self, text):
        self.result_text.append(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())





























