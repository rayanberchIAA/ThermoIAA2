#!/usr/bin/env python3
"""
Script d'aide pour configurer ThermoIAA en PWA
"""

import os
import shutil
from pathlib import Path

def setup_pwa():
    """Configure l'application Streamlit pour PWA"""

    app_path = Path(__file__).parent / "app.py"

    # Lire le fichier app.py
    with open(app_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Vérifier si PWA est déjà configuré
    if 'manifest.json' in content:
        print("✅ PWA déjà configuré dans app.py")
        return

    # Trouver la ligne de set_page_config
    if 'st.set_page_config' in content:
        print("⚠️  set_page_config déjà présent, vérifiez manuellement")
        return

    # Ajouter la configuration PWA
    pwa_config = '''
# Configuration PWA
st.set_page_config(
    page_title="ThermoIAA",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Métadonnées PWA
st.markdown("""
<link rel="manifest" href="manifest.json">
<meta name="theme-color" content="#0d2b45">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
""", unsafe_allow_html=True)

# Service Worker
st.markdown("""
<script>
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js')
        .then(registration => console.log('SW registered'))
        .catch(error => console.log('SW registration failed'));
}
</script>
""", unsafe_allow_html=True)
'''

    # Insérer après les imports
    import_end = content.find('# ── Modules locaux ────────────────────────────────────────────────────────────')
    if import_end == -1:
        import_end = content.find('import streamlit')

    new_content = content[:import_end] + pwa_config + '\n' + content[import_end:]

    # Écrire le fichier modifié
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("✅ Configuration PWA ajoutée à app.py")
    print("📝 Pensez à créer les icônes icon-192.png et icon-512.png")

def create_icons_placeholder():
    """Crée des placeholders pour les icônes"""
    print("📝 Créez des icônes PNG de 192x192 et 512x512 pixels")
    print("   Nommez-les: icon-192.png et icon-512.png")
    print("   Placez-les dans le même dossier que app.py")

if __name__ == "__main__":
    print("🔧 Configuration ThermoIAA PWA")
    print("=" * 40)

    setup_pwa()
    create_icons_placeholder()

    print("\n🚀 Pour tester:")
    print("1. streamlit run app.py")
    print("2. Ouvrir http://localhost:8501 dans Chrome Android")
    print("3. Menu > Ajouter à l'écran d'accueil")