# Audit des poids : 1 et 12 halteres

Diagnostic sans modification des scripts de traitement.

Parametres verifies : cible yaw = 0 deg, pitch = -90 deg, Theta0_deg = 15, Poids_min = 0.05.
Les intervalles ont ete redetectes depuis les six fichiers IMU/BAR30. Les listes v_r, L_touret et d obtenues correspondent exactement aux listes de 2repet.py pour ces deux groupes.
Les d ont aussi ete recalcules independamment par atan2(sin(delta), cos(delta)) : concordance a la precision exportee (0.001 deg).

d est un ecart RMS a la cible : il comprend le decalage constant et les fluctuations. W = somme(w_i^2) / somme(w_i) porte sur les intervalles retenus, sans ponderation par leur duree.

## 1 haltere(s)

Score du groupe W : 0.308995. Moyenne simple des poids : 0.175203.

| Fichier | Intervalle (s) | RMS yaw (deg) | RMS pitch (deg) | d (deg) | w_i | Contribution a la moyenne |
|---|---:|---:|---:|---:|---:|---:|
| 1v1 | 52.054-55.224 | 36.570 | 3.639 | 36.750 | 0.050000 | 7.13 % |
| 1v2 | 60.996-63.006 | 27.856 | 2.514 | 27.970 | 0.175795 | 25.08 % |
| 1v2 | 63.009-65.429 | 19.160 | 4.234 | 19.622 | 0.425033 | 60.65 % |
| 1v3 | 46.846-48.955 | 102.665 | 3.271 | 102.717 | 0.050000 | 7.13 % |

| Fichier / debut (s) | Ecart type yaw deroule (deg) | Ecart type roll+yaw deroule (deg) | Yaw exactement nul |
|---|---:|---:|---:|
| 1v1 / 52.054 | 25.449 | 2.175 | 0.00 % |
| 1v2 / 60.996 | 12.648 | 3.579 | 13.28 % |
| 1v2 / 63.009 | 9.696 | 0.963 | 20.34 % |
| 1v3 / 46.846 | 35.531 | 1.263 | 0.00 % |

## 12 haltere(s)

Score du groupe W : 0.185086. Moyenne simple des poids : 0.094834.

| Fichier | Intervalle (s) | RMS yaw (deg) | RMS pitch (deg) | d (deg) | w_i | Contribution a la moyenne |
|---|---:|---:|---:|---:|---:|---:|
| 12v1 | 13.416-15.718 | 41.059 | 3.394 | 41.199 | 0.050000 | 7.53 % |
| 12v1 | 18.247-21.029 | 68.304 | 3.738 | 68.407 | 0.050000 | 7.53 % |
| 12v1 | 21.036-24.048 | 47.311 | 3.245 | 47.422 | 0.050000 | 7.53 % |
| 12v2 | 14.393-16.888 | 32.354 | 3.024 | 32.495 | 0.095701 | 14.42 % |
| 12v2 | 16.962-20.505 | 48.555 | 4.110 | 48.729 | 0.050000 | 7.53 % |
| 12v2 | 21.427-23.452 | 22.515 | 2.908 | 22.702 | 0.318119 | 47.92 % |
| 12v3 | 20.149-23.190 | 105.631 | 2.180 | 105.654 | 0.050000 | 7.53 % |

| Fichier / debut (s) | Ecart type yaw deroule (deg) | Ecart type roll+yaw deroule (deg) | Yaw exactement nul |
|---|---:|---:|---:|
| 12v1 / 13.416 | 21.282 | 3.126 | 0.00 % |
| 12v1 / 18.247 | 20.871 | 5.741 | 0.00 % |
| 12v1 / 21.036 | 18.422 | 4.517 | 3.07 % |
| 12v2 / 14.393 | 30.734 | 1.292 | 6.95 % |
| 12v2 / 16.962 | 22.884 | 2.798 | 0.00 % |
| 12v2 / 21.427 | 20.206 | 1.400 | 10.97 % |
| 12v3 / 20.149 | 49.936 | 8.636 | 3.47 % |

## Interpretation

- Le filtre de selection limite deja le pitch a -90 +/- 6 deg. Les portions avec un decalage plus grand sont exclues avant la ponderation.
- Le yaw contribue a plus de 95 % de d^2 dans chacun des 11 intervalles retenus. Le poids est donc presque entierement determine par le yaw.
- A 1 haltere, la portion 1v2 de 63.009 a 65.429 s represente 60.65 % de la moyenne ponderee. Elle ne suffit pas a qualifier toute la descente.
- Pres de -90 deg, la convention Euler usuelle presente une singularite (gimbal lock). La compensation roll/yaw observee est compatible avec cette limite, sans suffire a identifier le traitement exact du logiciel acquisition.
- Le yaw nul pendant certaines portions proches de -90 deg doit etre verifie dans le code acquisition. attitude_ok vaut True sur tous les echantillons retenus ; cela ne garantit pas que le yaw isole soit un indicateur physique fiable.
- Corriger la periodicite de 360 deg ne supprime pas cette singularite.

Reference : https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.transform.Rotation.as_euler.html

## Figures

[Comparaison par intervalle](comparaison_1_12.png)

[Angles bruts et intervalles retenus](angles_bruts_intervalles.png)
