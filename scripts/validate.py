#!/usr/bin/env python3
"""Validation automatique avant envoi."""

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
    # Extraire uniquement le premier nombre trouvé (ignore "ar", "EUR", "$", etc.)
    match = re.search(r'-?\d[\d\s.,]*', s)
    if not match:
        return default
    s = match.group(0)
    s = s.replace(" ", "").replace("\u00a0", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return default


def calculer_total(config: dict) -> float:
    sous_total = 0.0
    for article in config.get("articles", []):
        qte = float(article.get("quantite", 0) or 0)
        prix = float(article.get("prix_unitaire", 0) or 0)
        sous_total += qte * prix
    remise_pct = float(config.get("remise_pourcentage", 0) or 0)
    remise_montant = float(config.get("remise_montant", 0) or 0)
    remise = (sous_total * remise_pct / 100.0) + remise_montant
    remise = min(remise, sous_total)
    base = sous_total - remise
    tva_pct = float(config.get("tva_pourcentage", 0) or 0)
    return base + (base * tva_pct / 100.0)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate.py invoice.json")
        sys.exit(1)
    config_path = sys.argv[1]
    erreurs = []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ JSON invalide : {e}")
        sys.exit(1)
    vendeur = config.get("vendeur", {})
    client = config.get("client", {})
    articles = config.get("articles", [])
    if not vendeur.get("nom", "").strip():
        erreurs.append("Nom vendeur manquant")
    if not client.get("nom", "").strip():
        erreurs.append("Nom client manquant")
    if not articles:
        erreurs.append("Aucun article")
    for i, article in enumerate(articles, start=1):
        if not article.get("designation", "").strip():
            erreurs.append(f"Article {i}: désignation manquante")
        qte = parse_number(article.get("quantite"), -1)
        if qte <= 0:
            erreurs.append(f"Article {i}: quantité invalide")
        prix = parse_number(article.get("prix_unitaire"), -1)
        if prix < 0:
            erreurs.append(f"Article {i}: prix invalide")
    total = 0
    try:
        total = calculer_total(config)
        if total <= 0:
            erreurs.append("Total inférieur ou égal à 0")
    except Exception:
        erreurs.append("Impossible de calculer le total")
    payment_amount = os.getenv("PAYMENT_AMOUNT", "").strip()
    if payment_amount:
        payment = parse_number(payment_amount, -1)
        if payment < 0:
            erreurs.append(f"Montant payé invalide ({payment_amount!r})")
        elif abs(payment - total) > 1:
            erreurs.append(f"Montant payé ({payment}) différent du total ({total})")
    pdfs = list(Path("out").glob("*.pdf"))
    if not pdfs:
        erreurs.append("Aucun PDF généré dans out/")
    else:
        for pdf in pdfs:
            if pdf.stat().st_size < 1024:
                erreurs.append(f"PDF probablement vide : {pdf.name}")
    if erreurs:
        print("❌ Validation refusée :")
        for erreur in erreurs:
            print(f"- {erreur}")
        sys.exit(1)
    print("✅ Validation OK")
    print(f"- Client : {client.get('nom')}")
    print(f"- Articles : {len(articles)}")
    print(f"- Total : {total}")
    print(f"- PDF : {len(pdfs)}")


if __name__ == "__main__":
    main()
