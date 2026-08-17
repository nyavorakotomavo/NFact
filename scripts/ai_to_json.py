#!/usr/bin/env python3
"""
Transforme n'importe quel texte (message client en vrac) en invoice.json.
Utilise l'IA comme source principale, avec fallback sur parsing regex.
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
    s = s.replace(" ", "").replace("\u00a0", "").replace("\u202f", "")
    s = s.replace(",", ".").replace("%", "").replace("'", "")
    s = re.sub(r"[^\d.\-]", "", s)
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
    """Extrait le JSON d'une réponse IA (avec ou sans markdown)."""
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
    """Appelle l'IA pour extraire les infos depuis un texte en vrac."""
    api_key = os.getenv("AI_API_KEY")
    url = os.getenv("AI_API_URL", "")
    model = os.getenv("AI_MODEL", "")

    if not api_key:
        print("⚠️  Pas de AI_API_KEY, mode parsing uniquement")
        return None

    if not url:
        print("⚠️  Pas de AI_API_URL, mode parsing uniquement")
        return None

    if not model:
        print("⚠️  Pas de AI_MODEL, mode parsing uniquement")
        return None

    print(f"🤖 Appel IA : {model} sur {url}")

    system_prompt = """Tu es un expert en extraction d'informations de facturation.
Tu dois extraire TOUTES les informations pertinentes depuis le texte brut du client.

Retourne UNIQUEMENT un JSON valide, sans markdown, sans explication, sans texte autour.

Format exact à respecter :
{
  "type_document": "FACTURE ou DEVIS",
  "devise": "Ar, EUR, USD, ...",
  "client": {
    "nom": "nom du client ou entreprise",
    "adresse": "adresse complète",
    "telephone": "numéro",
    "email": "email si présent"
  },
  "articles": [
    {
      "designation": "description du produit/service",
      "quantite": 1,
      "prix_unitaire": 0
    }
  ],
  "tva_pourcentage": 20,
  "remise_pourcentage": 0,
  "remise_montant": 0,
  "conditions_paiement": "conditions si mentionnées"
}

RÈGLES IMPORTANTES :
- Si le type n'est pas précisé, mettre "FACTURE"
- Si la devise n'est pas précisée, mettre "Ar"
- Pour les articles : extrais même si c'est implicite (ex: "site web 500000" = 1 article)
- Quantité par défaut = 1 si non précisée
- Prix unitaire = prix mentionné pour cet article
- Si tu vois "TVA 20%", mets 20
- Si tu vois "remise 10%", mets remise_pourcentage: 10
- Si une info manque, mets une chaîne vide "" ou 0
- NE JAMAIS inventer d'informations qui ne sont pas dans le texte"""

    payload = {
        "model": model,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extrais les infos de facturation depuis ce texte :\n\n{raw}"}
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
            print(f"❌ Erreur API : {resp.text[:500]}")
            return None

        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        print(f"📝 Réponse IA : {content[:200]}...")
        return extract_json(content)

    except Exception as e:
        print(f"❌ Exception IA : {e}")
        return None


def sanitize_articles(articles):
    """Nettoie et valide la liste d'articles."""
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

        quantite = parse_number(
            art.get("quantite") or art.get("quantity") or art.get("qty"),
            1
        )
        if quantite <= 0:
            quantite = 1

        prix = parse_number(
            art.get("prix_unitaire") or art.get("price") or
            art.get("prix") or art.get("montant"),
            0
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
    """Fallback parsing regex si l'IA échoue."""
    print("🔄 Mode fallback : parsing regex...")

    data = {
        "client_name": "",
        "client_address": "",
        "client_phone": "",
        "articles": []
    }

    lines = str(raw).strip().split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Essayer de trouver des prix (nombres avec Ar, EUR, $, €)
        price_matches = re.findall(r'(\d[\d\s.,]*\d)\s*(?:ar|€|\$|eur|usd)?', line, re.I)

        # Si on trouve un prix, essayer de trouver la désignation avant
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

    if not raw.strip():
        print("❌ CLIENT_INFOS est vide")
        sys.exit(1)

    print("=" * 60)
    print("📥 Texte reçu du client :")
    print("-" * 60)
    print(raw[:500])
    print("-" * 60)

    vendor = load_vendor()

    # 1. Essayer l'IA d'abord
    ai_result = call_ai(raw)

    client = {"nom": "", "adresse": "", "telephone": "", "email": ""}
    articles = []
    type_doc = "FACTURE"
    devise = "Ar"
    tva = 0
    remise_pct = 0
    remise_montant = 0
    conditions = "Paiement à réception de facture."

    # 2. Si l'IA a réussi, utiliser ses résultats
    if ai_result and isinstance(ai_result, dict):
        print("✅ IA a extrait les informations avec succès")

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

    # 3. Si pas d'articles via IA, essayer fallback
    if not articles:
        fallback = fallback_parse(raw)
        articles = sanitize_articles(fallback.get("articles"))

    # 4. Si toujours pas de nom client, utiliser l'email
    if not client.get("nom"):
        if email_to and "@" in email_to:
            client["nom"] = email_to.split("@")[0].replace(".", " ").title()
        else:
            client["nom"] = "Client"

    # 5. Validation finale
    if not articles:
        print("❌ Aucun article trouvé dans le texte")
        print("💡 Essaie d'inclure les articles dans ton texte, ex :")
        print("   'Développement site web 1 500 000 Ar, maintenance 300 000 Ar'")
        sys.exit(1)

    # 6. Construire le JSON final
    invoice = {
        "type_document": type_doc if type_doc in ("FACTURE", "DEVIS") else "FACTURE",
        "devise": devise,
        "vendeur": vendor,
        "client": client,
        "articles": articles,
        "tva_pourcentage": tva,
        "remise_pourcentage": remise_pct,
        "remise_montant": remise_montant,
        "conditions_paiement": conditions,
        "mentions_legales": "",
        "couleur_accent": "#2E5CFF",
        "couleur_texte": "#000000",
        "couleur_fond_alternee": "#f5f5f5",
        "taille_papier": "A4",
        "dossier_sortie": "out"
    }

    Path("invoice.json").write_text(
        json.dumps(invoice, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print("✅ invoice.json créé avec succès !")
    print("=" * 60)
    print(f"📋 Type    : {invoice['type_document']}")
    print(f"👤 Client  : {invoice['client'].get('nom')}")
    print(f"📍 Adresse : {invoice['client'].get('adresse') or '(non renseignée)'}")
    print(f"💰 Devise  : {invoice['devise']}")
    print(f"📦 Articles: {len(invoice['articles'])}")
    for i, art in enumerate(invoice['articles'], 1):
        print(f"   {i}. {art['designation']} x{art['quantite']} @ {art['prix_unitaire']}")
    print(f"📊 TVA     : {invoice['tva_pourcentage']}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
