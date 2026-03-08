import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import signal
from scipy.ndimage import gaussian_filter1d

from polariton_fit_core import build_ui_initial_guess, choose_best_fit_result, density_weights, estimate_initial_guess, run_weighted_fit
from polariton_models import HBAR_C_MEV_NM, HC_MEV_NM, cavity_dispersion, polariton_branches


@dataclass
class FitSummary:
    mode: str
    success: bool
    text: str


class PolaritonFitter:
    def __init__(self):
        self.full_raw_angle_coords = None
        self.full_intensity_matrix = None
        self.raw_angle_coords = None
        self.intensity_matrix = None
        self.wavelength_nm = None
        self.energy_mev = None
        self.full_angle_deg = None
        self.angle_deg = None

        self.crop_min_index = 0
        self.crop_max_index = 0
        self.k0_index = 0
        self.na = 0.9

        self.fit_params = {}
        self.fit_summary = FitSummary(mode="", success=False, text="")
        self.last_fit = {}

    def load_data(self, file_path):
        try:
            frame = pd.read_table(file_path, header=None)
            data = np.array(frame.values, dtype=np.float64)
            rows, cols = data.shape
            if rows < 3 or cols < 3:
                return False, f"Data shape too small: {data.shape}"

            if cols >= rows:
                raw_wavelength = data[0, 1:]
                raw_angle = data[1:, 0]
                raw_intensity = data[1:, 1:]
            else:
                raw_wavelength = data[1:, 0]
                raw_angle = data[0, 1:]
                raw_intensity = data[1:, 1:].T

            valid_wavelength = np.isfinite(raw_wavelength) & (raw_wavelength > 0)
            raw_wavelength = raw_wavelength[valid_wavelength]
            raw_intensity = raw_intensity[:, valid_wavelength]

            order = np.argsort(raw_wavelength)
            self.wavelength_nm = raw_wavelength[order]
            self.full_intensity_matrix = np.nan_to_num(raw_intensity[:, order], nan=0.0, posinf=0.0, neginf=0.0)
            self.full_raw_angle_coords = np.nan_to_num(raw_angle, nan=0.0, posinf=0.0, neginf=0.0)
            self.energy_mev = HC_MEV_NM / self.wavelength_nm
            return True, f"Loaded matrix: {self.full_intensity_matrix.shape}"
        except Exception as exc:
            logging.exception("load_data failed")
            return False, f"Load failed: {exc}"

    def _auto_crop_bounds(self, angle_profile, smoothing_sigma, crop_padding):
        sigma = max(0.0, float(smoothing_sigma))
        smooth = gaussian_filter1d(angle_profile, sigma=sigma) if sigma > 0 else angle_profile.astype(np.float64, copy=True)
        grad = np.diff(smooth)
        left = int(np.argmax(grad)) - int(crop_padding)
        right = int(np.argmin(grad)) + 1 + int(crop_padding)
        return left, right

    def _manual_crop_bounds(self, left_bound, right_bound):
        left = int(left_bound if left_bound is not None else 0)
        right = int(right_bound if right_bound is not None else len(self.full_raw_angle_coords) - 1)
        return left, right

    def apply_processing(self, smoothing_sigma=5, na=0.9, auto_k0=True, k0_index=0, crop_padding=5, crop_mode="auto", left_bound=None, right_bound=None):
        if self.full_intensity_matrix is None:
            raise ValueError("No data loaded")

        self.na = float(np.clip(na, 0.05, 1.5))
        angle_profile = np.sum(self.full_intensity_matrix, axis=1)
        if crop_mode == "manual":
            left, right = self._manual_crop_bounds(left_bound, right_bound)
        else:
            left, right = self._auto_crop_bounds(angle_profile, smoothing_sigma, crop_padding)

        left = int(np.clip(left, 0, len(angle_profile) - 1))
        right = int(np.clip(right, 0, len(angle_profile) - 1))

        if right <= left:
            left = 0
            right = len(angle_profile) - 1

        self.crop_min_index = left
        self.crop_max_index = right
        self.raw_angle_coords = self.full_raw_angle_coords[left : right + 1]
        self.intensity_matrix = self.full_intensity_matrix[left : right + 1, :]

        if auto_k0:
            cropped_profile = np.sum(self.intensity_matrix, axis=1)
            index = np.arange(cropped_profile.size)
            if np.sum(cropped_profile) > 0:
                self.k0_index = int(np.round(np.sum(cropped_profile * index) / np.sum(cropped_profile)))
            else:
                self.k0_index = int(cropped_profile.size // 2)
        else:
            self.k0_index = int(np.clip(k0_index, 0, self.intensity_matrix.shape[0] - 1))

        k0_raw_coord = float(self.raw_angle_coords[self.k0_index])
        cropped_centered = self.raw_angle_coords - k0_raw_coord
        cropped_span = max(1.0, float(np.max(np.abs(cropped_centered))))
        full_centered = self.full_raw_angle_coords - k0_raw_coord
        full_sin_theta = np.clip((full_centered / cropped_span) * self.na, -1.0, 1.0)
        cropped_sin_theta = np.clip((cropped_centered / cropped_span) * self.na, -1.0, 1.0)
        self.full_angle_deg = np.rad2deg(np.arcsin(full_sin_theta))
        self.angle_deg = np.rad2deg(np.arcsin(cropped_sin_theta))

    def snap_to_extremum(self, click_angle, click_energy, feature="dip", search_px=10):
        if self.intensity_matrix is None:
            return None, None

        angle_index = int(np.argmin(np.abs(self.angle_deg - click_angle)))
        energy_index = int(np.argmin(np.abs(self.energy_mev - click_energy)))
        return self._snap_index(angle_index, energy_index, feature, search_px)

    def _snap_index(self, angle_index, energy_index, feature, search_px):
        j0 = max(0, int(energy_index) - int(search_px))
        j1 = min(self.energy_mev.size, int(energy_index) + int(search_px) + 1)
        if j1 <= j0:
            return float(self.angle_deg[angle_index]), float(self.energy_mev[energy_index]), angle_index, float(energy_index)

        segment = self.intensity_matrix[angle_index, j0:j1]
        local_index = int(np.argmin(segment)) if feature == "dip" else int(np.argmax(segment))
        real_index = self._refine_peak_center(self.intensity_matrix[angle_index], j0 + local_index, feature)
        energy_value = float(np.interp(real_index, np.arange(self.energy_mev.size, dtype=np.float64), self.energy_mev))
        return float(self.angle_deg[angle_index]), energy_value, angle_index, real_index

    def _refine_peak_center(self, profile, center_index, feature, radius=4):
        profile = np.asarray(profile, dtype=np.float64)
        j0 = max(0, int(center_index) - int(radius))
        j1 = min(profile.size, int(center_index) + int(radius) + 1)
        if j1 <= j0:
            return float(center_index)

        local = profile[j0:j1]
        if feature == "dip":
            weights = np.max(local) - local
        else:
            weights = local - np.min(local)
        weights = np.clip(weights, 0.0, None)
        if not np.any(weights):
            return float(center_index)

        local_axis = np.arange(j0, j1, dtype=np.float64)
        return float(np.sum(local_axis * weights) / np.sum(weights))

    def _refine_trace_centerline(self, trace, feature):
        if not trace:
            return []

        refined = []
        for angle_index, energy_index, prominence in trace:
            center_index = self._refine_peak_center(self.intensity_matrix[angle_index], energy_index, feature)
            refined.append((angle_index, center_index, prominence))
        return refined

    def trace_branch(self, start_angle, start_energy, feature="dip", search_px=16, min_prominence=5.0, max_misses=4):
        if self.intensity_matrix is None or self.angle_deg is None:
            raise ValueError("Data not processed")

        start_angle_index = int(np.argmin(np.abs(self.angle_deg - start_angle)))
        start_energy_index = int(np.argmin(np.abs(self.energy_mev - start_energy)))
        _, _, start_angle_index, start_energy_index = self._snap_index(start_angle_index, start_energy_index, feature, search_px)

        forward = self._trace_direction(start_angle_index, start_energy_index, +1, feature, search_px, min_prominence, max_misses)
        backward = self._trace_direction(start_angle_index, start_energy_index, -1, feature, search_px, min_prominence, max_misses)

        combined = backward[::-1] + forward[1:]
        combined = self._trim_trace(combined, min_prominence)
        combined = self._refine_trace_centerline(combined, feature)
        energy_axis = np.arange(self.energy_mev.size, dtype=np.float64)
        return [(float(self.angle_deg[i]), float(np.interp(j, energy_axis, self.energy_mev))) for i, j, _ in combined]

    def _trace_direction(self, start_i, start_j, direction, feature, search_px, min_prominence, max_misses):
        trace = [(start_i, start_j, float("inf"))]
        last_j = int(start_j)
        misses = 0
        iterator = range(start_i + 1, self.intensity_matrix.shape[0]) if direction > 0 else range(start_i - 1, -1, -1)

        for angle_index in iterator:
            candidate_j, prominence = self._find_next_extremum(angle_index, last_j, feature, search_px)
            if candidate_j is None:
                misses += 1
                if misses >= max_misses:
                    break
                continue

            trace.append((angle_index, candidate_j, prominence))
            last_j = int(candidate_j)
            misses = misses + 1 if prominence < min_prominence else 0
            if misses >= max_misses:
                break

        return trace

    def _find_next_extremum(self, angle_index, center_j, feature, search_px):
        j0 = max(0, int(center_j) - int(search_px))
        j1 = min(self.energy_mev.size, int(center_j) + int(search_px) + 1)
        if j1 <= j0:
            return None, 0.0

        raw = self.intensity_matrix[angle_index, j0:j1]
        work = -raw if feature == "dip" else raw
        center_local = int(np.clip(center_j - j0, 0, work.size - 1))

        peaks, props = signal.find_peaks(work, prominence=0)
        if peaks.size > 0:
            prominences = props.get("prominences", np.zeros_like(peaks, dtype=np.float64))
            distances = np.abs(peaks - center_local)
            scores = prominences - 0.25 * distances
            best = int(np.argmax(scores))
            peak_local = int(peaks[best])
            prominence = float(prominences[best])
        else:
            peak_local = int(np.argmax(work))
            prominence = float(work[peak_local] - np.median(work))

        refined_peak = self._refine_peak_center(self.intensity_matrix[angle_index], j0 + peak_local, feature)
        return refined_peak, max(0.0, prominence)

    def _trim_trace(self, trace, min_prominence):
        if not trace:
            return []
        last_good = 0
        for idx, (_, _, prominence) in enumerate(trace):
            if prominence >= min_prominence or idx == 0:
                last_good = idx
        return trace[: last_good + 1]

    def angles_to_k(self, angles_deg, energies_mev):
        angles = np.asarray(angles_deg, dtype=np.float64)
        energies = np.asarray(energies_mev, dtype=np.float64)
        return (energies / HC_MEV_NM) * (2 * np.pi) * np.sin(np.deg2rad(angles)) * 1e3

    def _prepare_branch(self, points):
        if not points:
            return np.array([]), np.array([]), np.array([])

        arr = np.array(points, dtype=np.float64)
        rounded = np.round(arr, 3)
        _, unique_index = np.unique(rounded, axis=0, return_index=True)
        arr = arr[np.sort(unique_index)]
        arr = arr[np.argsort(arr[:, 0])]

        angles = arr[:, 0]
        energies = arr[:, 1]
        k_values = self.angles_to_k(angles, energies)
        valid = np.isfinite(k_values) & np.isfinite(energies)
        return angles[valid], energies[valid], k_values[valid]

    def prepare_data_pack(self, cavity_points, lp_points, up_points):
        data_pack = {}
        cavity_angle, cavity_energy, cavity_k = self._prepare_branch(cavity_points)
        lp_angle, lp_energy, lp_k = self._prepare_branch(lp_points)
        up_angle, up_energy, up_k = self._prepare_branch(up_points)

        if cavity_k.size:
            data_pack["cavity"] = (cavity_k, cavity_energy)
            data_pack["cavity_angle"] = cavity_angle
        if lp_k.size:
            data_pack["lp"] = (lp_k, lp_energy)
            data_pack["lp_angle"] = lp_angle
        if up_k.size:
            data_pack["up"] = (up_k, up_energy)
            data_pack["up_angle"] = up_angle
        return data_pack

    def fit_data(self, mode, data_pack, config):
        self.fit_params = {}
        self.last_fit = {}

        def plain_rmse(residual):
            residual = np.asarray(residual, dtype=np.float64)
            return float(np.sqrt(np.mean(residual**2))) if residual.size else float("nan")

        try:
            if mode == "ca":
                if "cavity" not in data_pack:
                    self.fit_summary = FitSummary(mode, False, "Cavity fit requires cavity trace points")
                    return False
                k_value, energy = data_pack["cavity"]
                if k_value.size < 3:
                    self.fit_summary = FitSummary(mode, False, "Need at least 3 cavity points")
                    return False

                initial_guess = estimate_initial_guess(mode, data_pack, config)
                param_order = ["m_r", "E0", "k_shift"]
                k_span = max(float(np.max(k_value) - np.min(k_value)), 1e-3)
                lower = np.array([config["ca_mr_b_min"], config["ca_e0_b_min"], float(np.min(k_value) - 0.25 * k_span)], dtype=np.float64)
                upper = np.array([config["ca_mr_b_max"], config["ca_e0_b_max"], float(np.max(k_value) + 0.25 * k_span)], dtype=np.float64)
                density_weight = density_weights(k_value)

                def residual_builder(param):
                    if isinstance(param, str) and param == "weights":
                        return density_weight
                    prediction = cavity_dispersion(k_value, param[0], param[1], param[2])
                    return prediction - energy

                result, residual, weight, final_param, diagnostics = run_weighted_fit(
                    param_order, lower, upper, initial_guess, residual_builder
                )
                if not result.success:
                    self.fit_summary = FitSummary(
                        mode,
                        False,
                        "[Cavity]\n"
                        f"optimization_status={diagnostics['solver_status']}\n"
                        f"nfev={diagnostics['solver_nfev']}\n"
                        f"message={diagnostics['solver_message']}\n"
                        f"init={initial_guess}",
                    )
                    return False
                prediction = cavity_dispersion(k_value, final_param["m_r"], final_param["E0"], final_param["k_shift"])

                self.fit_params = final_param
                self.last_fit = {
                    "mode": mode,
                    "k": k_value,
                    "e": energy,
                    "pred": prediction,
                    "residual": residual,
                    "diagnostics": diagnostics,
                }
                self.fit_summary = FitSummary(
                    mode,
                    True,
                    "[Cavity]\n"
                    f"m_r={final_param['m_r']:.3e}\n"
                    f"E0={final_param['E0']:.3f} meV\n"
                    f"k_shift={final_param['k_shift']:.4f} um^-1\n"
                    f"RMSE={plain_rmse(residual):.3f}\n"
                    f"weighted_RMSE={diagnostics['weighted_rmse']:.3f}\n"
                    f"confidence={diagnostics['confidence']}\n"
                    f"optimization_status={diagnostics['solver_status']}\n"
                    f"nfev={diagnostics['solver_nfev']}\n"
                    f"init={initial_guess}",
                )
                return True

            if mode == "lp":
                if "lp" not in data_pack:
                    self.fit_summary = FitSummary(mode, False, "LP fit requires LP trace points")
                    return False
                k_value, energy = data_pack["lp"]
                if k_value.size < 4:
                    self.fit_summary = FitSummary(mode, False, "Need at least 4 LP points")
                    return False

                ui_guess = build_ui_initial_guess(mode, config)
                auto_guess = estimate_initial_guess(mode, data_pack, config)
                seed_candidates = [("ui", ui_guess), ("auto", auto_guess)]
                param_order = ["m_r", "E0", "g", "Eex", "k_shift"]
                lower = np.array([config["mr_b_min"], config["e0_b_min"], config["g_b_min"], config["eex_b_min"], config["kshift_b_min"]], dtype=np.float64)
                upper = np.array([config["mr_b_max"], config["e0_b_max"], config["g_b_max"], config["eex_b_max"], config["kshift_b_max"]], dtype=np.float64)
                density_weight = density_weights(k_value)

                def residual_builder(param):
                    if isinstance(param, str) and param == "weights":
                        return density_weight
                    prediction = polariton_branches(k_value, param[0], param[1], param[2], param[3], param[4])[0]
                    return prediction - energy

                seed_results = []
                for seed_source, initial_guess in seed_candidates:
                    result, residual, weight, final_param, diagnostics = run_weighted_fit(
                        param_order, lower, upper, initial_guess, residual_builder
                    )
                    diagnostics.update({
                        "seed_source": seed_source,
                        "seed_candidates": [name for name, _ in seed_candidates],
                        "tried_seeds": {name: guess.copy() for name, guess in seed_candidates},
                    })
                    seed_results.append({
                        "seed_source": seed_source,
                        "initial_guess": initial_guess,
                        "result": result,
                        "residual": residual,
                        "weight": weight,
                        "final_param": final_param,
                        "diagnostics": diagnostics,
                    })

                best_fit = choose_best_fit_result(seed_results)
                result = best_fit["result"]
                residual = best_fit["residual"]
                final_param = best_fit["final_param"]
                diagnostics = best_fit["diagnostics"]
                initial_guess = best_fit["initial_guess"]
                if not result.success:
                    self.fit_summary = FitSummary(
                        mode,
                        False,
                        "[LP only]\n"
                        f"seed_source={diagnostics['seed_source']}\n"
                        f"seed_candidates={','.join(diagnostics['seed_candidates'])}\n"
                        f"optimization_status={diagnostics['solver_status']}\n"
                        f"nfev={diagnostics['solver_nfev']}\n"
                        f"message={diagnostics['solver_message']}\n"
                        f"init={initial_guess}",
                    )
                    return False
                prediction = polariton_branches(k_value, final_param["m_r"], final_param["E0"], final_param["g"], final_param["Eex"], final_param["k_shift"])[0]

                self.fit_params = final_param
                self.last_fit = {
                    "mode": mode,
                    "k": k_value,
                    "e": energy,
                    "pred": prediction,
                    "residual": residual,
                    "diagnostics": diagnostics,
                }
                self.fit_summary = FitSummary(
                    mode,
                    True,
                    "[LP only]\n"
                    f"m_r={final_param['m_r']:.3e}\n"
                    f"E0={final_param['E0']:.3f} meV\n"
                    f"k_shift={final_param['k_shift']:.4f} um^-1\n"
                    f"g={final_param['g']:.3f} meV\n"
                    f"Eex={final_param['Eex']:.3f} meV\n"
                    f"RMSE={plain_rmse(residual):.3f}\n"
                    f"weighted_RMSE={diagnostics['weighted_rmse']:.3f}\n"
                    f"confidence={diagnostics['confidence']}\n"
                    f"seed_source={diagnostics['seed_source']}\n"
                    f"optimization_status={diagnostics['solver_status']}\n"
                    f"nfev={diagnostics['solver_nfev']}\n"
                    f"init={initial_guess}",
                )
                return True

            if mode == "coupled":
                if "lp" not in data_pack or "up" not in data_pack:
                    self.fit_summary = FitSummary(mode, False, "Coupled fit requires both LP and UP trace points")
                    return False
                k_lp, e_lp = data_pack["lp"]
                k_up, e_up = data_pack["up"]
                if k_lp.size < 3 or k_up.size < 3:
                    self.fit_summary = FitSummary(mode, False, "Need at least 3 LP and 3 UP points")
                    return False

                ui_guess = build_ui_initial_guess(mode, config)
                auto_guess = estimate_initial_guess(mode, data_pack, config)
                seed_candidates = [("ui", ui_guess), ("auto", auto_guess)]
                param_order = ["m_r", "E0", "g", "Eex", "k_shift"]
                lower = np.array([config["mr_b_min"], config["e0_b_min"], config["g_b_min"], config["eex_b_min"], config["kshift_b_min"]], dtype=np.float64)
                upper = np.array([config["mr_b_max"], config["e0_b_max"], config["g_b_max"], config["eex_b_max"], config["kshift_b_max"]], dtype=np.float64)
                weight_lp = density_weights(k_lp)
                weight_up = density_weights(k_up)
                density_weight = np.concatenate([weight_lp, weight_up])

                def residual_builder(param):
                    if isinstance(param, str) and param == "weights":
                        return density_weight
                    lp_pred, _ = polariton_branches(k_lp, param[0], param[1], param[2], param[3], param[4])
                    _, true_up_pred = polariton_branches(k_up, param[0], param[1], param[2], param[3], param[4])
                    return np.concatenate([lp_pred - e_lp, true_up_pred - e_up])

                seed_results = []
                for seed_source, initial_guess in seed_candidates:
                    result, residual, weight, final_param, diagnostics = run_weighted_fit(
                        param_order, lower, upper, initial_guess, residual_builder
                    )
                    diagnostics.update({
                        "seed_source": seed_source,
                        "seed_candidates": [name for name, _ in seed_candidates],
                        "tried_seeds": {name: guess.copy() for name, guess in seed_candidates},
                    })
                    seed_results.append({
                        "seed_source": seed_source,
                        "initial_guess": initial_guess,
                        "result": result,
                        "residual": residual,
                        "weight": weight,
                        "final_param": final_param,
                        "diagnostics": diagnostics,
                    })

                best_fit = choose_best_fit_result(seed_results)
                result = best_fit["result"]
                residual = best_fit["residual"]
                final_param = best_fit["final_param"]
                diagnostics = best_fit["diagnostics"]
                initial_guess = best_fit["initial_guess"]
                if not result.success:
                    self.fit_summary = FitSummary(
                        mode,
                        False,
                        "[Coupled]\n"
                        f"seed_source={diagnostics['seed_source']}\n"
                        f"seed_candidates={','.join(diagnostics['seed_candidates'])}\n"
                        f"optimization_status={diagnostics['solver_status']}\n"
                        f"nfev={diagnostics['solver_nfev']}\n"
                        f"message={diagnostics['solver_message']}\n"
                        f"init={initial_guess}",
                    )
                    return False
                lp_pred, _ = polariton_branches(k_lp, final_param["m_r"], final_param["E0"], final_param["g"], final_param["Eex"], final_param["k_shift"])
                _, up_pred = polariton_branches(k_up, final_param["m_r"], final_param["E0"], final_param["g"], final_param["Eex"], final_param["k_shift"])
                lp_rmse = plain_rmse(lp_pred - e_lp)
                up_rmse = plain_rmse(up_pred - e_up)
                diagnostics.update({
                    "lp_rmse": lp_rmse,
                    "up_rmse": up_rmse,
                })

                self.fit_params = final_param
                self.last_fit = {
                    "mode": mode,
                    "k_lp": k_lp,
                    "e_lp": e_lp,
                    "pred_lp": lp_pred,
                    "k_up": k_up,
                    "e_up": e_up,
                    "pred_up": up_pred,
                    "residual": residual,
                    "diagnostics": diagnostics,
                }
                self.fit_summary = FitSummary(
                    mode,
                    True,
                    "[Coupled]\n"
                    f"m_r={final_param['m_r']:.3e}\n"
                    f"E0={final_param['E0']:.3f} meV\n"
                    f"k_shift={final_param['k_shift']:.4f} um^-1\n"
                    f"g={final_param['g']:.3f} meV\n"
                    f"Eex={final_param['Eex']:.3f} meV\n"
                    f"RMSE={plain_rmse(residual):.3f}\n"
                    f"LP_RMSE={lp_rmse:.3f}\n"
                    f"UP_RMSE={up_rmse:.3f}\n"
                    f"weighted_RMSE={diagnostics['weighted_rmse']:.3f}\n"
                    f"confidence={diagnostics['confidence']}\n"
                    f"seed_source={diagnostics['seed_source']}\n"
                    f"optimization_status={diagnostics['solver_status']}\n"
                    f"nfev={diagnostics['solver_nfev']}\n"
                    f"init={initial_guess}",
                )
                return True

            self.fit_summary = FitSummary(mode, False, f"Unknown mode: {mode}")
            return False
        except Exception as exc:
            logging.exception("fit_data failed")
            self.fit_summary = FitSummary(mode, False, f"Fit failed: {exc}")
            return False

    def get_k_range(self):
        k_max = 5.0
        if self.last_fit:
            values = []
            for key in ("k", "k_lp", "k_up"):
                if key in self.last_fit:
                    values.append(np.asarray(self.last_fit[key], dtype=np.float64))
            if values:
                merged = np.concatenate(values)
                max_abs = float(np.max(np.abs(merged)))
                if np.isfinite(max_abs) and max_abs > 0:
                    k_max = 1.15 * max_abs

        if self.angle_deg is not None and self.energy_mev is not None:
            display_energy = float(np.max(self.energy_mev))
            display_angle = float(np.max(np.abs(self.angle_deg)))
            display_k_max = abs((display_energy / HC_MEV_NM) * (2 * np.pi) * np.sin(np.deg2rad(display_angle)) * 1e3)
            if np.isfinite(display_k_max) and display_k_max > 0:
                k_max = max(k_max, 1.15 * display_k_max)
        return -k_max, k_max

    def _angle_from_k_energy(self, k_um_inv, energy_mev):
        value = (k_um_inv * 1e-3) * HBAR_C_MEV_NM / energy_mev
        return np.rad2deg(np.arcsin(np.clip(value, -1.0, 1.0)))

    def _align_curve_to_display_angle(self, source_angle, source_energy):
        if self.angle_deg is None or not self.angle_deg.size:
            return np.asarray(source_angle, dtype=np.float64), np.asarray(source_energy, dtype=np.float64)

        source_angle = np.asarray(source_angle, dtype=np.float64)
        source_energy = np.asarray(source_energy, dtype=np.float64)
        order = np.argsort(source_angle)
        sorted_angle = source_angle[order]
        sorted_energy = source_energy[order]
        unique_angle, unique_index = np.unique(sorted_angle, return_index=True)
        unique_energy = sorted_energy[unique_index]
        display_angle = np.asarray(self.angle_deg, dtype=np.float64)
        aligned_energy = np.interp(display_angle, unique_angle, unique_energy)
        return display_angle, aligned_energy

    def generate_curves(self, k_min=None, k_max=None, num_points=500):
        if not self.fit_params:
            return {}

        if k_min is None or k_max is None:
            k_min, k_max = self.get_k_range()

        k_value = np.linspace(float(k_min), float(k_max), int(num_points))
        curves = {"k": k_value}
        param = self.fit_params
        display_angle = np.asarray(self.angle_deg, dtype=np.float64) if self.angle_deg is not None and self.angle_deg.size else None

        if "E0" in param:
            e_cavity = cavity_dispersion(k_value, param["m_r"], param["E0"], param.get("k_shift", 0.0))
            angle_cavity = self._angle_from_k_energy(k_value, e_cavity)
            curves["E_cav"] = e_cavity
            curves["angle_cav_k"] = angle_cavity
            if display_angle is not None:
                curves["angle_cav"], curves["E_cav_angle"] = self._align_curve_to_display_angle(angle_cavity, e_cavity)
            else:
                curves["angle_cav"] = angle_cavity
                curves["E_cav_angle"] = e_cavity

        if "g" in param:
            e_lp, e_up = polariton_branches(k_value, param["m_r"], param["E0"], param["g"], param["Eex"], param.get("k_shift", 0.0))
            angle_lp = self._angle_from_k_energy(k_value, e_lp)
            angle_up = self._angle_from_k_energy(k_value, e_up)
            curves["E_lp"] = e_lp
            curves["E_up"] = e_up
            curves["E_ex"] = np.full_like(k_value, param["Eex"])
            curves["angle_lp_k"] = angle_lp
            curves["angle_up_k"] = angle_up
            if display_angle is not None:
                curves["angle_lp"], curves["E_lp_angle"] = self._align_curve_to_display_angle(angle_lp, e_lp)
                curves["angle_up"], curves["E_up_angle"] = self._align_curve_to_display_angle(angle_up, e_up)
                curves["angle_ex"] = display_angle
                curves["E_ex_angle"] = np.full_like(display_angle, param["Eex"], dtype=np.float64)
            else:
                curves["angle_lp"] = angle_lp
                curves["angle_up"] = angle_up
                curves["E_lp_angle"] = e_lp
                curves["E_up_angle"] = e_up
                curves["angle_ex"] = curves.get("angle_cav", angle_lp)
                curves["E_ex_angle"] = np.full_like(k_value, param["Eex"])
        return curves














