#!/usr/bin/env python3
"""
Transforme le message brut du client en invoice.json.
Gère : vendeur, style, couleur, format, logo.
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


def load_seller():
    """Charge le vendeur depuis la variable SELLER_FILE ou config/vendeur.json"""
    seller_file = os.getenv("SELLER_FILE", "")
    
    if seller_file:
        path = Path(seller_file)
        if path.is_file():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
    
    # Fallback : config/vendeur.json
    path = Path("config/vendeur.json")
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    
    return {
        "nom": "Mon Entreprise", "adresse": "", "telephone": "",
        "email": "", "nif": "", "stat": "", "logo": ""
    }


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


def call_ai(raw):
    api_key = os.getenv("AI_API_KEY")
    url = os.getenv("AI_API_URL", "")
    model = os.getenv("AI_MODEL", "")

    if not api_key or not url or not model:
        print("⚠️  IA non configurée")
        return None

    print(f"🤖 Appel IA : {model}")

    system_prompt = """Tu es un expert en extraction d'informations de facturation.
Extrais TOUTES les informations depuis le texte brut du client.
Retourne UNIQUEMENT un JSON valide, sans markdown, sans texte autour.

Format exact :
{
  "type_document": "FACTURE ou DEVIS",
  "devise": "Ar, EUR, USD",
  "client": {"nom": "", "adresse": "", "telephone": "", "email": ""},
  "articles": [{"designation": "", "quantite": 1, "prix_unitaire": 0}],
  "tva_pourcentage": 0,
  "remise_pourcentage": 0,
  "remise_montant": 0,
  "conditions_paiement": ""
}

RÈGLES CRITIQUES :
- Le "client" est la personne/entreprise QUI REÇOIT la facture (celui qui paie)
- Les "articles" sont UNIQUEMENT les produits/services facturés avec leur prix
- N'inclus JAMAIS dans les articles du texte conversationnel comme "bonjour", "merci", "n'oublie pas"
- Si un prix est mentionné pour un service, extrais-le comme article
- Quantité par défaut = 1
- Si le texte dit "3 mois de maintenance à 150 000 Ar le mois", c'est : quantite=3, prix_unitaire=150000
- N'invente JAMAIS d'informations absentes du texte
- La devise par défaut est "Ar" si non précisée"""

    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrais les infos de facturation :\n\n{raw}"}
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
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        result = extract_json(content)
        if result:
            print("✅ IA a retourné un JSON valide")
        else:
            print("⚠️  La réponse IA n'est pas du JSON valide")
        return result
    except Exception as e:
        print(f"❌ Exception IA : {e}")
        return None


def sanitize_articles(articles):
    """Nettoie et valide les articles. Rejette les articles suspects."""
    result = []
    if not isinstance(articles, list):
        return result
    
    # Mots qui indiquent un texte conversationnel, pas un article
    stop_words = [
        "bonjour", "salut", "merci", "n'oublie", "oublie pas", "s'il te plaît",
        "stp", "comme convenu", "suite à", "tu peux", "envoie", "dès que",
        "mon numéro", "adresse", "je suis", "c'est", "voici", "peux-tu",
        "n'oubliez", "pourriez", "cordialement", "bien à toi"
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
        
        # Rejeter les articles trop longs (>100 chars = probablement du texte conversationnel)
        if len(designation) > 100:
            print(f"  ⚠️  Article rejeté (trop long) : {designation[:50]}...")
            continue
        
        # Rejeter les articles contenant des mots conversationnels
        lower_desig = designation.lower()
        if any(w in lower_desig for w in stop_words):
            print(f"  ⚠️  Article rejeté (texte conversationnel) : {designation[:50]}...")
            continue
        
        quantite = parse_number(art.get("quantite") or art.get("quantity"), 1)
        if quantite <= 0 or quantite > 10000:
            quantite = 1
        
        prix = parse_number(
            art.get("prix_unitaire") or art.get("price") or art.get("prix"), 0
        )
        if prix < 0:
            prix = 0
        
        # Rejeter les articles avec un prix absurde (> 1 milliard)
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
    raw = os.getenv("CLIENT_INFOS", "")
    style = os.getenv("STYLE", "stripe")
    couleur_accent = os.getenv("COULEUR_ACCENT", "#2E5CFF")
    taille_papier = os.getenv("TAILLE_PAPIER", "A4")
    logo_path = os.getenv("LOGO_PATH", "")

    if not raw.strip():
        print("❌ CLIENT_INFOS est vide")
        sys.exit(1)

    print("=" * 60)
    print("📥 Texte reçu du client :")
    print("-" * 60)
    print(raw[:500])
    print("-" * 60)

    seller = load_seller()
    print(f"🏢 Vendeur : {seller.get('nom', '?')}")
    print(f"🎨 Style   : {style}")
    print(f"🖌️  Couleur : {couleur_accent}")
    print(f"📄 Format  : {taille_papier}")
    print(f"🖼️  Logo    : {logo_path or '(aucun)'}")
    print("-" * 60)

    # Appliquer le logo si fourni
    if logo_path and Path(logo_path).is_file():
        seller["logo"] = logo_path

    # Appeler l'IA
    ai_result = call_ai(raw)

    if not ai_result or not isinstance(ai_result, dict):
        print("❌ L'IA n'a pas pu extraire les informations.")
        print("💡 Vérifie que tes secrets AI_API_KEY, AI_API_URL, AI_MODEL sont corrects.")
        print("💡 Ou fournis un message plus structuré avec les articles et prix.")
        sys.exit(1)

    # Extraire les infos
    client = {"nom": "", "adresse": "", "telephone": "", "email": ""}
    if isinstance(ai_result.get("client"), dict):
        client = {
            "nom": str(ai_result["client"].get("nom", "")).strip(),
            "adresse": str(ai_result["client"].get("adresse", "")).strip(),
            "telephone": str(ai_result["client"].get("telephone", "")).strip(),
            "email": str(ai_result["client"].get("email", "")).strip()
        }

    articles = sanitize_articles(ai_result.get("articles"))
    type_doc = str(ai_result.get("type_document", "FACTURE")).upper()
    devise = str(ai_result.get("devise", "Ar"))
    tva = parse_number(ai_result.get("tva_pourcentage"), 0)
    remise_pct = parse_number(ai_result.get("remise_pourcentage"), 0)
    remise_montant = parse_number(ai_result.get("remise_montant"), 0)
    conditions = str(ai_result.get("conditions_paiement", "") or "Paiement à réception de facture.")

    # Validation
    if not client.get("nom"):
        print("❌ Nom du client introuvable dans le message.")
        sys.exit(1)

    if not articles:
        print("❌ Aucun article valide extrait du message.")
        print("💡 Le message doit contenir des services/produits avec leurs prix.")
        sys.exit(1)

    # Valider la couleur
    try:
        from reportlab.lib import colors as rl_colors
        rl_colors.HexColor(couleur_accent)
    except Exception:
        couleur_accent = "#2E5CFF"

    # Valider le format
    if taille_papier.upper() not in ("A4", "LETTER", "A5"):
        taille_papier = "A4"

    invoice = {
        "type_document": type_doc if type_doc in ("FACTURE", "DEVIS") else "FACTURE",
        "devise": devise,
        "style": style,
        "couleur_accent": couleur_accent,
        "taille_papier": taille_papier.upper(),
        "vendeur": seller,
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
    print(f"🏢 Vendeur   : {seller.get('nom')}")
    print(f"👤 Client    : {client.get('nom')}")
    print(f"📍 Adresse   : {client.get('adresse') or '(non renseignée)'}")
    print(f"📋 Type      : {invoice['type_document']}")
    print(f"💰 Devise    : {devise}")
    print(f"🎨 Style     : {style}")
    print(f"📦 Articles  : {len(articles)}")
    for i, art in enumerate(articles, 1):
        print(f"   {i}. {art['designation']} x{art['quantite']} @ {art['prix_unitaire']}")
    print(f"📊 TVA       : {tva}%")
    if remise_pct > 0:
        print(f"🏷️  Remise   : {remise_pct}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
