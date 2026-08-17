#!/usr/bin/env python3
"""
Transforme les informations client brutes en invoice.json.
Utilise une IA si AI_API_KEY est configuré, sinon parsing automatique.
"""

import os
import json
import re
from pathlib import Path


def parse_number(value, default=0.0):
    if value is None:
        return default
    s = str(value).strip()
    if not s:
        return default
    s = s.replace(" ", "").replace("\u00a0", "")
    s = s.replace(",", ".").replace("%", "")
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
        "nom": "Mon Entreprise",
        "adresse": "",
        "telephone": "",
        "email": "",
        "nif": "",
        "stat": "",
        "logo": ""
    }


def parse_articles(text):
    items = []
    if not text:
        return items
    text = str(text)
    text = re.sub(r"(?i)^\s*(articles?|services?|produits?)\s*:\s*", "", text.strip())
    chunks = re.split(r"[,|]", text)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        chunk = re.sub(r"^[-*•]\s*", "", chunk)
        m = re.search(
            r"(?P<name>.+?)\s*(?:x|\*|:)?\s*(?P<qty>\d+(?:[.,]\d+)?)\s*(?:à|@|:| )\s*(?P<price>\d+(?:[.,]\d+)?)\s*$",
            chunk, flags=re.I
        )
        if m:
            name = m.group("name").strip(" :-")
            qty = parse_number(m.group("qty"), 1)
            price = parse_number(m.group("price"), 0)
            if name and qty > 0:
                items.append({"designation": name, "quantite": qty, "prix_unitaire": price})
            continue
        m = re.search(r"(?P<name>.+?)\s*[:=]\s*(?P<price>\d+(?:[.,]\d+)?)\s*$", chunk)
        if m:
            name = m.group("name").strip()
            price = parse_number(m.group("price"), 0)
            if name:
                items.append({"designation": name, "quantite": 1, "prix_unitaire": price})
            continue
        m = re.search(r"(?P<name>.+?)\s+(?P<price>\d+(?:[.,]\d+)?)\s*$", chunk)
        if m:
            name = m.group("name").strip()
            price = parse_number(m.group("price"), 0)
            if name:
                items.append({"designation": name, "quantite": 1, "prix_unitaire": price})
    return items


def parse_structured(text):
    data = {"articles": []}
    if not text:
        return data
    normalized = str(text).replace("\r", " ").replace("\n", ";")
    parts = re.split(r"[;|]", normalized)
    article_parts = []
    for part in parts:
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if not value:
            continue
        if key in ("nom", "client", "société", "societe", "entreprise", "customer", "name"):
            data["client_name"] = value
        elif key in ("adresse", "address", "adr", "adresse client"):
            data["client_address"] = value
        elif key in ("tel", "telephone", "téléphone", "phone", "mobile", "tél"):
            data["client_phone"] = value
        elif key in ("email", "mail", "e-mail"):
            data["client_email"] = value
        elif key in ("tva", "vat", "tax", "tva %", "tva pourcentage"):
            data["tva"] = parse_number(value, 0)
        elif key in ("devise", "currency", "monnaie"):
            data["devise"] = value
        elif key in ("type", "type_document", "document", "type document"):
            data["type_document"] = value.upper()
        elif key in ("articles", "article", "services", "service", "produits", "produit"):
            article_parts.append(value)
        elif key in ("conditions", "conditions_paiement", "paiement", "condition"):
            data["conditions"] = value
        elif key in ("remise", "remise %", "discount"):
            data["remise_pct"] = parse_number(value, 0)
    if article_parts:
        data["articles"] = parse_articles(", ".join(article_parts))
    if not data.get("articles"):
        data["articles"] = parse_articles(text)
    return data


def extract_json(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        return text[start:end]
    return text


def call_ai(raw):
    api_key = os.getenv("AI_API_KEY")
    if not api_key:
        return None
    url = os.getenv("AI_API_URL", "https://api.openai.com/v1/chat/completions")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    system_prompt = """
Tu es un assistant qui transforme des informations client brutes en JSON strict pour une facture.
Retourne UNIQUEMENT un JSON valide, sans texte autour, sans markdown.
Format attendu :
{
  "type_document": "FACTURE",
  "devise": "Ar",
  "client": {"nom": "", "adresse": "", "telephone": ""},
  "articles": [{"designation": "", "quantite": 1, "prix_unitaire": 0}],
  "tva_pourcentage": 0,
  "remise_pourcentage": 0,
  "remise_montant": 0,
  "conditions_paiement": ""
}
"""
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw}
        ]
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        import requests
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code != 200:
            print(f"⚠️ IA HTTP {resp.status_code}")
            return None
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(extract_json(content))
    except Exception as e:
        print(f"⚠️ IA non disponible : {e}")
        return None


def sanitize_articles(raw_articles):
    items = []
    if not isinstance(raw_articles, list):
        return items
    for article in raw_articles:
        if not isinstance(article, dict):
            continue
        designation = str(article.get("designation") or article.get("name") or "").strip()
        quantite = parse_number(article.get("quantite") or article.get("quantity"), 1)
        prix = parse_number(article.get("prix_unitaire") or article.get("price"), 0)
        if designation and quantite > 0:
            items.append({"designation": designation, "quantite": quantite, "prix_unitaire": prix})
    return items


def main():
    raw = os.getenv("CLIENT_INFOS", "")
    if not raw.strip():
        raise SystemExit("❌ CLIENT_INFOS est vide")
    vendor = load_vendor()
    parsed = parse_structured(raw)
    ai_raw = call_ai(raw)
    ai = {}
    if isinstance(ai_raw, dict):
        if isinstance(ai_raw.get("client"), dict) and ai_raw["client"].get("nom"):
            ai["client"] = {
                "nom": str(ai_raw["client"].get("nom", "")).strip(),
                "adresse": str(ai_raw["client"].get("adresse", "")).strip(),
                "telephone": str(ai_raw["client"].get("telephone", "")).strip()
            }
        articles_ai = sanitize_articles(ai_raw.get("articles"))
        if articles_ai:
            ai["articles"] = articles_ai
        for key in ("type_document", "devise", "conditions_paiement"):
            if isinstance(ai_raw.get(key), str):
                ai[key] = ai_raw[key]
        for key in ("tva_pourcentage", "remise_pourcentage", "remise_montant"):
            if key in ai_raw:
                ai[key] = parse_number(ai_raw.get(key), 0)
    client = ai.get("client") or {
        "nom": parsed.get("client_name", ""),
        "adresse": parsed.get("client_address", ""),
        "telephone": parsed.get("client_phone", "")
    }
    if not client.get("nom"):
        email = os.getenv("EMAIL_TO", "")
        if email and "@" in email:
            client["nom"] = email.split("@")[0].title()
    articles = ai.get("articles") or parsed.get("articles", [])
    invoice = {
        "type_document": str(ai.get("type_document") or parsed.get("type_document") or "FACTURE").upper(),
        "devise": ai.get("devise") or parsed.get("devise") or "Ar",
        "vendeur": vendor,
        "client": client,
        "articles": articles,
        "tva_pourcentage": parse_number(ai.get("tva_pourcentage"), parsed.get("tva", 0)),
        "remise_pourcentage": parse_number(ai.get("remise_pourcentage"), parsed.get("remise_pct", 0)),
        "remise_montant": parse_number(ai.get("remise_montant"), 0),
        "conditions_paiement": ai.get("conditions_paiement") or parsed.get("conditions") or "Paiement à réception de facture.",
        "mentions_legales": "",
        "couleur_accent": "#2E5CFF",
        "couleur_texte": "#000000",
        "couleur_fond_alternee": "#f5f5f5",
        "taille_papier": "A4",
        "dossier_sortie": "out"
    }
    if not invoice["client"].get("nom"):
        raise SystemExit("❌ Nom client introuvable. Ajoute au moins : Nom: ...")
    if not invoice["articles"]:
        raise SystemExit("❌ Articles introuvables. Exemple : Articles: Développement x1 à 1500000, Maintenance x1 à 300000")
    Path("invoice.json").write_text(json.dumps(invoice, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✅ invoice.json créé")
    print(f"- Client : {invoice['client'].get('nom')}")
    print(f"- Articles : {len(invoice['articles'])}")
    print(f"- Devise : {invoice['devise']}")
    print(f"- TVA : {invoice['tva_pourcentage']}%")


if __name__ == "__main__":
    main()
