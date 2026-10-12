from math import pi

#Unité SI : Masses en Kg, Volume en m^3, forces en N, Vitesse en m/s

#Constantes environnement
rho = 1024
g = 9.81

#Fluides
v_r = 0.57 #VITESSE RELATIVE
essai_haltere = 1
C_d_tube = 0.889

#Incertitudes 

	#VOLUMES
dV_Fusion = 0.03 #% pourcentage de variation entre CAO et réalité

dV_mesure = 0.0005 #m Incertitude sur la mesure de la hauteur d'eau dans un déplacement

	#MASSES
dm_lourd = 0.1 #kg résolution de la grosse balance

dm_leger = 0.001 #kg résolution de la petite balance

dm_haltere =  0.03 #kg variation de poids d'une haltère

#BlueROV2
m_bluerov = 11.1
V_bluerov = 0.011_665_000

#Cylindre_MASSES

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
V_h1 = 0.000_093_030

#Cordes
m_cordes = 0

d_cordes = 0.004
L_cordes = 0

V_cordes = L_cordes * pi * d_cordes**2 / 4

#touret + Mousquetons
d_touret = 0.004
L_touret = 0

m_mousqueton = 0.1
V_mousqueton = 0.000_015

m_touret = m_mousqueton + 0.45 * L_touret
V_touret = V_mousqueton + L_touret * pi * d_touret**2 / 4

#RESOLUTION DU PFS


def calculer_trainee(v_r, essai_haltere):
    """Retourne la traînée du BlueROV en N (v_r en m/s, nombre d'haltères)."""
    Volumes = V_bluerov + V_tapbas + V_tube + V_mousq + V_tige + V_taphaut + V_cachebas + V_h1 * essai_haltere + V_cordes + V_touret
    Archimède = rho * g * Volumes

    Masses = m_bluerov + m_totale + m_h1 * essai_haltere + m_cordes + m_touret
    Poids = g * Masses

    F_drag_cylindre = 1/2 * rho * C_d_tube * (pi * d_ext_tube**2 / 4) * v_r**2

    return Poids - Archimède - F_drag_cylindre


if __name__ == "__main__":
    F_drag_bluerov = calculer_trainee(v_r, essai_haltere)
    print("Force de trainée =", F_drag_bluerov, "N")
