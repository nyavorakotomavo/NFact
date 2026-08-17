#!/usr/bin/env python3
"""
Transforme le message brut du client en invoice.json.
Gère aussi : style, couleur, format papier, logo.
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


def load_vendor():
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
        print("⚠️  IA non configurée, mode parsing uniquement")
        return None

    print(f"🤖 Appel IA : {model}")

    system_prompt = """Tu es un expert en extraction d'informations de facturation.
Extrais TOUTES les informations depuis le texte brut du client.
Retourne UNIQUEMENT un JSON valide, sans markdown.

Format :
{
  "type_document": "FACTURE ou DEVIS",
  "devise": "Ar, EUR, USD",
  "client": {"nom": "", "adresse": "", "telephone": "", "email": ""},
  "articles": [{"designation": "", "quantite": 1, "prix_unitaire": 0}],
  "tva_pourcentage": 20,
  "remise_pourcentage": 0,
  "remise_montant": 0,
  "conditions_paiement": ""
}

RÈGLES :
- Type par défaut : FACTURE
- Devise par défaut : Ar
- Quantité par défaut : 1
- N'invente JAMAIS d'informations absentes du texte"""

    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrais les infos :\n\n{raw}"}
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
        return extract_json(content)
    except Exception as e:
        print(f"❌ Exception IA : {e}")
        return None


def sanitize_articles(articles):
    result = []
    if not isinstance(articles, list):
        return result
    for art in articles:
        if not isinstance(art, dict):
            continue
        designation = str(
            art.get("designation") or art.get("name") or
            art.get("produit") or art.get("service") or ""
        ).strip()
        if not designation:
            continue
        quantite = parse_number(art.get("quantite") or art.get("quantity"), 1)
        if quantite <= 0:
            quantite = 1
        prix = parse_number(
            art.get("prix_unitaire") or art.get("price") or art.get("prix"), 0
        )
        if prix < 0:
            prix = 0
        result.append({
            "designation": designation,
            "quantite": quantite,
            "prix_unitaire": prix
        })
    return result


def fallback_parse(raw):
    print("🔄 Fallback : parsing regex...")
    data = {"articles": []}
    lines = str(raw).strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        price_matches = re.findall(r'(\d[\d\s.,]*\d)\s*(?:ar|€|\$|eur|usd)?', line, re.I)
        if price_matches:
            last_price = price_matches[-1]
            price_value = parse_number(last_price)
            if price_value > 0:
                designation = line.replace(last_price, "").strip(" :-–—")
                if designation and len(designation) > 2:
                    data["articles"].append({
                        "designation": designation,
                        "quantite": 1,
                        "prix_unitaire": price_value
                    })
    return data


def main():
    raw = os.getenv("CLIENT_INFOS", "")
    email_to = os.getenv("EMAIL_TO", "")
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
    print(f"🎨 Style        : {style}")
    print(f"🖌️  Couleur      : {couleur_accent}")
    print(f"📄 Format       : {taille_papier}")
    print(f"🖼️  Logo         : {logo_path or '(aucun)'}")
    print("-" * 60)

    vendor = load_vendor()

    # Appliquer le logo si fourni
    if logo_path and Path(logo_path).is_file():
        vendor["logo"] = logo_path
        print(f"✅ Logo appliqué : {logo_path}")

    # Appeler l'IA
    ai_result = call_ai(raw)

    client = {"nom": "", "adresse": "", "telephone": "", "email": ""}
    articles = []
    type_doc = "FACTURE"
    devise = "Ar"
    tva = 0
    remise_pct = 0
    remise_montant = 0
    conditions = "Paiement à réception de facture."

    if ai_result and isinstance(ai_result, dict):
        print("✅ IA a extrait les informations")
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
        if ai_result.get("conditions_paiement"):
            conditions = str(ai_result["conditions_paiement"])

    if not articles:
        fallback = fallback_parse(raw)
        articles = sanitize_articles(fallback.get("articles"))

    if not client.get("nom"):
        if email_to and "@" in email_to:
            client["nom"] = email_to.split("@")[0].replace(".", " ").title()
        else:
            client["nom"] = "Client"

    if not articles:
        print("❌ Aucun article trouvé dans le texte")
        sys.exit(1)

    # Validation de la couleur
    try:
        from reportlab.lib import colors
        colors.HexColor(couleur_accent)
    except Exception:
        print(f"⚠️ Couleur invalide '{couleur_accent}', utilisation de #2E5CFF")
        couleur_accent = "#2E5CFF"

    # Validation du format papier
    if taille_papier.upper() not in ("A4", "LETTER", "A5"):
        print(f"⚠️ Format inconnu '{taille_papier}', utilisation de A4")
        taille_papier = "A4"

    invoice = {
        "type_document": type_doc if type_doc in ("FACTURE", "DEVIS") else "FACTURE",
        "devise": devise,
        "style": style,
        "couleur_accent": couleur_accent,
        "taille_papier": taille_papier.upper(),
        "vendeur": vendor,
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
    print(f"📋 Type      : {invoice['type_document']}")
    print(f"🎨 Style     : {invoice['style']}")
    print(f"🖌️  Couleur   : {invoice['couleur_accent']}")
    print(f"📄 Format    : {invoice['taille_papier']}")
    print(f"🖼️  Logo      : {vendor.get('logo') or '(aucun)'}")
    print(f"👤 Client    : {invoice['client'].get('nom')}")
    print(f"📦 Articles  : {len(invoice['articles'])}")
    for i, art in enumerate(invoice['articles'], 1):
        print(f"   {i}. {art['designation']} x{art['quantite']} @ {art['prix_unitaire']}")
    print(f"📊 TVA       : {invoice['tva_pourcentage']}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
