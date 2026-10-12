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
dv_mesure = 0.002

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
m_bluerov = 11.1
V_bluerov = 0.011_665_000

#Cordes d'attache blueROV + Mousqueton
m_attache = 0.0 #DEJA COMPTé DANS m_BlueROV
dv_attache = 0.109 - 0.1009
V_attache = S_cyl * dv_attache


#### Cylindre_MASSES ####

m_totale = 3.393

#Tap_haut
V_taphaut = 0.000_110_200

#tap_bas + cache
V_tapbas = 0.000_110_100
V_cachebas = 0.000_130_800

#TubePVC
d_ext_tube = 0.125
V_tube = 0.000_881_000

#Corde + Mousqueton
L_mousq = 1
d_mousq = 0.004
V_mousq = 0.000_015 + L_mousq * pi * d_mousq**2 / 4

#Tigesfiletés + ecrous
V_tige = 0.000_221_215_3

#HALTèRES
#1
m_h1 = 0.530

dv_h1 = 0.0666 - 0.0615
V_h1 = S_cyl * dv_h1

#Cordes
m_cordes = 0.4913

d_cordes = 0.004
L_cordes = 0

V_cordes = L_cordes * pi * d_cordes**2 / 4

#touret + Mousquetons
d_touret = 0.004
L_touret = 0

m_mousqueton = 0.1
V_mousqueton = 0.000_015

#RESOLUTION DU PFS


def calculer_trainee(v_r, essai_haltere, L_touret=0):
    """Retourne la traînée en N (v_r en m/s, L_touret en m)."""
    m_touret = m_mousqueton + 0.012 * L_touret
    V_touret = V_mousqueton + L_touret * pi * d_touret**2 / 4

    Volumes = V_bluerov + V_attache + V_tapbas + V_tube + V_mousq + V_tige + V_taphaut + V_cachebas + V_h1 * essai_haltere + V_cordes + V_touret
    Archimède = rho * g * Volumes

    Masses = m_bluerov + m_attache + m_totale + m_h1 * essai_haltere + m_cordes + m_touret
    Poids = g * Masses

    F_drag_cylindre = 1/2 * rho * C_d_tube * (pi * d_ext_tube**2 / 4) * v_r**2

    return Poids - Archimède - F_drag_cylindre


if __name__ == "__main__":
    F_drag_bluerov = calculer_trainee(v_r, essai_haltere, L_touret)
    print("Force de trainée =", F_drag_bluerov, "N")
