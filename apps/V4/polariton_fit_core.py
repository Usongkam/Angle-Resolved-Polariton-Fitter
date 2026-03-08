import numpy as np
from scipy.optimize import least_squares

from polariton_models import J0


def density_weights(k_values):
    k_values = np.asarray(k_values, dtype=np.float64)
    if k_values.size <= 1:
        return np.ones_like(k_values, dtype=np.float64)
    order = np.argsort(k_values)
    ordered = k_values[order]
    spacing = np.empty_like(ordered)
    spacing[0] = max(abs(ordered[1] - ordered[0]), 1e-6)
    spacing[-1] = max(abs(ordered[-1] - ordered[-2]), 1e-6)
    if ordered.size > 2:
        spacing[1:-1] = np.maximum(0.5 * (ordered[2:] - ordered[:-2]), 1e-6)
    weights_ordered = 1.0 / np.maximum(spacing, 1e-6)
    weights_ordered = 1.0 / np.maximum(weights_ordered, 1e-12)
    weights_ordered /= np.mean(weights_ordered)
    weights = np.empty_like(weights_ordered)
    weights[order] = weights_ordered
    return weights


def low_k_stats(k_values, energies, center=0.0):
    k_values = np.asarray(k_values, dtype=np.float64)
    energies = np.asarray(energies, dtype=np.float64)
    if k_values.size == 0:
        return None, None
    centered = np.abs(k_values - float(center))
    threshold = np.quantile(centered, 0.35)
    mask = centered <= max(threshold, 1e-6)
    if np.sum(mask) < 3:
        mask = np.argsort(centered)[: min(5, k_values.size)]
        return k_values[mask], energies[mask]
    return k_values[mask], energies[mask]


def estimate_mass_from_quadratic(k_values, energies, fallback):
    if k_values is None or energies is None or k_values.size < 3:
        return fallback
    try:
        quad = np.polyfit(k_values, energies, 2)
        curvature = max(float(quad[0]), 1e-10)
        m_r = J0 / curvature
        return float(np.clip(m_r, 1e-7, 1e-2))
    except Exception:
        return fallback


def estimate_branch_vertex(k_values, energies, fallback=0.0):
    if k_values is None or energies is None:
        return float(fallback)
    k_values = np.asarray(k_values, dtype=np.float64)
    energies = np.asarray(energies, dtype=np.float64)
    if k_values.size < 3:
        return float(fallback)
    try:
        quad = np.polyfit(k_values, energies, 2)
        curvature = float(quad[0])
        if not np.isfinite(curvature) or abs(curvature) < 1e-10:
            return float(fallback)
        vertex = -float(quad[1]) / (2.0 * curvature)
        if not np.isfinite(vertex):
            return float(fallback)
        return float(np.clip(vertex, np.min(k_values), np.max(k_values)))
    except Exception:
        return float(fallback)


def estimate_shared_k_shift(*branches):
    candidates = []
    for branch in branches:
        if branch is None:
            continue
        k_values, energies = branch
        vertex = estimate_branch_vertex(k_values, energies, fallback=np.nan)
        if np.isfinite(vertex):
            candidates.append(float(vertex))
    if not candidates:
        return 0.0
    return float(np.median(np.asarray(candidates, dtype=np.float64)))


def estimate_cavity_seed(k_values, energies, fallback_mr, fallback_e0):
    mr_guess = float(fallback_mr)
    e0_guess = float(fallback_e0)
    k_shift_guess = 0.0
    if k_values.size < 3:
        return mr_guess, e0_guess, k_shift_guess

    try:
        quad = np.polyfit(k_values, energies, 2)
        curvature = max(float(quad[0]), 1e-10)
        mr_guess = float(np.clip(J0 / curvature, 1e-7, 1e-2))
        k_shift_guess = float(np.clip(-quad[1] / (2.0 * curvature), np.min(k_values), np.max(k_values)))
        e0_vertex = float(np.polyval(quad, k_shift_guess))
        if np.isfinite(e0_vertex):
            e0_guess = e0_vertex
    except Exception:
        pass
    return mr_guess, e0_guess, k_shift_guess


def build_ui_initial_guess(mode, config):
    if mode == "ca":
        return {
            "m_r": float(config["ca_mr_p0"]),
            "E0": float(config["ca_e0_p0"]),
            "k_shift": 0.0,
        }
    return {
        "m_r": float(config["mr_p0"]),
        "E0": float(config["e0_p0"]),
        "g": float(config["g_p0"]),
        "Eex": float(config["eex_p0"]),
        "k_shift": float(config.get("kshift_p0", 0.0)),
    }


def estimate_initial_guess(mode, data_pack, config):
    if mode == "ca":
        k_value, energy = data_pack["cavity"]
        low_k, low_e = low_k_stats(k_value, energy)
        e0_guess = float(np.median(low_e)) if low_e is not None else float(config["ca_e0_p0"])
        mr_guess = estimate_mass_from_quadratic(low_k, low_e, float(config["ca_mr_p0"])) if low_k is not None else float(config["ca_mr_p0"])
        mr_guess, e0_guess, k_shift_guess = estimate_cavity_seed(k_value, energy, mr_guess, e0_guess)
        return {"m_r": mr_guess, "E0": e0_guess, "k_shift": k_shift_guess}

    if mode == "lp":
        k_value, energy = data_pack["lp"]
        k_shift_guess = estimate_shared_k_shift((k_value, energy))
        low_k, low_e = low_k_stats(k_value, energy, center=k_shift_guess)
        e_lp0 = float(np.median(low_e)) if low_e is not None else float(np.median(energy))
        eex_guess = max(float(np.max(energy)), e_lp0 + 5.0)
        g_guess = max(0.5 * abs(eex_guess - float(np.min(energy))), float(config["g_p0"]) * 0.25, 1.0)
        e0_guess = max(float(config["e0_p0"]), e_lp0 + 0.5 * g_guess)
        mr_guess = estimate_mass_from_quadratic(low_k, low_e, float(config["mr_p0"])) if low_k is not None else float(config["mr_p0"])
        return {"m_r": mr_guess, "E0": e0_guess, "g": g_guess, "Eex": eex_guess, "k_shift": k_shift_guess}

    k_lp, e_lp = data_pack["lp"]
    k_up, e_up = data_pack["up"]
    k_shift_guess = estimate_shared_k_shift((k_lp, e_lp), (k_up, e_up))
    low_k_lp, low_lp = low_k_stats(k_lp, e_lp, center=k_shift_guess)
    low_k_up, low_up = low_k_stats(k_up, e_up, center=k_shift_guess)

    lp_center = float(np.median(low_lp)) if low_lp is not None else float(np.median(e_lp))
    up_center = float(np.median(low_up)) if low_up is not None else float(np.median(e_up))
    split = max(up_center - lp_center, 2.0 * float(config["g_p0"]), 2.0)
    g_guess = max(0.5 * split, 1.0)
    eex_guess = max(float(np.median(e_up)), up_center, lp_center + 2.0 * g_guess)
    e0_guess = float(lp_center + up_center - eex_guess)
    if not np.isfinite(e0_guess):
        e0_guess = float(config["e0_p0"])
    mr_guess = estimate_mass_from_quadratic(low_k_lp, low_lp, float(config["mr_p0"])) if low_k_lp is not None else float(config["mr_p0"])
    return {"m_r": mr_guess, "E0": e0_guess, "g": g_guess, "Eex": eex_guess, "k_shift": k_shift_guess}


def clip_guess_to_bounds(initial, lower, upper, order):
    return np.array([np.clip(initial[key], lower[idx], upper[idx]) for idx, key in enumerate(order)], dtype=np.float64)


def weighted_rmse(residual, weight):
    residual = np.asarray(residual, dtype=np.float64)
    weight = np.asarray(weight, dtype=np.float64)
    if residual.size == 0:
        return float("nan")
    return float(np.sqrt(np.sum(weight * residual**2) / np.sum(weight)))


def residual_reweight(residual):
    residual = np.asarray(residual, dtype=np.float64)
    if residual.size == 0:
        return residual
    scale = 1.4826 * np.median(np.abs(residual - np.median(residual)))
    scale = max(float(scale), 1e-6)
    return 1.0 / np.sqrt(1.0 + (residual / (2.5 * scale)) ** 2)


def build_diagnostics(residual, weight, initial_guess, final_param, bounds):
    residual = np.asarray(residual, dtype=np.float64)
    weight = np.asarray(weight, dtype=np.float64)
    abs_residual = np.abs(residual)
    outlier_limit = max(3.0 * np.median(abs_residual) if abs_residual.size else 0.0, 1e-6)
    outlier_fraction = float(np.mean(abs_residual > outlier_limit)) if abs_residual.size else 0.0
    weighted = weighted_rmse(residual, weight)
    bound_hits = []
    for idx, key in enumerate(final_param):
        if np.isclose(final_param[key], bounds[0][idx]) or np.isclose(final_param[key], bounds[1][idx]):
            bound_hits.append(key)
    confidence = "good"
    if outlier_fraction > 0.18 or bound_hits:
        confidence = "warning"
    if outlier_fraction > 0.35:
        confidence = "poor"
    return {
        "weighted_rmse": weighted,
        "outlier_fraction": outlier_fraction,
        "confidence": confidence,
        "bound_hits": bound_hits,
        "initial_guess": initial_guess,
    }


def run_weighted_fit(param_order, lower, upper, initial_guess, residual_builder):
    x0 = clip_guess_to_bounds(initial_guess, lower, upper, param_order)
    base_weight = np.asarray(residual_builder("weights"), dtype=np.float64)

    def solve(start_param, extra_weight):
        total_weight = base_weight * extra_weight

        def objective(param):
            residual = np.asarray(residual_builder(param), dtype=np.float64)
            return np.sqrt(total_weight) * residual

        return least_squares(objective, x0=start_param, bounds=(lower, upper), loss="soft_l1", f_scale=2.0, max_nfev=40000)

    pass1 = solve(x0, np.ones_like(base_weight))
    residual1 = np.asarray(residual_builder(pass1.x), dtype=np.float64)
    robust_weight = residual_reweight(residual1)
    pass2 = solve(pass1.x, robust_weight)
    residual2 = np.asarray(residual_builder(pass2.x), dtype=np.float64)
    final_weight = base_weight * robust_weight
    final_param = {key: float(pass2.x[idx]) for idx, key in enumerate(param_order)}
    diagnostics = build_diagnostics(residual2, final_weight, initial_guess, final_param, (lower, upper))
    diagnostics.update({
        "solver_success": bool(pass2.success),
        "solver_status": int(pass2.status),
        "solver_nfev": int(pass2.nfev),
        "solver_message": str(pass2.message),
        "solver_cost": float(pass2.cost),
    })
    return pass2, residual2, final_weight, final_param, diagnostics


def choose_best_fit_result(seed_results):
    if not seed_results:
        raise ValueError("seed_results must not be empty")

    successful = [item for item in seed_results if item["result"].success]
    pool = successful if successful else list(seed_results)

    def sort_key(item):
        diagnostics = item["diagnostics"]
        weighted = diagnostics.get("weighted_rmse", np.inf)
        cost = diagnostics.get("solver_cost", np.inf)
        nfev = diagnostics.get("solver_nfev", np.inf)
        return (
            weighted if np.isfinite(weighted) else np.inf,
            cost if np.isfinite(cost) else np.inf,
            nfev if np.isfinite(nfev) else np.inf,
        )

    return min(pool, key=sort_key)
