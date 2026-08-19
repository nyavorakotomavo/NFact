#!/usr/bin/env python3
"""
Extrait vendeur + client depuis messages bruts via Mistral IA.
Lit la config depuis config/ia.json automatiquement.
"""

import os
import json
import re
import sys
from pathlib import Path


def parse_number(value, default=0.0):
    if value is None:
        return default
    s = str(value).strip()
    if not s:
        return default
    match = re.search(r'-?\d[\d\s.,]*', s)
    if not match:
        return default
    s = match.group(0)
    s = s.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return default


def extract_json(text):
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end])
        except Exception:
            return None
    return None


def load_ia_config():
    """Charge la config IA depuis config/ia.json"""
    config_path = Path("config/ia.json")
    if not config_path.is_file():
        print("❌ Fichier config/ia.json introuvable")
        print("💡 Crée-le avec ta clé Mistral :")
        print('   {"api_key": "ta_cle", "api_url": "https://api.mistral.ai/v1/chat/completions", "model": "mistral-small-latest"}')
        sys.exit(1)
    
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ config/ia.json invalide : {e}")
        sys.exit(1)
    
    if not config.get("api_key") or config["api_key"] == "METS_TA_CLE_MISTRAL_ICI":
        print("❌ Clé API manquante dans config/ia.json")
        print("💡 Remplace METS_TA_CLE_MISTRAL_ICI par ta vraie clé Mistral")
        sys.exit(1)
    
    return config


def call_ai(seller_raw, client_raw, ia_config):
    api_key = ia_config["api_key"]
    url = ia_config.get("api_url", "https://api.mistral.ai/v1/chat/completions")
    model = ia_config.get("model", "mistral-small-latest")

    print(f"🤖 Appel IA : {model}")

    system_prompt = """Tu es un expert en extraction d'informations de facturation.
Tu vas recevoir DEUX messages :

1. SELLER_INFOS : les informations du VENDEUR (celui qui émet la facture)
2. CLIENT_INFOS : le message du CLIENT (celui qui reçoit la facture) avec sa demande

Extrais les informations et retourne UNIQUEMENT un JSON valide, sans markdown.

Format exact :
{
  "vendeur": {
    "nom": "nom de l'entreprise du vendeur",
    "adresse": "adresse complète",
    "telephone": "numéro",
    "email": "email",
    "nif": "NIF si mentionné",
    "stat": "STAT si mentionné"
  },
  "client": {
    "nom": "nom du client ou de son entreprise",
    "adresse": "adresse",
    "telephone": "numéro",
    "email": "email"
  },
  "type_document": "FACTURE ou DEVIS",
  "devise": "Ar, EUR, USD",
  "articles": [
    {"designation": "description du service", "quantite": 1, "prix_unitaire": 0}
  ],
  "tva_pourcentage": 0,
  "remise_pourcentage": 0,
  "remise_montant": 0,
  "conditions_paiement": ""
}

RÈGLES CRITIQUES :
- Le VENDEUR est celui qui ÉMET la facture (ses infos sont dans SELLER_INFOS)
- Le CLIENT est celui qui REÇOIT la facture (ses infos sont dans CLIENT_INFOS)
- Les articles sont extraits UNIQUEMENT depuis CLIENT_INFOS
- N'inclus JAMAIS de texte conversationnel dans les articles
- Si "3 mois de maintenance à 150 000 Ar le mois" → quantite=3, prix_unitaire=150000
- Devise par défaut : "Ar"
- Type par défaut : "FACTURE"
- N'invente JAMAIS d'informations absentes des messages"""

    user_message = f"""SELLER_INFOS :
{seller_raw}

CLIENT_INFOS :
{client_raw}"""

    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        import requests
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        print(f"📡 Réponse HTTP : {resp.status_code}")
        if resp.status_code != 200:
            print(f"❌ Erreur API : {resp.text[:300]}")
            sys.exit(1)
        content = resp.json()["choices"][0]["message"]["content"]
        result = extract_json(content)
        if not result:
            print("❌ La réponse IA n'est pas du JSON valide")
            print(f"   Réponse brute : {content[:200]}")
            sys.exit(1)
        return result
    except Exception as e:
        print(f"❌ Exception IA : {e}")
        sys.exit(1)


def sanitize_articles(articles):
    result = []
    if not isinstance(articles, list):
        return result

    stop_words = [
        "bonjour", "salut", "merci", "n'oublie", "oublie pas", "s'il te plaît",
        "stp", "comme convenu", "suite à", "tu peux", "envoie", "dès que",
        "mon numéro", "je suis", "c'est", "voici", "peux-tu", "pourriez",
        "cordialement", "bien à toi", "n'oubliez"
    ]

    for art in articles:
        if not isinstance(art, dict):
            continue
        designation = str(
            art.get("designation") or art.get("name") or
            art.get("produit") or art.get("service") or ""
        ).strip()

        if not designation:
            continue
        if len(designation) > 100:
            print(f"  ⚠️  Article rejeté (trop long) : {designation[:50]}...")
            continue
        lower_desig = designation.lower()
        if any(w in lower_desig for w in stop_words):
            print(f"  ⚠️  Article rejeté (conversationnel) : {designation[:50]}...")
            continue

        quantite = parse_number(art.get("quantite") or art.get("quantity"), 1)
        if quantite <= 0 or quantite > 10000:
            quantite = 1
        prix = parse_number(
            art.get("prix_unitaire") or art.get("price") or art.get("prix"), 0
        )
        if prix < 0:
            prix = 0
        if prix > 1_000_000_000:
            print(f"  ⚠️  Article rejeté (prix absurde) : {designation[:50]}...")
            continue

        result.append({
            "designation": designation,
            "quantite": quantite,
            "prix_unitaire": prix
        })
    return result


def main():
    seller_raw = os.getenv("SELLER_INFOS", "")
    client_raw = os.getenv("CLIENT_INFOS", "")
    style = os.getenv("STYLE", "stripe")
    couleur_accent = os.getenv("COULEUR_ACCENT", "#2E5CFF")
    taille_papier = os.getenv("TAILLE_PAPIER", "A4")
    logo_path = os.getenv("LOGO_PATH", "")

    if not seller_raw.strip():
        print("❌ SELLER_INFOS est vide")
        sys.exit(1)
    if not client_raw.strip():
        print("❌ CLIENT_INFOS est vide")
        sys.exit(1)

    print("=" * 60)
    print("📥 Message VENDEUR :")
    print("-" * 60)
    print(seller_raw[:300])
    print("-" * 60)
    print("📥 Message CLIENT :")
    print("-" * 60)
    print(client_raw[:300])
    print("-" * 60)

    # Charger config IA
    ia_config = load_ia_config()

    # Appeler l'IA
    ai_result = call_ai(seller_raw, client_raw, ia_config)

    # Extraire vendeur
    vendeur = {
        "nom": "", "adresse": "", "telephone": "",
        "email": "", "nif": "", "stat": "", "logo": ""
    }
    if isinstance(ai_result.get("vendeur"), dict):
        v = ai_result["vendeur"]
        vendeur = {
            "nom": str(v.get("nom", "")).strip(),
            "adresse": str(v.get("adresse", "")).strip(),
            "telephone": str(v.get("telephone", "")).strip(),
            "email": str(v.get("email", "")).strip(),
            "nif": str(v.get("nif", "")).strip(),
            "stat": str(v.get("stat", "")).strip(),
            "logo": ""
        }

    if logo_path and Path(logo_path).is_file():
        vendeur["logo"] = logo_path

    client = {"nom": "", "adresse": "", "telephone": "", "email": ""}
    if isinstance(ai_result.get("client"), dict):
        c = ai_result["client"]
        client = {
            "nom": str(c.get("nom", "")).strip(),
            "adresse": str(c.get("adresse", "")).strip(),
            "telephone": str(c.get("telephone", "")).strip(),
            "email": str(c.get("email", "")).strip()
        }

    articles = sanitize_articles(ai_result.get("articles"))

    type_doc = str(ai_result.get("type_document", "FACTURE")).upper()
    devise = str(ai_result.get("devise", "Ar"))
    tva = parse_number(ai_result.get("tva_pourcentage"), 0)
    remise_pct = parse_number(ai_result.get("remise_pourcentage"), 0)
    remise_montant = parse_number(ai_result.get("remise_montant"), 0)
    conditions = str(ai_result.get("conditions_paiement", "") or "Paiement à réception de facture.")

    erreurs = []
    if not vendeur.get("nom"):
        erreurs.append("Nom du vendeur introuvable")
    if not client.get("nom"):
        erreurs.append("Nom du client introuvable")
    if not articles:
        erreurs.append("Aucun article valide extrait")

    if erreurs:
        print("❌ Extraction incomplète :")
        for e in erreurs:
            print(f"  - {e}")
        sys.exit(1)

    try:
        from reportlab.lib import colors as rl_colors
        rl_colors.HexColor(couleur_accent)
    except Exception:
        couleur_accent = "#2E5CFF"

    if taille_papier.upper() not in ("A4", "LETTER", "A5"):
        taille_papier = "A4"

    invoice = {
        "type_document": type_doc if type_doc in ("FACTURE", "DEVIS") else "FACTURE",
        "devise": devise,
        "style": style,
        "couleur_accent": couleur_accent,
        "taille_papier": taille_papier.upper(),
        "vendeur": vendeur,
        "client": client,
        "articles": articles,
        "tva_pourcentage": tva,
        "remise_pourcentage": remise_pct,
        "remise_montant": remise_montant,
        "conditions_paiement": conditions,
        "mentions_legales": "",
        "couleur_texte": "#000000",
        "couleur_fond_alternee": "#f5f5f5",
        "dossier_sortie": "out"
    }

    Path("invoice.json").write_text(
        json.dumps(invoice, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print("✅ invoice.json créé avec succès !")
    print("=" * 60)
    print(f"🏢 Vendeur   : {vendeur.get('nom')}")
    print(f"👤 Client    : {client.get('nom')}")
    print(f"📦 Articles  : {len(articles)}")
    for i, art in enumerate(articles, 1):
        print(f"   {i}. {art['designation']} x{art['quantite']} @ {art['prix_unitaire']}")
    print(f"📊 TVA       : {tva}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
