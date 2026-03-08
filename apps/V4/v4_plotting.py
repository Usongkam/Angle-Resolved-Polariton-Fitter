import numpy as np


def draw_heatmap(ax, x, y, z):
    vmin = float(np.nanpercentile(z, 2))
    vmax = float(np.nanpercentile(z, 98))
    ax.pcolormesh(x, y, z, shading="auto", cmap="gray", vmin=vmin, vmax=vmax)


def draw_raw_crop_preview(ax_raw, full_angle_deg, crop_min_index, crop_max_index, preview_bounds=None):
    if full_angle_deg is None or not full_angle_deg.size:
        return
    left_angle = float(full_angle_deg[crop_min_index])
    right_angle = float(full_angle_deg[crop_max_index])
    if preview_bounds is not None:
        left_index, right_index = preview_bounds
        left_angle = float(full_angle_deg[left_index])
        right_angle = float(full_angle_deg[right_index])
    x_min, x_max = sorted((left_angle, right_angle))
    ax_raw.axvspan(x_min, x_max, color="#4c9aff", alpha=0.16, zorder=3)
    ax_raw.axvline(x_min, color="#0b63ce", linewidth=1.5, linestyle="--", zorder=4)
    ax_raw.axvline(x_max, color="#0b63ce", linewidth=1.5, linestyle="--", zorder=4)


def draw_base_images(plot, fitter, preview_bounds=None):
    if fitter.full_intensity_matrix is None or fitter.intensity_matrix is None:
        return
    plot.reset_axes()
    raw_data = fitter.full_intensity_matrix.T
    crop_data = fitter.intensity_matrix.T
    draw_heatmap(plot.ax_raw, fitter.full_angle_deg, fitter.energy_mev, raw_data)
    draw_raw_crop_preview(plot.ax_raw, fitter.full_angle_deg, fitter.crop_min_index, fitter.crop_max_index, preview_bounds=preview_bounds)
    draw_heatmap(plot.ax_pick, fitter.angle_deg, fitter.energy_mev, crop_data)
    draw_heatmap(plot.clean_ax, fitter.angle_deg, fitter.energy_mev, crop_data)
    plot.canvas.draw_idle()
    plot.clean_canvas.draw_idle()


def redraw_raw_crop_preview(plot, fitter, preview_bounds=None):
    if fitter.full_intensity_matrix is None or fitter.full_angle_deg is None:
        return
    plot.ax_raw.cla()
    plot.ax_raw.set_title("1. Raw / crop overview")
    plot.ax_raw.set_xlabel("Angle / deg")
    plot.ax_raw.set_ylabel("Energy / meV")
    raw_data = fitter.full_intensity_matrix.T
    draw_heatmap(plot.ax_raw, fitter.full_angle_deg, fitter.energy_mev, raw_data)
    draw_raw_crop_preview(plot.ax_raw, fitter.full_angle_deg, fitter.crop_min_index, fitter.crop_max_index, preview_bounds=preview_bounds)
    plot.canvas.draw_idle()


def draw_fit_overlays(plot, fitter, fit_curves):
    if fitter.intensity_matrix is None:
        return

    plot.ax_k.cla()
    plot.ax_residual.cla()
    plot.ax_k.set_title("3. k-space fit")
    plot.ax_k.set_xlabel("k / um^-1")
    plot.ax_k.set_ylabel("Energy / meV")
    plot.ax_residual.set_title("4. Residuals")
    plot.ax_residual.set_xlabel("Point index")
    plot.ax_residual.set_ylabel("Residual / meV")

    clean_lines = []
    if not fit_curves:
        return

    colors = {"cavity": "#ff8c00", "lp": "#cc0000", "up": "#0066cc", "exciton": "#228b22"}
    if "E_cav" in fit_curves:
        plot.ax_k.plot(fit_curves["k"], fit_curves["E_cav"], color=colors["cavity"], linewidth=2, label="Cavity")
        clean_lines.append((fit_curves.get("angle_cav"), fit_curves.get("E_cav_angle", fit_curves["E_cav"]), colors["cavity"], "Cavity"))
    if "E_lp" in fit_curves:
        plot.ax_k.plot(fit_curves["k"], fit_curves["E_lp"], color=colors["lp"], linewidth=2, label="LP")
        clean_lines.append((fit_curves.get("angle_lp"), fit_curves.get("E_lp_angle", fit_curves["E_lp"]), colors["lp"], "LP"))
    if "E_up" in fit_curves:
        plot.ax_k.plot(fit_curves["k"], fit_curves["E_up"], color=colors["up"], linewidth=2, label="UP")
        clean_lines.append((fit_curves.get("angle_up"), fit_curves.get("E_up_angle", fit_curves["E_up"]), colors["up"], "UP"))
    if "E_ex" in fit_curves:
        plot.ax_k.plot(fit_curves["k"], fit_curves["E_ex"], color=colors["exciton"], linewidth=1.5, linestyle="--", label="Exciton")
        clean_lines.append((fit_curves.get("angle_ex"), fit_curves.get("E_ex_angle", fit_curves["E_ex"]), colors["exciton"], "Exciton"))

    last_fit = fitter.last_fit
    if last_fit.get("mode") == "ca":
        plot.ax_k.plot(last_fit["k"], last_fit["e"], linestyle="None", marker="o", color=colors["cavity"], alpha=0.7)
        plot.ax_residual.plot(last_fit["residual"], color=colors["cavity"], marker="o")
    elif last_fit.get("mode") == "lp":
        plot.ax_k.plot(last_fit["k"], last_fit["e"], linestyle="None", marker="o", color=colors["lp"], alpha=0.7)
        plot.ax_residual.plot(last_fit["residual"], color=colors["lp"], marker="o")
    elif last_fit.get("mode") == "coupled":
        plot.ax_k.plot(last_fit["k_lp"], last_fit["e_lp"], linestyle="None", marker="o", color=colors["lp"], alpha=0.7)
        plot.ax_k.plot(last_fit["k_up"], last_fit["e_up"], linestyle="None", marker="o", color=colors["up"], alpha=0.7)
        split = len(last_fit["k_lp"])
        plot.ax_residual.plot(np.arange(split), last_fit["residual"][:split], color=colors["lp"], marker="o", linestyle="None")
        plot.ax_residual.plot(np.arange(len(last_fit["residual"][split:])), last_fit["residual"][split:], color=colors["up"], marker="o", linestyle="None")

    plot.ax_k.legend(loc="best", fontsize="small")

    plot.clean_ax.cla()
    draw_heatmap(plot.clean_ax, fitter.angle_deg, fitter.energy_mev, fitter.intensity_matrix.T)
    plot.clean_ax.set_title("Crop clean preview")
    plot.clean_ax.set_xlabel("Angle / deg")
    plot.clean_ax.set_ylabel("Energy / meV")

    plot.full_clean_ax.cla()
    plot.full_clean_ax.set_title("Full clean preview")
    plot.full_clean_ax.set_xlabel("Angle / deg")
    plot.full_clean_ax.set_ylabel("Energy / meV")

    curve_energy = []
    for angles, energies, color, label in clean_lines:
        if angles is None:
            continue
        plot.clean_ax.plot(angles, energies, color=color, linewidth=2, label=label)
        plot.full_clean_ax.plot(angles, energies, color=color, linewidth=2, label=label)
        curve_energy.extend(np.asarray(energies, dtype=np.float64).tolist())

    if fitter.angle_deg is not None and fitter.angle_deg.size:
        angle_min = float(fitter.angle_deg.min())
        angle_max = float(fitter.angle_deg.max())
        plot.clean_ax.set_xlim(angle_min, angle_max)
        plot.full_clean_ax.set_xlim(angle_min, angle_max)

    if fitter.energy_mev is not None and fitter.energy_mev.size:
        plot.clean_ax.set_ylim(float(fitter.energy_mev.min()), float(fitter.energy_mev.max()))

    if curve_energy:
        y_min = float(min(curve_energy))
        y_max = float(max(curve_energy))
        pad = max((y_max - y_min) * 0.08, 5.0)
        plot.full_clean_ax.set_ylim(y_min - pad, y_max + pad)
    elif fitter.energy_mev is not None and fitter.energy_mev.size:
        plot.full_clean_ax.set_ylim(float(fitter.energy_mev.min()), float(fitter.energy_mev.max()))

    if clean_lines:
        plot.clean_ax.legend(loc="best", fontsize="small")
        plot.full_clean_ax.legend(loc="best", fontsize="small")
    plot.clean_canvas.draw_idle()
    plot.full_clean_canvas.draw_idle()
