import os, re, io, zipfile
import streamlit as st
import streamlit.components.v1 as components
from openai import OpenAI

st.set_page_config(page_title="SiteForge AI", page_icon="🌐", layout="wide")
st.markdown("""
<style>
.block-container{max-width:1150px;padding-top:1.2rem}
.hero{padding:1.4rem;border-radius:22px;background:linear-gradient(135deg,#e5f4ff,#f1e8ff)}
.hero h1{margin:0;color:#182238}.hero p{margin:.5rem 0 0;color:#33415c}
div.stButton>button{border-radius:12px;min-height:2.7rem}
</style>
<div class="hero"><h1>🌐 SiteForge AI</h1>
<p>Décris ton idée, génère un site web, prévisualise-le et télécharge-le pour le publier gratuitement.</p></div>
""", unsafe_allow_html=True)

def get_key():
    try: return st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    except Exception: return os.getenv("OPENAI_API_KEY", "")

key = get_key()
with st.sidebar:
    st.header("Personnalise ton site")
    kind = st.selectbox("Type", ["Site vitrine", "Portfolio", "Blog", "Restaurant / commerce", "Page de lancement", "Association"])
    style = st.selectbox("Style", ["Moderne et épuré", "Luxe et élégant", "Coloré et créatif", "Sombre et technologique", "Naturel et chaleureux"])
    language = st.selectbox("Langue", ["Français", "Anglais", "Espagnol", "Italien"])
    mobile = st.checkbox("Optimisé pour téléphone", True)

name = st.text_input("Nom du site", placeholder="Ex. : Les Pattes Heureuses")
prompt = st.text_area("Décris le site que tu veux", placeholder="Ex. : un site pour un salon de toilettage, avec services, tarifs, horaires, galerie et contact…", height=130)
if not key:
    st.warning("La génération nécessite une clé API OpenAI. Dans Streamlit Cloud → Settings → Secrets, ajoute OPENAI_API_KEY.")
    st.code('OPENAI_API_KEY = "ta_cle_api"', language="toml")

if "site_html" not in st.session_state: st.session_state.site_html = ""
if st.button("✨ Créer mon site", type="primary", use_container_width=True):
    if not prompt.strip(): st.error("Décris le site que tu souhaites.")
    elif not key: st.error("Ajoute d'abord la clé API dans les Secrets.")
    else:
        instructions = f"""Tu es un développeur web et designer UX senior. Génère un site complet et soigné.
Type: {kind}; style: {style}; langue: {language}; nom: {name or 'déduire de la demande'}; mobile: {mobile}.
Retourne UNIQUEMENT un document HTML complet, sans bloc Markdown. Un seul fichier index.html autonome avec CSS dans style et JS simple dans script. Aucun framework ni compilation. Mise en page responsive, accessibilité, navigation, sections pertinentes, pied de page. Boutons fonctionnels si possible. N'invente pas de témoignages réels, adresses, numéros ni statistiques. Les informations manquantes doivent être des placeholders clairs. Images optionnelles depuis images.unsplash.com. Un formulaire ne doit pas prétendre envoyer des données sans backend; utilise un lien mailto ou indique la limite. Le site doit être publiable en hébergement statique. N'inclus aucune clé secrète."""
        try:
            with st.spinner("L'IA conçoit et code ton site…"):
                client = OpenAI(api_key=key)
                result = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[{"role":"system","content":instructions},{"role":"user","content":prompt}],
                    max_tokens=7000)
                html = (result.choices[0].message.content or "").strip()
                html = re.sub(r"^```(?:html)?\s*", "", html, flags=re.I)
                html = re.sub(r"\s*```$", "", html)
            if "<html" not in html.lower() or "<body" not in html.lower():
                st.error("L'IA n'a pas retourné un document HTML complet. Réessaie avec une demande plus précise.")
            else:
                st.session_state.site_html = html
                st.success("Site généré ! Vérifie le contenu avant de le publier.")
        except Exception as e:
            st.error("Échec de génération : vérifie la clé API, les crédits et l'accès au modèle.")
            st.caption(str(e)[:400])

html = st.session_state.site_html
if html:
    st.divider()
    st.subheader("Aperçu du site")
    mode = st.radio("Affichage", ["Ordinateur", "Téléphone"], horizontal=True)
    components.html(html, height=760 if mode=="Ordinateur" else 700, scrolling=True)
    st.download_button("⬇️ Télécharger index.html", html.encode("utf-8"), file_name="index.html", mime="text/html", use_container_width=True)
    slug = re.sub(r"[^a-z0-9]+", "-", (name or "mon-site").lower()).strip("-") or "mon-site"
    bundle = io.BytesIO()
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("index.html", html)
        z.writestr("README-publication.txt", """PUBLICATION GRATUITE
1. Décompresse ce ZIP.
2. Pour Netlify Drop : ouvre https://app.netlify.com/drop et dépose le dossier contenant index.html.
3. Ou utilise GitHub Pages : https://pages.github.com/ et active Pages dans les paramètres du dépôt.
Vérifie textes, liens, coordonnées et images avant publication. L'hébergement statique peut être gratuit dans les limites du service. Domaine personnalisé, formulaires avec stockage, base de données ou espace membre peuvent coûter de l'argent.""")
    st.download_button("📦 Télécharger le pack prêt à publier (ZIP)", bundle.getvalue(), file_name=slug+".zip", mime="application/zip", use_container_width=True)
    st.markdown("### Publier gratuitement")
    st.markdown("- [Netlify Drop](https://app.netlify.com/drop) : décompresse le ZIP et dépose le dossier.\n- [GitHub Pages](https://pages.github.com/) : ajoute index.html à un dépôt et active Pages.")
    st.caption("Ce prototype génère les fichiers, mais ne crée pas automatiquement un compte d'hébergement ni ne publie le site à ta place.")

with st.expander("Comment activer l'IA ?"):
    st.markdown('Dans Streamlit Cloud → Settings → Secrets, ajoute `OPENAI_API_KEY = "ta_cle_api"`. Ne publie jamais la clé dans GitHub. Les appels API peuvent être facturés.')
