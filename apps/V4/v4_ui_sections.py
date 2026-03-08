from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)


def build_load_group(window):
    group = QGroupBox("1. Load Data")
    layout = QVBoxLayout(group)

    window.btn_load = QPushButton("Load Data")
    window.btn_load.clicked.connect(window.load_data)
    layout.addWidget(window.btn_load)

    window.file_label = QLabel("No file loaded")
    window.file_label.setWordWrap(True)
    layout.addWidget(window.file_label)
    return group


def build_process_group(window):
    group = QGroupBox("2. Pre-process")
    layout = QGridLayout(group)

    smoothing_label = QLabel("Smoothing")
    window.smoothing = QSpinBox()
    window.smoothing.setRange(0, 50)
    window.smoothing.setValue(15)
    window._apply_tooltip(smoothing_label, window.smoothing, window._parameter_tooltip("smoothing"))
    layout.addWidget(smoothing_label, 0, 0)
    layout.addWidget(window.smoothing, 0, 1)

    crop_mode_label = QLabel("Crop mode")
    window.crop_mode = QComboBox()
    window.crop_mode.addItems(["Auto", "Manual"])
    window.crop_mode.currentIndexChanged.connect(window.on_crop_mode_changed)
    window._apply_tooltip(crop_mode_label, window.crop_mode, window._parameter_tooltip("crop_mode"))
    layout.addWidget(crop_mode_label, 1, 0)
    layout.addWidget(window.crop_mode, 1, 1)

    crop_padding_label = QLabel("Crop pad")
    window.crop_padding = QSpinBox()
    window.crop_padding.setRange(0, 50)
    window.crop_padding.setValue(0)
    window._apply_tooltip(crop_padding_label, window.crop_padding, window._parameter_tooltip("crop_padding"))
    layout.addWidget(crop_padding_label, 2, 0)
    layout.addWidget(window.crop_padding, 2, 1)

    left_boundary_label = QLabel("Left boundary")
    window.left_boundary = QSpinBox()
    window.left_boundary.setRange(0, 99999)
    window._apply_tooltip(left_boundary_label, window.left_boundary, window._parameter_tooltip("left_boundary"))
    layout.addWidget(left_boundary_label, 3, 0)
    layout.addWidget(window.left_boundary, 3, 1)

    right_boundary_label = QLabel("Right boundary")
    window.right_boundary = QSpinBox()
    window.right_boundary.setRange(0, 99999)
    window._apply_tooltip(right_boundary_label, window.right_boundary, window._parameter_tooltip("right_boundary"))
    layout.addWidget(right_boundary_label, 4, 0)
    layout.addWidget(window.right_boundary, 4, 1)

    objective_label = QLabel("Objective")
    window.objective_preset = QComboBox()
    window.objective_preset.addItems(["Nikon 100x (NA=0.9)", "Mitutoyo 100x (NA=0.7)", "Others"])
    window.objective_preset.currentIndexChanged.connect(window.on_objective_preset_changed)
    layout.addWidget(objective_label, 5, 0)
    layout.addWidget(window.objective_preset, 5, 1)

    na_label = QLabel("NA")
    window.na = QDoubleSpinBox()
    window.na.setRange(0.05, 1.50)
    window.na.setDecimals(3)
    window.na.setSingleStep(0.01)
    window.na.setValue(0.90)
    window._apply_tooltip(na_label, window.na, window._parameter_tooltip("na"))
    layout.addWidget(na_label, 6, 0)
    layout.addWidget(window.na, 6, 1)

    window.auto_k0 = QCheckBox("Auto k=0")
    window.auto_k0.setChecked(True)
    window.auto_k0.toggled.connect(window._toggle_k0_enabled)
    layout.addWidget(window.auto_k0, 7, 0, 1, 2)

    k0_label = QLabel("k0 idx")
    window.k0 = QSpinBox()
    window.k0.setRange(0, 99999)
    window.k0.setEnabled(False)
    window._apply_tooltip(k0_label, window.k0, window._parameter_tooltip("k0"))
    layout.addWidget(k0_label, 8, 0)
    layout.addWidget(window.k0, 8, 1)

    feature_label = QLabel("Feature")
    window.feature = QComboBox()
    window.feature.addItems(["Reflectivity dip", "PL peak"])
    window._apply_tooltip(feature_label, window.feature, window._parameter_tooltip("feature"))
    layout.addWidget(feature_label, 9, 0)
    layout.addWidget(window.feature, 9, 1)

    mode_label = QLabel("Fit mode")
    window.mode = QComboBox()
    window.mode.addItems(["Coupled (LP+UP)", "LP only", "Cavity only"])
    window.mode.currentIndexChanged.connect(window.on_fit_mode_changed)
    window._apply_tooltip(mode_label, window.mode, window._parameter_tooltip("fit_mode"))
    layout.addWidget(mode_label, 10, 0)
    layout.addWidget(window.mode, 10, 1)

    window.btn_apply = QPushButton("Apply")
    window.btn_apply.clicked.connect(window.apply_processing)
    layout.addWidget(window.btn_apply, 11, 0, 1, 2)
    return group


def build_trace_group(window):
    group = QGroupBox("3. Start Point and Trace")
    layout = QVBoxLayout(group)

    window.trace_hint = QLabel("Left click section 2 to set a start point. Trace New Segment creates a pending segment until you add it to the branch.")
    window.trace_hint.setWordWrap(True)
    layout.addWidget(window.trace_hint)

    branch_layout = QHBoxLayout()
    window.rb_cavity = QRadioButton("Cavity")
    window.rb_lp = QRadioButton("LP")
    window.rb_up = QRadioButton("UP")
    window.rb_lp.setChecked(True)
    window.branch_group = QButtonGroup(window)
    window.branch_group.addButton(window.rb_cavity)
    window.branch_group.addButton(window.rb_lp)
    window.branch_group.addButton(window.rb_up)
    window.rb_cavity.toggled.connect(window.sync_trace_defaults)
    window.rb_lp.toggled.connect(window.sync_trace_defaults)
    window.rb_up.toggled.connect(window.sync_trace_defaults)
    branch_layout.addWidget(window.rb_cavity)
    branch_layout.addWidget(window.rb_lp)
    branch_layout.addWidget(window.rb_up)
    layout.addLayout(branch_layout)

    search_row = QGridLayout()
    search_label = QLabel("Search px")
    window.search_px = QSpinBox()
    window.search_px.setRange(2, 80)
    window.search_px.setValue(40)
    window._apply_tooltip(search_label, window.search_px, window._parameter_tooltip("search_px"))
    search_row.addWidget(search_label, 0, 0)
    search_row.addWidget(window.search_px, 0, 1)

    prominence_label = QLabel("Prom.")
    window.min_prominence = QDoubleSpinBox()
    window.min_prominence.setRange(0.0, 1e6)
    window.min_prominence.setDecimals(2)
    window.min_prominence.setValue(200.0)
    window._apply_tooltip(prominence_label, window.min_prominence, window._parameter_tooltip("prominence"))
    search_row.addWidget(prominence_label, 1, 0)
    search_row.addWidget(window.min_prominence, 1, 1)

    max_miss_label = QLabel("Max miss")
    window.max_misses = QSpinBox()
    window.max_misses.setRange(1, 30)
    window.max_misses.setValue(4)
    window._apply_tooltip(max_miss_label, window.max_misses, window._parameter_tooltip("max_miss"))
    search_row.addWidget(max_miss_label, 2, 0)
    search_row.addWidget(window.max_misses, 2, 1)
    layout.addLayout(search_row)

    window.btn_trace = QPushButton("Trace New Segment")
    window.btn_trace.clicked.connect(window.trace_new_segment)
    layout.addWidget(window.btn_trace)

    window.btn_add_segment = QPushButton("Add Segment To Branch")
    window.btn_add_segment.clicked.connect(window.add_pending_segment_to_branch)
    layout.addWidget(window.btn_add_segment)

    window.pending_segment_status = QLabel("No pending segment.")
    window.pending_segment_status.setWordWrap(True)
    layout.addWidget(window.pending_segment_status)

    edit_layout = QHBoxLayout()
    window.edit_trace = QCheckBox("Edit Branch")
    window.edit_trace.toggled.connect(window.on_edit_trace_toggled)
    window.btn_pick_delete = QPushButton("Pick Delete")
    window.btn_pick_delete.clicked.connect(lambda: window._set_trace_edit_mode("pick"))
    window.btn_box_delete = QPushButton("Box Delete")
    window.btn_box_delete.clicked.connect(lambda: window._set_trace_edit_mode("box"))
    window.btn_undo_delete = QPushButton("Undo Last Delete")
    window.btn_undo_delete.clicked.connect(window.undo_last_delete)
    edit_layout.addWidget(window.edit_trace)
    edit_layout.addWidget(window.btn_pick_delete)
    edit_layout.addWidget(window.btn_box_delete)
    layout.addLayout(edit_layout)
    layout.addWidget(window.btn_undo_delete)

    clear_layout = QHBoxLayout()
    window.btn_clear_cavity = QPushButton("Clear Cavity")
    window.btn_clear_lp = QPushButton("Clear LP")
    window.btn_clear_up = QPushButton("Clear UP")
    window.btn_clear_cavity.clicked.connect(lambda: window.clear_branch("cavity"))
    window.btn_clear_lp.clicked.connect(lambda: window.clear_branch("lp"))
    window.btn_clear_up.clicked.connect(lambda: window.clear_branch("up"))
    clear_layout.addWidget(window.btn_clear_cavity)
    clear_layout.addWidget(window.btn_clear_lp)
    clear_layout.addWidget(window.btn_clear_up)
    layout.addLayout(clear_layout)

    window.counts = QLabel("")
    layout.addWidget(window.counts)

    save_layout = QHBoxLayout()
    window.btn_save_points = QPushButton("Save Points")
    window.btn_load_points = QPushButton("Load Points")
    window.btn_save_points.clicked.connect(window.save_points_json)
    window.btn_load_points.clicked.connect(window.load_points_json)
    save_layout.addWidget(window.btn_save_points)
    save_layout.addWidget(window.btn_load_points)
    layout.addLayout(save_layout)
    return group


def build_fit_group(window):
    group = QGroupBox("4. Fit")
    layout = QVBoxLayout(group)

    material_label = QLabel("Material Preset")
    window.material_preset = QComboBox()
    window.material_preset.addItems(["Generic", "Perovskite / CsPbBr3", "Perovskite / FAPbBr3 (seed)", "TMD / WSe2 monolayer", "Magnetic / CrSBr", "Keep current values"])
    window.material_preset.currentIndexChanged.connect(window.on_material_preset_changed)
    layout.addWidget(material_label)
    layout.addWidget(window.material_preset)

    window.param_container = QGroupBox()
    window.param_container.setFlat(True)
    window.param_container.setStyleSheet("QGroupBox { border: none; margin-top: 0; padding-top: 0; }")
    window.param_layout = QVBoxLayout(window.param_container)
    window.param_layout.setContentsMargins(0, 0, 0, 0)
    window.param_layout.setSpacing(4)
    layout.addWidget(window.param_container)

    window.btn_fit = QPushButton("Run Fit")
    window.btn_fit.clicked.connect(window.run_fit)
    layout.addWidget(window.btn_fit)

    window.btn_report = QPushButton("Export Report (TXT)")
    window.btn_csv = QPushButton("Export Fit Data (CSV)")
    window.btn_report.clicked.connect(window.export_report_txt)
    window.btn_csv.clicked.connect(window.export_fit_csv)
    layout.addWidget(window.btn_report)
    layout.addWidget(window.btn_csv)
    return group


def build_result_group(window):
    group = QGroupBox("5. Session")
    layout = QVBoxLayout(group)

    window.session_headline = QLabel("No fit executed.")
    window.session_headline.setWordWrap(True)
    window.session_headline.setStyleSheet("color: #1f3550; font-weight: 700;")
    layout.addWidget(window.session_headline)

    window.session_metrics = QLabel("Metrics: --")
    window.session_metrics.setWordWrap(True)
    window.session_metrics.setStyleSheet("color: #2a3c52;")
    layout.addWidget(window.session_metrics)

    window.session_params = QLabel("Params: --")
    window.session_params.setWordWrap(True)
    window.session_params.setStyleSheet("color: #2a3c52;")
    layout.addWidget(window.session_params)

    window.session_export = QLabel("Export: --")
    window.session_export.setWordWrap(True)
    window.session_export.setStyleSheet("color: #4b627d;")
    layout.addWidget(window.session_export)

    window.status_summary = window.session_headline

    window.btn_focus_workspace = QPushButton("Focus Workspace Tab")
    window.btn_focus_clean = QPushButton("Focus Clean Output Tab")
    window.btn_focus_log = QPushButton("Focus Session Log Tab")
    window.btn_focus_workspace.clicked.connect(lambda: window.plot.tabs.setCurrentIndex(0))
    window.btn_focus_clean.clicked.connect(lambda: window.plot.tabs.setCurrentIndex(1))
    window.btn_focus_log.clicked.connect(lambda: window.plot.tabs.setCurrentIndex(2))
    layout.addWidget(window.btn_focus_workspace)
    layout.addWidget(window.btn_focus_clean)
    layout.addWidget(window.btn_focus_log)
    return group

