# ThermoIAA — Outil de dimensionnement thermodynamique
## Refroidissement & Congélation en industrie agroalimentaire

> **Projet Thermodynamique Appliquée — Option B : Application interactive Python/Streamlit**

---

## 📋 Description

**ThermoIAA** est une application interactive professionnelle développée en Python/Streamlit permettant à un ingénieur IAA de :

- Réaliser des **bilans matière et énergétiques** complets
- Calculer la **puissance frigorifique** et la **consommation électrique**
- Estimer les **coûts énergétiques** (par opération, par kg, journalier, mensuel, annuel)
- Conduire des **analyses de sensibilité** interactives
- **Comparer plusieurs scénarios** (COP, température, masse, durée)
- Générer une **interprétation automatique** des résultats
- **Exporter** les résultats en Excel et PDF

---

## 🧑‍🎓 Informations du projet

- Auteur : Rayane Berch
- Niveau d'étude : 1CI IAA
- Professeure : Amal Ibijbijen

---

## 🗂️ Structure du projet

```
thermo_iam/
│
├── app.py              ← Interface Streamlit principale (1 000+ lignes)
├── calculations.py     ← Moteur de calculs thermodynamiques (400 lignes)
├── utils.py            ← Utilitaires : interprétation, export Excel/PDF (430 lignes)
├── requirements.txt    ← Dépendances Python
├── README.md           ← Ce fichier
│
├── data/               ← (réservé pour données futures)
├── assets/             ← (logos, images)
└── report/             ← (rapports générés)
```

---

## ⚙️ Installation

### Prérequis
- Python 3.10 ou supérieur
- pip

### Étapes

```bash
# 1. Cloner / décompresser le projet
cd thermo_iam

# 2. (Recommandé) Créer un environnement virtuel
python -m venv venv
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate             # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Lancer l'application
streamlit run app.py
```

L'application s'ouvre automatiquement dans le navigateur à l'adresse : `http://localhost:8501`

---

## 🚀 Utilisation

1. **Choisir le mode** : Refroidissement simple OU Congélation complète
2. **Sélectionner un produit** : poulet, bœuf, poisson, fromage, jus... ou personnalisé
3. **Saisir les paramètres** dans la barre latérale gauche
4. **Cliquer sur "Lancer les calculs"**
5. **Explorer les onglets** :
   - 📊 Résultats — KPI, bilans, coûts
   - 📈 Analyse de sensibilité — variation COP, T, masse, prix
   - ⚖️ Comparaison scénarios — tableau et graphes
   - 🔭 Profil thermique — courbe de température
   - 📐 Équations — modèle mathématique explicite
   - 💬 Interprétation — analyse automatique + radar
   - 📄 Rapport & Export — Excel, PDF, Markdown
   - 📋 Historique — suivi des simulations

---

## 📐 Modèle thermodynamique

### Procédé : Refroidissement & Congélation (Application 5)

| Phase | Équation | Unité |
|-------|----------|-------|
| Chaleur sensible (avant cong.) | Q₁ = m · cp · (T_ini − T_cong) | kJ |
| Chaleur latente | Q₂ = m · w_eau · L_cong | kJ |
| Chaleur sensible (après cong.) | Q₃ = m · cp_c · (T_cong − T_fin) | kJ |
| Énergie totale | Q = Q₁ + Q₂ + Q₃ | kJ |
| Puissance utile | P_utile = Q / (Δt × 3600) | kW |
| Puissance électrique | P_élec = P_utile / COP | kW |
| Énergie consommée | E = P_élec × Δt | kWh |
| Coût opération | C = E × p_élec | € |

---

## 🥩 Produits disponibles (valeurs littérature IAA)

| Produit | cp (kJ/kg·K) | cp_c (kJ/kg·K) | L (kJ/kg) | T_cong (°C) |
|---------|-------------|----------------|-----------|-------------|
| Poulet | 3.31 | 1.68 | 246 | -1.5 |
| Bœuf | 3.52 | 1.75 | 251 | -1.7 |
| Saumon | 3.60 | 1.80 | 257 | -2.0 |
| Fromage | 2.55 | 1.35 | 180 | -3.5 |
| Jus de fruit | 3.90 | 2.00 | 292 | -1.0 |
| Légumes | 3.85 | 1.95 | 285 | -1.2 |

---

## 📦 Dépendances

```
streamlit>=1.32.0
numpy>=1.26.0
pandas>=2.2.0
plotly>=5.20.0
matplotlib>=3.8.0
openpyxl>=3.1.2
fpdf2>=2.7.9
```

---

## 🎓 Contexte académique

Projet réalisé dans le cadre du cours de **Thermodynamique Appliquée** — Industrie Agroalimentaire.

**Livrables :** Application interactive Python + Rapport technico-économique + Présentation orale

**Conformité :** Répond aux exigences de l'Option B (Application interactive) du cahier des charges.

---

*ThermoIAA v1.0 — Thermodynamique Appliquée IAA — 2024/2025*
