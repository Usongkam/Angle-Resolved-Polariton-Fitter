import numpy as np

J0 = 0.381e-4  # hbar^2/2m_e (meV*um^2)
HC_MEV_NM = 1239841.98  # hc (meV*nm)
HBAR_C_MEV_NM = HC_MEV_NM / (2 * np.pi)


def cavity_dispersion(k_um_inv, m_r, e0_mev, k_shift_um_inv=0.0):
    return e0_mev + J0 / m_r * ((k_um_inv - k_shift_um_inv) ** 2)


def polariton_branches(k_um_inv, m_r, e0_mev, g_mev, eex_mev, k_shift_um_inv=0.0):
    e_cav = cavity_dispersion(k_um_inv, m_r, e0_mev, k_shift_um_inv)
    delta = np.sqrt((e_cav - eex_mev) ** 2 + 4 * (g_mev**2))
    e_lp = 0.5 * (e_cav + eex_mev - delta)
    e_up = 0.5 * (e_cav + eex_mev + delta)
    return e_lp, e_up
