from math import pi

#Unité SI : Masses en Kg, Volume en m^3, forces en N, Vitesse en m/s

#Constantes environnement
rho = 1024
g = 9.81

#Fluides
v_r = 0.77 #VITESSE RELATIVE
essai_haltere = 1
C_d_tube = 0.889

#CALCUL VOLUME AVEC Cylindre
d_cyl = 0.1524
S_cyl = pi * d_cyl**2 / 4

###################################
#INCERTITUDES

#mesures volume cylindre
dv_mesure = 0.002 #à appliquer sur le dv_ pas sur le Volume

#Volumes CAO
dv_cao = 0.000_001 #1cm^3

#BALANCES masse_small
dm_small = 0.001

#BALANCES masse_big
dm_big = 0.1

###################################

###################################
#CALCULS

#BlueROV2
m_bluerov = 11.1  #balance masse_big
V_bluerov = 0.011_665_000 #volumeCAO

#Cordes d'attache blueROV + Mousqueton
m_attache = 0.0 #DEJA COMPTé DANS m_BlueROV
dv_attache = 0.109 - 0.1009 #mesure volume cylindre
V_attache = S_cyl * dv_attache


#### Cylindre_MASSES ####

m_totale = 3.393 #balance masse_big

#Tap_haut
V_taphaut = 0.000_110_200 #volumeCAO

#tap_bas + cache
V_tapbas = 0.000_110_100 #VolumeCAO
V_cachebas = 0.000_130_800  #VolumeCAO

#TubePVC
d_ext_tube = 0.125
V_tube = 0.000_881_000 #VolumeCAO


#Corde + Mousqueton
L_mousq = 1
d_mousq = 0.004
V_mousq = 0.000_015 + L_mousq * pi * d_mousq**2 / 4 #VOLUME CAO

#Tigesfiletés + ecrous
V_tige = 0.000_221_215_3  #VolumeCAO


#HALTèRES
#1
m_h1 = 0.530

dv_h1 = 0.0666 - 0.0615 #mesure volume cylindre
V_h1 = S_cyl * dv_h1

#Cordes
m_cordes = 0.4913

d_cordes = 0.004
L_cordes = 0

V_cordes = L_cordes * pi * d_cordes**2 / 4 #VolumeCAO

#touret + Mousquetons
d_touret = 0.004
L_touret = 0

m_mousqueton = 0.1
V_mousqueton = 0.000_015 #Volume CAO

#RESOLUTION DU PFS


def calculer_trainee(v_r, essai_haltere, L_touret=0, incertitudes=False):
    """Retourne la traînée en N, ou (nominale, min, max) avec incertitudes."""
    m_touret = m_mousqueton + 0.012 * L_touret
    V_touret = V_mousqueton + L_touret * pi * d_touret**2 / 4

    Volumes = V_bluerov + V_attache + V_tapbas + V_tube + V_mousq + V_tige + V_taphaut + V_cachebas + V_h1 * essai_haltere + V_cordes + V_touret
    Archimède = rho * g * Volumes

    Masses = m_bluerov + m_attache + m_totale + m_h1 * essai_haltere + m_cordes + m_touret
    Poids = g * Masses

    F_drag_cylindre = 1/2 * rho * C_d_tube * (pi * d_ext_tube**2 / 4) * v_r**2

    F_drag = Poids - Archimède - F_drag_cylindre
    if not incertitudes:
        return F_drag

    # Deux pesées sur la grosse balance ; haltères, cordes et mousqueton
    # sur la petite. L'attache est déjà incluse dans la masse du BlueROV.
    dm = 2 * dm_big + (essai_haltere + 2) * dm_small
    Poids_min = g * (Masses - dm)
    Poids_max = g * (Masses + dm)

    # Huit volumes CAO : BlueROV, deux taps, cache, tube, mousq, tige,
    # mousqueton du touret. Pas d'incertitude ajoutée aux cordes absentes.
    dV = (8 + (L_cordes > 0)) * dv_cao
    dV += S_cyl * dv_mesure * (1 + essai_haltere)
    Archimede_min = rho * g * (Volumes - dV)
    Archimede_max = rho * g * (Volumes + dV)

    F_drag_min = Poids_min - Archimede_max - F_drag_cylindre
    F_drag_max = Poids_max - Archimede_min - F_drag_cylindre
    return F_drag, F_drag_min, F_drag_max


if __name__ == "__main__":
    F_drag_bluerov, F_drag_min, F_drag_max = calculer_trainee(
        v_r, essai_haltere, L_touret, incertitudes=True
    )
    print("Force de trainée =", F_drag_bluerov, "N")
    print("Force de trainée min =", F_drag_min, "N")
    print("Force de trainée max =", F_drag_max, "N")
