"""
==============================================================================
utils.py — Utilitaires : interprétation, export, mise en forme
==============================================================================
"""

import io
import math
import datetime
import os
import re
import warnings
from pathlib import Path

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# 1.  Interprétation automatique des résultats
# ─────────────────────────────────────────────────────────────────────────────

def interpreter_resultats(r: dict, mode: str) -> list[str]:
    """
    Génère une liste de phrases d'analyse technique & économique
    à partir du dictionnaire de résultats.
    """
    textes = []
    q = r["Q_totale_kJ"]
    p_utile = r["P_utile_kW"]
    e_elec  = r["E_elec_kWh"]
    cout_op = r["cout_operation"]
    cout_kg = r["cout_kg"]
    cout_an = r["cout_annuel"]
    cop     = r["COP"]
    duree   = r["duree_h"]

    # ── Énergivore ou non ────────────────────────────────────────────────────
    if q > 500_000:
        textes.append(
            f"⚡ Le procédé est **fortement énergivore** : {q/1000:.1f} MJ "
            f"doivent être extraits par opération. Un équipement de forte puissance est requis."
        )
    elif q > 100_000:
        textes.append(
            f"🔶 Le procédé présente une **consommation énergétique modérée** : "
            f"{q/1000:.1f} MJ par opération."
        )
    else:
        textes.append(
            f"✅ La quantité de chaleur à extraire reste **raisonnable** : "
            f"{q:.0f} kJ par opération."
        )

    # ── Puissance requise ────────────────────────────────────────────────────
    if p_utile > 100:
        textes.append(
            f"🏭 La puissance frigorifique utile calculée ({p_utile:.1f} kW) "
            f"nécessite une **installation industrielle** de grande capacité."
        )
    elif p_utile > 20:
        textes.append(
            f"🔧 La puissance frigorifique utile ({p_utile:.1f} kW) correspond à "
            f"une **installation semi-industrielle** (chambre froide ou groupe froid dédié)."
        )
    else:
        textes.append(
            f"✅ La puissance frigorifique requise ({p_utile:.1f} kW) est compatible "
            f"avec une **installation compacte**."
        )

    # ── COP & efficacité énergétique ─────────────────────────────────────────
    if cop >= 4.0:
        textes.append(
            f"💚 Le COP = {cop:.1f} est **excellent** : la machine produit {cop:.1f} kJ "
            f"de froid pour chaque kJ d'électricité consommée — très efficiente."
        )
    elif cop >= 2.5:
        textes.append(
            f"🟡 Le COP = {cop:.1f} est **acceptable** pour une machine frigorifique "
            f"industrielle. Une modernisation de l'installation pourrait l'améliorer."
        )
    else:
        textes.append(
            f"🔴 Le COP = {cop:.1f} est **faible** — une machine plus performante "
            f"réduirait significativement la consommation électrique et les coûts."
        )

    # ── Coût par kg ──────────────────────────────────────────────────────────
    if cout_kg > 0.10:
        textes.append(
            f"💰 Le coût de {cout_kg:.4f} MAD/kg est **élevé**. Pour rester compétitif, "
            f"il est conseillé d'optimiser le COP ou de réduire la durée de traitement."
        )
    elif cout_kg > 0.03:
        textes.append(
            f"📊 Le coût de {cout_kg:.4f} MAD/kg est **dans la moyenne industrielle** "
            f"pour ce type de procédé."
        )
    else:
        textes.append(
            f"✅ Le coût de {cout_kg:.4f} MAD/kg est **compétitif** — le procédé est "
            f"économiquement rentable à cette échelle."
        )

    # ── Coût annuel ──────────────────────────────────────────────────────────
    textes.append(
        f"📅 Le coût de fonctionnement annuel estimé est de **{cout_an:,.0f} MAD/an** "
        f"— à intégrer dans l'analyse de rentabilité globale de l'unité."
    )

    # ── Répartition de l'énergie (congélation uniquement) ───────────────────
    if mode == "congelation" and r.get("Q_latente_kJ", 0) > 0:
        pct_lat = r.get("part_latente_pct", 0)
        pct_sen = r.get("part_sensible_pct", 0)
        pct_pst = r.get("part_post_pct", 0)
        textes.append(
            f"🧊 Répartition de l'énergie extraite : "
            f"**{pct_sen:.1f}% chaleur sensible** (avant congélation), "
            f"**{pct_lat:.1f}% chaleur latente** (changement d'état), "
            f"**{pct_pst:.1f}% refroidissement post-congélation**. "
            f"La chaleur latente est souvent la part dominante."
        )

    # ── Recommandations techniques ────────────────────────────────────────────
    textes.append(
        "🔑 **Recommandations :** Privilégier des machines frigorifiques à COP élevé, "
        "isoler thermiquement les parois des chambres froides, et optimiser le planning "
        "des cycles pour lisser la demande en puissance électrique."
    )

    return textes


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Recommandation automatique de scénario
# ─────────────────────────────────────────────────────────────────────────────

def recommander_scenario(df_comparaison: pd.DataFrame) -> str:
    """Retourne une phrase de recommandation basée sur le tableau comparatif."""
    if df_comparaison.empty:
        return "Aucun scénario disponible."
    idx = df_comparaison["Coût annuel (MAD)"].idxmin()
    sc_opt = df_comparaison.loc[idx, "Scénario"]
    cout_opt = df_comparaison.loc[idx, "Coût annuel (MAD)"]

    # Calcul de l'économie par rapport au plus coûteux
    cout_max = df_comparaison["Coût annuel (MAD)"].max()
    economie = cout_max - cout_opt
    economie_pct = 100 * economie / cout_max if cout_max > 0 else 0

    return (
        f"✅ **Scénario recommandé : {sc_opt}**. "
        f"Il présente le coût annuel le plus faible ({cout_opt:,.0f} MAD/an), "
        f"soit une économie de **{economie:,.0f} MAD ({economie_pct:.1f}%)** "
        f"par rapport au scénario le plus coûteux."
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Export Excel
# ─────────────────────────────────────────────────────────────────────────────

def exporter_excel(
    params: dict,
    resultats: dict,
    df_sensibilite: dict[str, pd.DataFrame],
    df_scenarios: pd.DataFrame,
    interpretations: list[str],
) -> bytes:
    """
    Génère un fichier Excel multi-feuilles conforme à la structure attendue
    (Données d'entrée / Calculs / Résultats / Analyse de sensibilité / Conclusion).
    Retourne les bytes du fichier .xlsx.
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:

        # ── Feuille 1 : Données d'entrée ─────────────────────────────────────
        df_input = pd.DataFrame(
            list(params.items()),
            columns=["Paramètre", "Valeur"]
        )
        df_input.to_excel(writer, sheet_name="Données d'entrée", index=False)

        # ── Feuille 2 : Calculs ───────────────────────────────────────────────
        calculs = {
            "Paramètre": [
                "Q sensible phase 1 (kJ)", "Q latente congélation (kJ)",
                "Q sensible phase 3 (kJ)", "Q totale (kJ)", "Q totale (kWh)",
                "Puissance utile (kW)", "Puissance électrique absorbée (kW)",
                "Énergie électrique consommée (kWh)",
            ],
            "Valeur": [
                round(resultats.get("Q_sensible_kJ", 0), 2),
                round(resultats.get("Q_latente_kJ", 0), 2),
                round(resultats.get("Q_post_kJ", 0), 2),
                round(resultats.get("Q_totale_kJ", 0), 2),
                round(resultats.get("Q_totale_kWh", 0), 4),
                round(resultats.get("P_utile_kW", 0), 3),
                round(resultats.get("P_elec_kW", 0), 3),
                round(resultats.get("E_elec_kWh", 0), 4),
            ],
            "Équation": [
                "m·cp·ΔT1", "m·w·L", "m·cp_c·ΔT3",
                "Q1+Q2+Q3", "Q_totale/3600",
                "Q/(durée·3600)", "P_utile/COP", "P_elec·durée",
            ],
        }
        pd.DataFrame(calculs).to_excel(writer, sheet_name="Calculs", index=False)

        # ── Feuille 3 : Résultats ─────────────────────────────────────────────
        res = {
            "Indicateur": [
                "Énergie utile (kJ)", "Puissance utile (kW)",
                "Énergie consommée (kWh)", "Coût/opération (MAD)",
                "Coût journalier (MAD)", "Coût mensuel (MAD)", "Coût annuel (MAD)",
                "Coût/kg (MAD/kg)",
            ],
            "Valeur": [
                round(resultats.get("Q_totale_kJ", 0), 1),
                round(resultats.get("P_utile_kW", 0), 2),
                round(resultats.get("E_elec_kWh", 0), 3),
                round(resultats.get("cout_operation", 0), 3),
                round(resultats.get("cout_journalier", 0), 2),
                round(resultats.get("cout_mensuel", 0), 2),
                round(resultats.get("cout_annuel", 0), 1),
                round(resultats.get("cout_kg", 0), 5),
            ],
        }
        pd.DataFrame(res).to_excel(writer, sheet_name="Résultats", index=False)

        # ── Feuille 4 : Analyse de sensibilité ───────────────────────────────
        row_idx = 0
        ws = writer.book.create_sheet("Analyse de sensibilité")
        for titre, df_s in df_sensibilite.items():
            ws.cell(row=row_idx + 1, column=1, value=titre)
            row_idx += 1
            # En-têtes
            for c_idx, col in enumerate(df_s.columns, start=1):
                ws.cell(row=row_idx + 1, column=c_idx, value=col)
            row_idx += 1
            # Données
            for _, row in df_s.iterrows():
                for c_idx, val in enumerate(row.values, start=1):
                    ws.cell(row=row_idx + 1, column=c_idx, value=round(float(val), 4))
                row_idx += 1
            row_idx += 2  # ligne vide entre sections

        # ── Feuille 5 : Comparaison scénarios ────────────────────────────────
        if not df_scenarios.empty:
            df_scenarios.to_excel(writer, sheet_name="Comparaison scénarios", index=False)

        # ── Feuille 6 : Conclusion ────────────────────────────────────────────
        ws_conc = writer.book.create_sheet("Conclusion")
        ws_conc.cell(row=1, column=1, value="Interprétation automatique des résultats")
        for i, ligne in enumerate(interpretations, start=3):
            # On retire les emojis non ASCII pour la compatibilité Excel
            ligne_clean = ligne.encode("ascii", "ignore").decode()
            ws_conc.cell(row=i, column=1, value=ligne_clean)

    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Génération d'un rapport texte (Markdown)
# ─────────────────────────────────────────────────────────────────────────────

def generer_rapport_markdown(
    params: dict,
    resultats: dict,
    interpretations: list[str],
    df_scenarios: pd.DataFrame | None = None,
) -> str:
    """
    Génère un rapport Markdown structuré prêt à être affiché ou exporté.
    """
    date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    mode = resultats.get("mode", "—")

    rapport = f"""
# Rapport Technico-Économique
## Procédé : {mode}
**Date de simulation :** {date_str}

---

## 1. Présentation du procédé

Le refroidissement et la congélation de produits alimentaires sont des opérations
unitaires fondamentales dans l'industrie agroalimentaire (IAA). Elles permettent de
ralentir ou d'arrêter les réactions biochimiques et microbiologiques, d'assurer la
conservation et la sécurité alimentaire des produits.

**Importance énergétique :** Ces procédés représentent souvent 30 à 60 % de la
consommation électrique totale d'une unité IAA, ce qui justifie une attention
particulière lors du dimensionnement.

---

## 2. Système étudié et hypothèses

- **Type de système :** ouvert / régime permanent (flux de produit continu)
- **Hypothèses retenues :**
  - Propriétés thermophysiques constantes par phase
  - Rendement de la machine = 1 / COP (modèle idéal de Carnot dégradé)
  - Pas de pertes thermiques aux parois (bilan utile)
  - La fraction d'eau congelable est considérée constante

---

## 3. Modèle de calcul

### Bilan matière

| Entrée      | Valeur                         |
|-------------|-------------------------------|
| Masse produit | {params.get('masse_kg', '—')} kg |

### Bilan énergétique

| Phase                        | Énergie (kJ) |
|------------------------------|-------------|
| Chaleur sensible (avant cong.) | {resultats.get('Q_sensible_kJ', 0):.1f} |
| Chaleur latente (congélation)  | {resultats.get('Q_latente_kJ', 0):.1f} |
| Chaleur sensible (après cong.) | {resultats.get('Q_post_kJ', 0):.1f} |
| **Q totale**                 | **{resultats.get('Q_totale_kJ', 0):.1f}** |

### Puissances et consommation

| Indicateur             | Valeur                               |
|------------------------|--------------------------------------|
| Puissance utile        | {resultats.get('P_utile_kW', 0):.2f} kW |
| Puissance électrique   | {resultats.get('P_elec_kW', 0):.2f} kW |
| Énergie consommée      | {resultats.get('E_elec_kWh', 0):.3f} kWh |
| COP machine            | {resultats.get('COP', '—')} |

---

## 4. Résultats technico-économiques

| Indicateur             | Valeur                               |
|------------------------|--------------------------------------|
| Coût / opération       | {resultats.get('cout_operation', 0):.3f} MAD |
| Coût / kg produit      | {resultats.get('cout_kg', 0):.5f} MAD/kg |
| Coût journalier        | {resultats.get('cout_journalier', 0):.2f} MAD |
| Coût mensuel           | {resultats.get('cout_mensuel', 0):.2f} MAD |
| **Coût annuel**        | **{resultats.get('cout_annuel', 0):,.1f} MAD** |

---

## 5. Interprétation des résultats

{chr(10).join('- ' + t for t in interpretations)}

---

## 6. Conclusion

Ce dimensionnement fournit une base solide pour le choix et le calibrage de
l'installation frigorifique. Pour aller plus loin, il est recommandé d'intégrer :
- Les pertes thermiques aux parois de la chambre froide,
- Le facteur de charge (taux d'utilisation de la puissance installée),
- L'amortissement du coût d'investissement dans l'analyse économique.

*Rapport généré automatiquement par l'application ThermoIAA — {date_str}*

*Étudiant : Rayane Berch — 1CI IAA — Professeure : Amal Ibijbijen*
"""
    return rapport


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Export PDF via fpdf2
# ─────────────────────────────────────────────────────────────────────────────

UNICODE_FONT_CANDIDATES = [
    "DejaVuSans.ttf",
    "NotoSans-Regular.ttf",
    "NotoSans.ttf",
]
DEFAULT_PDF_FONT = "Helvetica"
MAX_TABLE_WIDTH = 190

REPLACEMENT_MAP = {
    "‘": "'",
    "’": "'",
    "“": '"',
    "”": '"',
    "–": '-',
    "—": '-',
    "…": '...',
    "•": '-',
    " ": ' ',
    "‒": '-',
    "―": '-',
}


def find_unicode_font() -> tuple[str, Path | None]:
    """Cherche un fichier de police Unicode disponible localement."""
    env_path = __import__('os').environ.get('PDF_UNICODE_FONT')
    if env_path:
        custom_path = Path(env_path.strip())
        if custom_path.exists():
            return custom_path.stem, custom_path
        __import__('warnings').warn(
            f"Police Unicode non trouvée à {custom_path}. Utilisez DejaVuSans.ttf ou NotoSans.ttf."
        )

    search_dirs = [
        Path(__file__).resolve().parent,
        Path.cwd(),
        Path(__file__).resolve().parent / "fonts",
        Path.cwd() / "fonts",
    ]
    for directory in search_dirs:
        for candidate in UNICODE_FONT_CANDIDATES:
            font_path = directory / candidate
            if font_path.exists():
                return font_path.stem, font_path
    return DEFAULT_PDF_FONT, None


def clean_text(text: str, allow_unicode: bool = True) -> str:
    """Nettoie le texte Markdown/plain text pour l'export PDF sans crash."""
    if text is None:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for source, replacement in REPLACEMENT_MAP.items():
        text = text.replace(source, replacement)
    text = text.replace("\t", "    ")
    text = text.replace("•", "-")
    text = text.replace("“", """).replace("”", """)
    text = text.replace("’", "'").replace("‘", "'")
    text = text.replace("…", "...").replace("–", "-").replace("—", "-")
    if not allow_unicode:
        text = text.encode("latin-1", "replace").decode("latin-1")
    return text
def _set_pdf_font(pdf, font_name: str, font_size: int = 11) -> None:
    """Positionne la police PDF de manière stable."""
    try:
        pdf.set_font(font_name, size=font_size)
    except Exception:
        pdf.set_font(DEFAULT_PDF_FONT, size=font_size)


def _safe_multi_cell(pdf, text: str) -> None:
    """Utilise multi_cell pour toutes les lignes et revient à cell en dernier recours."""
    try:
        pdf.multi_cell(0, 6, text)
    except Exception:
        try:
            pdf.cell(0, 6, text, ln=True)
        except Exception:
            safe_text = text.encode("latin-1", "replace").decode("latin-1")
            pdf.cell(0, 6, safe_text, ln=True)


def exporter_pdf(rapport_md: str) -> bytes:
    """Convertit un rapport Markdown en PDF sans jamais planter sur Unicode."""
    try:
        from fpdf import FPDF
    except ImportError:
        __import__('warnings').warn(
            "fpdf2 n'est pas installé. Installez-le avec `pip install fpdf2`."
        )
        return b""

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    font_name, font_path = find_unicode_font()
    unicode_font_available = False
    if font_path is not None:
        try:
            pdf.add_font(font_name, "", str(font_path), uni=True)
            _set_pdf_font(pdf, font_name, font_size=11)
            unicode_font_available = True
        except Exception as exc:
            __import__('warnings').warn(
                f"Impossible de charger la police Unicode {font_path}: {exc}. Retour à {DEFAULT_PDF_FONT}."
            )
            _set_pdf_font(pdf, DEFAULT_PDF_FONT, font_size=11)
    else:
        __import__('warnings').warn(
            "Aucune police Unicode trouvée. Installez DejaVuSans.ttf ou NotoSans.ttf "
            "dans le dossier du projet ou fonts/. Le rendu sera limité."
        )
        _set_pdf_font(pdf, DEFAULT_PDF_FONT, font_size=11)

    for raw_line in rapport_md.splitlines():
        ligne = clean_text(raw_line, allow_unicode=unicode_font_available)
        if ligne.startswith("# "):
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=16)
            _safe_multi_cell(pdf, ligne[2:].strip())
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
        elif ligne.startswith("## "):
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=13)
            _safe_multi_cell(pdf, ligne[3:].strip())
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
        elif ligne.startswith("### "):
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
            _safe_multi_cell(pdf, ligne[4:].strip())
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
        elif ligne.startswith("|"):
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=9)
            _safe_multi_cell(pdf, ligne)
            _set_pdf_font(pdf, font_name if unicode_font_available else DEFAULT_PDF_FONT, font_size=11)
        elif __import__('re').match(r"^[-*+]\s+", ligne):
            bullet = "• " if unicode_font_available else "- "
            _safe_multi_cell(pdf, f"{bullet}{ligne[2:].strip()}")
        elif ligne == "---":
            pdf.ln(2)
            pdf.set_draw_color(180, 180, 180)
            pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + MAX_TABLE_WIDTH, pdf.get_y())
            pdf.ln(2)
        elif not ligne.strip():
            pdf.ln(3)
        else:
            if "**" in ligne:
                ligne = ligne.replace("**", "")
            _safe_multi_cell(pdf, ligne)

    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode("latin-1", "replace")
    elif isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Formatage des nombres pour l'affichage
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# 6.  Formatage des nombres pour l'affichage
# ─────────────────────────────────────────────────────────────────────────────

def fmt(val: float, decimales: int = 2, unite: str = "") -> str:
    """Formate un nombre avec séparateur de milliers et unité."""
    if math.isnan(val) or math.isinf(val):
        return "—"
    formatted = f"{val:,.{decimales}f}"
    return f"{formatted} {unite}".strip()
