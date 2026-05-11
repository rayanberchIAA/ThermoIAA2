"""
==============================================================================
calculations.py — Moteur de calculs thermodynamiques
==============================================================================
Application : Refroidissement & Congélation d'un produit alimentaire
Niveau      : Ingénierie agroalimentaire (IAA)
Auteurs     : Projet Thermodynamique Appliquée
==============================================================================

Equations de référence
──────────────────────
1. Chaleur sensible (refroidissement seul)
       Q_sensible = m · cp · ΔT                [kJ]

2. Chaleur latente de congélation
       Q_latente = m · w_eau · L_cong          [kJ]
   où w_eau = fraction d'eau congelable

3. Chaleur sensible après congélation
       Q_post = m · cp_congelé · (T_cong - T_finale)   [kJ]

4. Énergie totale à extraire
       Q_totale = Q_sensible + Q_latente + Q_post       [kJ]

5. Puissance frigorifique utile
       P_utile = Q_totale / (durée × 3600)              [kW]

6. Puissance électrique absorbée
       P_elec = P_utile / COP                           [kW]

7. Énergie électrique consommée
       E_elec = P_elec × durée                          [kWh]

8. Coût énergétique
       Coût = E_elec × prix_elec                        [MAD]

9. Coût par kg de produit
       Coût_kg = Coût / masse                           [MAD/kg]

10. Temps minimal si puissance imposée
       t_min = Q_totale / (P_frigo_dispo × 3600)        [h]
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Structures de données d'entrée
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ParamsRefroidissement:
    """Paramètres d'entrée pour le calcul de refroidissement simple."""
    masse: float          # [kg]        masse du produit
    T_initiale: float     # [°C]        température initiale du produit
    T_finale: float       # [°C]        température finale souhaitée
    cp_produit: float     # [kJ/kg·K]   chaleur massique du produit
    duree: float          # [h]         durée souhaitée de refroidissement
    COP: float            # [-]         coefficient de performance de la machine
    prix_elec: float      # [MAD/kWh]    prix de l'électricité
    nb_operations: int    # [-]         nombre d'opérations par jour
    nb_jours: int         # [-]         nombre de jours de fonctionnement/an


@dataclass
class ParamsCongélation(ParamsRefroidissement):
    """Paramètres supplémentaires pour le calcul de congélation."""
    T_congelation: float  # [°C]        température de début de congélation
    cp_congele: float     # [kJ/kg·K]   chaleur massique du produit congelé
    L_congelation: float  # [kJ/kg]     chaleur latente de congélation
    fraction_eau: float   # [-]         fraction d'eau congelable (0–1)
    P_frigo_dispo: Optional[float] = None  # [kW] puissance disponible (optionnel)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Bilans thermodynamiques — Refroidissement simple
# ─────────────────────────────────────────────────────────────────────────────

def bilan_refroidissement(p: ParamsRefroidissement) -> dict:
    """
    Calcule le bilan énergétique pour un refroidissement simple (sans changement d'état).

    Retourne un dictionnaire avec tous les résultats intermédiaires et finaux.
    """
    delta_T = p.T_initiale - p.T_finale          # ΔT [K] — différence de température

    # Chaleur à extraire — Éq. 1
    Q_utile = p.masse * p.cp_produit * delta_T   # [kJ]

    # Puissance frigorifique utile — Éq. 5
    P_utile = Q_utile / (p.duree * 3600)         # [kW]

    # Puissance électrique absorbée — Éq. 6
    P_elec = P_utile / p.COP                     # [kW]

    # Énergie électrique consommée — Éq. 7
    E_elec = P_elec * p.duree                    # [kWh]

    # Coûts — Éq. 8 & 9
    cout_operation = E_elec * p.prix_elec                         # [MAD/opération]
    cout_kg        = cout_operation / p.masse                     # [MAD/kg]
    cout_journalier = cout_operation * p.nb_operations            # [MAD/jour]
    cout_mensuel    = cout_journalier * (p.nb_jours / 12)        # [MAD/mois]
    cout_annuel     = cout_journalier * p.nb_jours               # [MAD/an]

    return {
        # ─ Bilan matière ─
        "masse_kg"           : p.masse,
        # ─ Bilan énergétique ─
        "delta_T_K"          : delta_T,
        "Q_sensible_kJ"      : Q_utile,
        "Q_latente_kJ"       : 0.0,
        "Q_post_kJ"          : 0.0,
        "Q_totale_kJ"        : Q_utile,
        "Q_totale_kWh"       : Q_utile / 3600,
        # ─ Puissances ─
        "P_utile_kW"         : P_utile,
        "P_elec_kW"          : P_elec,
        # ─ Consommation ─
        "E_elec_kWh"         : E_elec,
        # ─ Coûts ─
        "cout_operation"     : cout_operation,
        "cout_kg"            : cout_kg,
        "cout_journalier"    : cout_journalier,
        "cout_mensuel"       : cout_mensuel,
        "cout_annuel"        : cout_annuel,
        # ─ Indicateurs ─
        "mode"               : "Refroidissement simple",
        "COP"                : p.COP,
        "duree_h"            : p.duree,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Bilans thermodynamiques — Congélation complète
# ─────────────────────────────────────────────────────────────────────────────

def bilan_congelation(p: ParamsCongélation) -> dict:
    """
    Calcule le bilan énergétique pour une congélation complète (3 étapes) :
      Phase 1 : refroidissement de T_ini à T_cong   (chaleur sensible, produit frais)
      Phase 2 : solidification à T_cong             (chaleur latente)
      Phase 3 : refroidissement de T_cong à T_fin   (chaleur sensible, produit congelé)
    """
    # ── Phase 1 : chaleur sensible avant congélation ──────────────────────
    dT1 = p.T_initiale - p.T_congelation             # ΔT phase 1 [K]
    Q1  = p.masse * p.cp_produit * dT1               # [kJ]

    # ── Phase 2 : chaleur latente de congélation ──────────────────────────
    Q2  = p.masse * p.fraction_eau * p.L_congelation  # [kJ]

    # ── Phase 3 : chaleur sensible après congélation ──────────────────────
    dT3 = p.T_congelation - p.T_finale               # ΔT phase 3 [K]
    Q3  = p.masse * p.cp_congele * dT3               # [kJ]

    # ── Bilan total ────────────────────────────────────────────────────────
    Q_totale = Q1 + Q2 + Q3                           # [kJ]

    # ── Puissance frigorifique utile ──────────────────────────────────────
    P_utile = Q_totale / (p.duree * 3600)             # [kW]

    # ── Machine frigorifique ───────────────────────────────────────────────
    P_elec = P_utile / p.COP                          # [kW]
    E_elec = P_elec * p.duree                         # [kWh]

    # ── Temps minimal si puissance dispo imposée ──────────────────────────
    if p.P_frigo_dispo and p.P_frigo_dispo > 0:
        t_min_h = Q_totale / (p.P_frigo_dispo * 3600)
    else:
        t_min_h = None

    # ── Coûts ─────────────────────────────────────────────────────────────
    cout_operation  = E_elec * p.prix_elec
    cout_kg         = cout_operation / p.masse
    cout_journalier = cout_operation * p.nb_operations
    cout_mensuel    = cout_journalier * (p.nb_jours / 12)
    cout_annuel     = cout_journalier * p.nb_jours

    return {
        # ─ Bilan matière ─
        "masse_kg"            : p.masse,
        # ─ Bilan énergétique détaillé ─
        "Q_sensible_kJ"       : Q1,
        "Q_latente_kJ"        : Q2,
        "Q_post_kJ"           : Q3,
        "Q_totale_kJ"         : Q_totale,
        "Q_totale_kWh"        : Q_totale / 3600,
        "part_sensible_pct"   : 100 * Q1 / Q_totale if Q_totale > 0 else 0,
        "part_latente_pct"    : 100 * Q2 / Q_totale if Q_totale > 0 else 0,
        "part_post_pct"       : 100 * Q3 / Q_totale if Q_totale > 0 else 0,
        # ─ Puissances ─
        "P_utile_kW"          : P_utile,
        "P_elec_kW"           : P_elec,
        # ─ Consommation ─
        "E_elec_kWh"          : E_elec,
        # ─ Temps minimal ─
        "t_min_h"             : t_min_h,
        # ─ Coûts ─
        "cout_operation"      : cout_operation,
        "cout_kg"             : cout_kg,
        "cout_journalier"     : cout_journalier,
        "cout_mensuel"        : cout_mensuel,
        "cout_annuel"         : cout_annuel,
        # ─ Meta ─
        "mode"                : "Congélation complète",
        "COP"                 : p.COP,
        "duree_h"             : p.duree,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Analyse de sensibilité — variation d'un paramètre
# ─────────────────────────────────────────────────────────────────────────────

def sensibilite_COP(p: ParamsCongélation, cops: np.ndarray) -> pd.DataFrame:
    """Fait varier le COP et retourne les métriques clés."""
    rows = []
    for cop in cops:
        p_tmp = ParamsCongélation(**{**p.__dict__, "COP": cop})
        r = bilan_congelation(p_tmp)
        rows.append({
            "COP"             : cop,
            "P_elec_kW"       : r["P_elec_kW"],
            "E_elec_kWh"      : r["E_elec_kWh"],
            "Coût/opération (MAD)": r["cout_operation"],
            "Coût annuel (MAD)" : r["cout_annuel"],
        })
    return pd.DataFrame(rows)


def sensibilite_T_finale(p: ParamsCongélation, temperatures: np.ndarray) -> pd.DataFrame:
    """Fait varier la température finale et retourne les métriques clés."""
    rows = []
    for T in temperatures:
        if T >= p.T_congelation:  # refroidissement seul
            p_tmp = ParamsRefroidissement(
                masse=p.masse, T_initiale=p.T_initiale, T_finale=T,
                cp_produit=p.cp_produit, duree=p.duree, COP=p.COP,
                prix_elec=p.prix_elec,
                nb_operations=p.nb_operations, nb_jours=p.nb_jours
            )
            r = bilan_refroidissement(p_tmp)
        else:
            p_tmp = ParamsCongélation(**{**p.__dict__, "T_finale": T})
            r = bilan_congelation(p_tmp)
        rows.append({
            "T_finale (°C)"   : T,
            "Q_totale_kJ"     : r["Q_totale_kJ"],
            "P_utile_kW"      : r["P_utile_kW"],
            "E_elec_kWh"      : r["E_elec_kWh"],
            "Coût/opération (MAD)": r["cout_operation"],
        })
    return pd.DataFrame(rows)


def sensibilite_masse(p: ParamsCongélation, masses: np.ndarray) -> pd.DataFrame:
    """Fait varier la masse du produit et retourne les métriques clés."""
    rows = []
    for m in masses:
        p_tmp = ParamsCongélation(**{**p.__dict__, "masse": m})
        r = bilan_congelation(p_tmp)
        rows.append({
            "Masse (kg)"      : m,
            "Q_totale_kJ"     : r["Q_totale_kJ"],
            "P_utile_kW"      : r["P_utile_kW"],
            "E_elec_kWh"      : r["E_elec_kWh"],
            "Coût/opération (MAD)": r["cout_operation"],
        })
    return pd.DataFrame(rows)


def sensibilite_prix_elec(p: ParamsCongélation, prix: np.ndarray) -> pd.DataFrame:
    """Fait varier le prix de l'électricité et retourne les coûts."""
    rows = []
    r_base = bilan_congelation(p)
    for px in prix:
        cout_op = r_base["E_elec_kWh"] * px
        rows.append({
            "Prix élec (MAD/kWh)" : px,
            "Coût/opération (MAD)": cout_op,
            "Coût annuel (MAD)"   : cout_op * p.nb_operations * p.nb_jours,
        })
    return pd.DataFrame(rows)


def sensibilite_duree(p: ParamsCongélation, durees: np.ndarray) -> pd.DataFrame:
    """Fait varier la durée de traitement et retourne la puissance nécessaire."""
    rows = []
    for d in durees:
        p_tmp = ParamsCongélation(**{**p.__dict__, "duree": d})
        r = bilan_congelation(p_tmp)
        rows.append({
            "Durée (h)"       : d,
            "P_utile_kW"      : r["P_utile_kW"],
            "P_elec_kW"       : r["P_elec_kW"],
            "E_elec_kWh"      : r["E_elec_kWh"],
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Comparaison de scénarios
# ─────────────────────────────────────────────────────────────────────────────

def comparer_scenarios(scenarios: list[dict]) -> pd.DataFrame:
    """
    Compare plusieurs scénarios décrits comme des dictionnaires.
    Chaque dict doit contenir 'nom', 'mode' ('refroid' ou 'congelation'),
    et les champs d'un ParamsRefroidissement ou ParamsCongélation.
    """
    rows = []
    for sc in scenarios:
        nom  = sc.pop("nom")
        mode = sc.pop("mode")
        if mode == "refroid":
            p = ParamsRefroidissement(**sc)
            r = bilan_refroidissement(p)
        else:
            p = ParamsCongélation(**sc)
            r = bilan_congelation(p)
        rows.append({
            "Scénario"              : nom,
            "Mode"                  : r["mode"],
            "Q totale (kJ)"         : round(r["Q_totale_kJ"], 1),
            "P utile (kW)"          : round(r["P_utile_kW"], 2),
            "P électrique (kW)"     : round(r["P_elec_kW"], 2),
            "E électrique (kWh)"    : round(r["E_elec_kWh"], 2),
            "COP"                   : r["COP"],
            "Coût/opération (MAD)"    : round(r["cout_operation"], 2),
            "Coût/kg (MAD)"           : round(r["cout_kg"], 4),
            "Coût journalier (MAD)"   : round(r["cout_journalier"], 2),
            "Coût annuel (MAD)"       : round(r["cout_annuel"], 1),
        })
        # On remet les clés pour ne pas muter l'original (pop() modifie)
    df = pd.DataFrame(rows)
    # Recommandation automatique basée sur le coût annuel
    idx_min = df["Coût annuel (MAD)"].idxmin()
    df["Recommandé"] = "—"
    df.loc[idx_min, "Recommandé"] = "✅ Optimal"
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Profil temporel de refroidissement (courbe de température)
# ─────────────────────────────────────────────────────────────────────────────

def profil_temperature(
    T_ini: float, T_cong: float, T_fin: float,
    duree_h: float, n_points: int = 200
) -> pd.DataFrame:
    """
    Génère un profil de température simplifié (loi exponentielle + palier
    de changement d'état) pour la visualisation graphique.
    """
    t = np.linspace(0, duree_h, n_points)
    T = np.zeros(n_points)

    # Fraction temporelle pour chaque phase
    has_congelation = T_fin < T_cong
    if has_congelation:
        f1 = 0.35   # fraction temps → phase 1 (refroid. sensible)
        f2 = 0.30   # fraction temps → phase 2 (palier congélation)
        f3 = 0.35   # fraction temps → phase 3 (refroid. congelé)
    else:
        f1 = 1.0
        f2 = 0.0
        f3 = 0.0

    t1_end = duree_h * f1
    t2_end = duree_h * (f1 + f2)

    for i, ti in enumerate(t):
        if ti <= t1_end:
            # Phase 1 : décroissance exponentielle vers T_cong
            alpha = 4.0 / t1_end if t1_end > 0 else 1e-6
            T[i] = T_cong + (T_ini - T_cong) * np.exp(-alpha * ti)
        elif has_congelation and ti <= t2_end:
            # Phase 2 : palier à T_cong (changement d'état)
            T[i] = T_cong
        else:
            # Phase 3 : décroissance exponentielle vers T_fin
            t_local = ti - t2_end
            t3_dur  = duree_h * f3 if f3 > 0 else 1e-6
            alpha   = 4.0 / t3_dur
            T[i] = T_fin + (T_cong - T_fin) * np.exp(-alpha * t_local)

    return pd.DataFrame({"Temps (h)": t, "Température (°C)": T})
