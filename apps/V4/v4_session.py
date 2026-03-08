import numpy as np


def parameter_tooltips():
    return {
        "smoothing": "骞虫粦寮哄害锛岀敤浜庤鍓墠鐨勮鍚戣疆寤撳钩婊戙€俓nSmoothing sigma used before crop detection.",
        "crop_mode": "瑁佸壀妯″紡銆侫uto 浣跨敤骞虫粦鍚庤竟缂樿嚜鍔ㄦ壘宸﹀彸杈圭晫锛汳anual 鍏佽鐩存帴杈撳叆杈圭晫骞跺湪 Raw 鍥炬嫋鍔ㄨ竟鐣岀嚎銆備慨鏀瑰悗闇€瑕佺偣 Apply 鐢熸晥銆俓nCrop mode. Auto detects crop edges from the smoothed angular profile; Manual uses explicit boundaries and supports dragging the crop lines in the Raw panel. Click Apply to commit changes.",
        "crop_padding": "鑷姩瑁佸壀鏃跺湪妫€娴嬪埌鐨勫乏鍙宠竟鐣屽棰濆淇濈暀鐨勫儚绱犳暟銆傚彧鍦?Auto 妯″紡涓嬬敓鏁堛€俓nExtra pixels kept outside the detected crop edges in Auto mode only.",
        "left_boundary": "鎵嬪姩瑁佸壀宸﹁竟鐣岋紝鍗曚綅涓哄師濮嬫í鍚戠储寮曘€侻anual 妯″紡涓嬩篃鍙湪 Raw 鍥剧洿鎺ユ嫋宸︿晶铏氱嚎銆備慨鏀瑰悗闇€瑕佺偣 Apply 鐢熸晥銆俓nLeft crop boundary in raw horizontal index. In Manual mode you can also drag the left dashed line in the Raw panel. Click Apply to commit changes.",
        "right_boundary": "鎵嬪姩瑁佸壀鍙宠竟鐣岋紝鍗曚綅涓哄師濮嬫í鍚戠储寮曘€侻anual 妯″紡涓嬩篃鍙湪 Raw 鍥剧洿鎺ユ嫋鍙充晶铏氱嚎銆備慨鏀瑰悗闇€瑕佺偣 Apply 鐢熸晥銆俓nRight crop boundary in raw horizontal index. In Manual mode you can also drag the right dashed line in the Raw panel. Click Apply to commit changes.",
        "na": "鐗╅暅鏁板€煎瓟寰勶紝鐢ㄤ簬鍍忕礌鍒拌搴︾殑鏄犲皠銆俓nObjective numerical aperture for pixel-to-angle mapping.",
        "k0": "瑁佸壀鍚?k=0 鐨勫儚绱犵储寮曘€俓nPixel index of k=0 inside the cropped matrix.",
        "feature": "閫夋嫨杩借釜璋峰€兼垨宄板€笺€傚弽灏勯€?dip锛孭L 閫?peak銆俓nChoose whether tracing follows dips or peaks.",
        "fit_mode": "閫夋嫨鍚庣画鎷熷悎妯″瀷銆侰oupled=LP+UP锛孡P only=浠呬笅鏀紝Cavity only=浠呰厰妯°€俓nChoose the fitting model used later.",
        "search_px": "姣忎竴姝ュ湪鑳介噺杞撮檮杩戞悳绱㈡瀬鍊肩殑绐楀彛鍗婂銆俓nHalf-width of the local search window along energy.",
        "prominence": "鑷姩寤剁敵鏃舵瀬鍊兼樉钁楁€ч槇鍊硷紝瓒婂ぇ瓒婁弗鏍笺€俓nProminence threshold for auto-tracing; larger is stricter.",
        "max_miss": "鍏佽杩炵画杩借釜澶辫触鐨勬渶澶ф鏁帮紝杈惧埌鍚庡仠姝㈠欢鐢炽€俓nMaximum consecutive misses before tracing stops.",
        "mr": "鐩稿鏈夋晥璐ㄩ噺锛屽崟浣嶄负鑷敱鐢靛瓙璐ㄩ噺 m_0銆俓nRelative effective mass in units of free-electron mass m_0.",
        "e0": "k=0 澶勭殑鑵旀ā鑳介噺锛屽崟浣?meV銆俓nCavity energy at k=0, in meV.",
        "kshift": "k 绌洪棿妯悜骞崇Щ锛岀敤浜庝慨姝?k=0 杞诲井鍋忕Щ锛屽崟浣?um^-1銆俓nHorizontal k-shift that corrects a small k=0 offset, in um^-1.",
        "g": "鑰﹀悎寮哄害 / Rabi 鍒嗚鐨勪竴鍗婏紝鍗曚綅 meV銆俓nCoupling strength (half Rabi splitting), in meV.",
        "eex": "婵€瀛愯兘閲忥紝鍗曚綅 meV銆俓nExciton energy, in meV.",
    }


def material_presets():
    return {
        "Generic": {"Eex": None, "g": None},
        "Perovskite / CsPbBr3": {"Eex": 2407.0, "g": 64.0},
        "Perovskite / FAPbBr3 (seed)": {"Eex": 2250.0, "g": 60.0},
        "TMD / WSe2 monolayer": {"Eex": 1650.0, "g": 11.75},
        "Magnetic / CrSBr": {"Eex": 1760.0, "g": 186.0},
        "Keep current values": {"Eex": None, "g": None},
    }


def reset_session_panel_text():
    return {
        "headline": "No fit executed.",
        "metrics": "Metrics: --",
        "params": "Params: --",
        "export": "Export: --",
    }


def format_fit_summary(summary, params):
    if not params:
        return summary
    lines = [summary, "", "Parameters:"]
    if "m_r" in params:
        lines.append(f"m_r / m_0 = {params['m_r']:.3e}")
    if "E0" in params:
        lines.append(f"E0 = {params['E0']:.4f} meV")
    if "k_shift" in params:
        lines.append(f"k_shift = {params['k_shift']:.4f} um^-1")
    if "g" in params:
        lines.append(f"g = {params['g']:.4f} meV")
    if "Eex" in params:
        lines.append(f"Eex = {params['Eex']:.4f} meV")
    return "\n".join(lines)


def build_session_panel_text(fitter, branch_points, mode_text, export_text):
    point_counts = f"Points C/LP/UP: {len(branch_points['cavity'])}/{len(branch_points['lp'])}/{len(branch_points['up'])}"
    fit_summary = fitter.fit_summary.text or ""
    params = fitter.fit_params
    if params:
        diagnostics = fitter.last_fit.get("diagnostics", {})
        headline = fit_summary.splitlines()[0] if fit_summary else f"Fit completed | mode: {mode_text}"
        metrics_lines = [
            f"RMSE: {np.sqrt(np.mean(np.asarray(fitter.last_fit.get('residual', []), dtype=np.float64) ** 2)):.3f}" if fitter.last_fit.get("residual") is not None and len(fitter.last_fit.get("residual", [])) else "RMSE: --",
            f"Weighted RMSE: {diagnostics.get('weighted_rmse', float('nan')):.3f}" if diagnostics else "Weighted RMSE: --",
            f"LP RMSE: {diagnostics.get('lp_rmse', float('nan')):.3f}" if diagnostics.get('lp_rmse') is not None else "LP RMSE: --",
            f"UP RMSE: {diagnostics.get('up_rmse', float('nan')):.3f}" if diagnostics.get('up_rmse') is not None else "UP RMSE: --",
            f"Outliers: {100.0 * diagnostics.get('outlier_fraction', 0.0):.1f}%" if diagnostics else "Outliers: --",
            f"Bounds: {', '.join(diagnostics.get('bound_hits', [])) if diagnostics.get('bound_hits') else 'none'}" if diagnostics else "Bounds: --",
        ]
        param_lines = [f"Mode: {mode_text}", point_counts]
        if "m_r" in params:
            param_lines.append(f"m_r / m_0: {params['m_r']:.3e}")
        if "E0" in params:
            param_lines.append(f"E0: {params['E0']:.4f} meV")
        if "k_shift" in params:
            param_lines.append(f"k_shift: {params['k_shift']:.4f} um^-1")
        if "g" in params:
            param_lines.append(f"g: {params['g']:.4f} meV")
        if "Eex" in params:
            param_lines.append(f"Eex: {params['Eex']:.4f} meV")
        return {
            "headline": headline,
            "metrics": "\n".join(metrics_lines),
            "params": "\n".join(param_lines),
            "export": export_text,
        }

    if fit_summary:
        headline = fit_summary.splitlines()[0]
    elif fitter.intensity_matrix is None:
        headline = "No fit executed."
    elif any(branch_points.values()):
        headline = f"Ready to fit | mode: {mode_text}"
    else:
        headline = "Processed. Ready for tracing."

    return {
        "headline": headline,
        "metrics": "RMSE: --\nWeighted RMSE: --\nLP RMSE: --\nUP RMSE: --\nOutliers: --\nBounds: --",
        "params": f"Mode: {mode_text}\n{point_counts}\nParams: --",
        "export": export_text,
    }

