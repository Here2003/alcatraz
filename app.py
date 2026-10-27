import os
import streamlit as st

st.set_page_config(
    page_title="Salut !",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Simple, mobile-first conversational assistant.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #f7f7f5; }
.block-container { max-width: 760px; padding: 1rem 1rem 2rem; }
.hero { padding: 1.2rem 0 .8rem; }
.hero h1 { font-size: 2rem; margin: 0; color: #20251f; }
.hero p { color: #687067; margin-top: .45rem; }
div[data-testid="stChatMessage"] { border-radius: 18px; padding: .7rem; }
div[data-testid="stChatInput"] { padding-bottom: .8rem; }
button[kind="primary"] { border-radius: 12px; }
.small-muted { color: #737a73; font-size: .85rem; }
</style>
<div class="hero">
  <h1>💬 Salut !</h1>
  <p>On peut parler de tout et de rien. Pose-moi une question, raconte-moi ta journée, demande un conseil ou lance un sujet.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("Réglages")
    assistant_style = st.selectbox(
        "Style de réponse",
        ["Naturel", "Drôle", "Direct", "Détaillé"],
    )
    if st.button("Nouvelle conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("Pour des réponses par IA, ajoute une clé API dans les secrets de Streamlit.")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Friendly starter prompts that fit mobile screens.
if not st.session_state.messages:
    st.markdown("**Tu veux parler de quoi ?**")
    starters = [
        "Raconte-moi une anecdote drôle",
        "Aide-moi à trouver une idée",
        "Parlons de musique ou de films",
        "J'ai besoin d'un conseil",
    ]
    cols = st.columns(2)
    for idx, starter in enumerate(starters):
        with cols[idx % 2]:
            if st.button(starter, key=f"starter_{idx}", use_container_width=True):
                st.session_state.pending_prompt = starter
                st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Écris ton message…")
if not prompt and st.session_state.get("pending_prompt"):
    prompt = st.session_state.pop("pending_prompt")

def local_reply(text, style):
    t = text.lower()
    if any(w in t for w in ["bonjour", "salut", "coucou", "hey", "hello"]):
        return "Salut 😄 Ça fait plaisir ! Quoi de neuf ? Tu veux discuter tranquillement ou tu as quelque chose en tête ?"
    if any(w in t for w in ["triste", "ça va pas", "je vais mal", "stress", "angoissé", "angoissée"]):
        return "Je suis là pour t'écouter. Tu veux me raconter ce qui se passe ? On peut prendre les choses une par une, sans jugement."
    if "merci" in t:
        return "Avec plaisir 😊 Tu peux continuer, je suis là."
    if any(w in t for w in ["blague", "drôle", "drole", "rigole"]):
        return "Pourquoi les plongeurs plongent-ils toujours en arrière et jamais en avant ? Parce que sinon ils tombent dans le bateau. 😄 Tu en veux une autre ?"
    if any(w in t for w in ["poubelle", "déchet", "collecte", "grasse"]):
        return ("Je peux aussi t'aider sur les infos de collecte à Grasse. Pour un jour de passage précis, "
                "il faut vérifier le calendrier officiel : https://www.paysdegrasse.fr/points-et-frequence-de-collecte")
    if any(w in t for w in ["idée", "idee", "projet", "créer", "creer"]):
        return "Avec plaisir ! On peut trouver des idées ensemble. Tu cherches une idée pour un projet, un cadeau, une sortie ou quelque chose d'autre ?"
    return "Je t'écoute 🙂 Tu peux m'en dire un peu plus ? Je peux t'aider à réfléchir, expliquer un sujet, écrire quelque chose ou simplement discuter."

def get_reply(text, style, history):
    api_key = ""
    try:
        api_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        return local_reply(text, style)
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        style_instruction = {
            "Naturel": "parle naturellement, comme dans une conversation amicale",
            "Drôle": "sois léger et drôle quand c'est approprié, sans forcer les blagues",
            "Direct": "réponds directement et simplement",
            "Détaillé": "explique clairement avec un peu plus de détails",
        }[style]
        transcript = []
        for item in history[-12:]:
            transcript.append({"role": item["role"], "content": item["content"]})
        transcript.append({"role": "user", "content": text})
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            instructions=(
                "Tu es un assistant conversationnel en français. Tu peux discuter de sujets variés, "
                "répondre aux questions, aider à réfléchir et écrire. Sois chaleureux, naturel et honnête. "
                "N'invente pas de faits présentés comme certains. Si tu ne sais pas, dis-le. "
                "Style demandé : " + style_instruction + "."
            ),
            input=transcript,
        )
        return response.output_text
    except Exception:
        return ("Je n'arrive pas à joindre le service IA pour le moment. Vérifie la clé API et les "
                "journaux Streamlit. En attendant, tu peux toujours me parler, mais mes réponses seront limitées.")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Je réfléchis…"):
            reply = get_reply(prompt, assistant_style, st.session_state.messages[:-1])
        st.markdown(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

st.markdown('<p class="small-muted">Astuce : sur téléphone, ouvre le menu en haut à gauche pour changer le style ou démarrer une nouvelle conversation.</p>', unsafe_allow_html=True)
