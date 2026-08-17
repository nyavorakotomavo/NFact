#!/usr/bin/env python3
"""Envoie le PDF au client par email via Resend API."""

import os
import sys
import json
import base64
from pathlib import Path
import requests


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


def formater_montant(montant: float, devise: str) -> str:
    try:
        entier = int(round(montant))
        formatte = f"{entier:,}".replace(",", " ")
        return f"{formatte} {devise}"
    except Exception:
        return f"0 {devise}"


def main():
    resend_api_key = os.getenv("RESEND_API_KEY")
    email_from = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
    email_to = os.getenv("EMAIL_TO")
    config_path = os.getenv("CONFIG_PATH", "invoice.json")

    if not resend_api_key:
        print("❌ Secret manquant : RESEND_API_KEY")
        sys.exit(1)

    if not email_to:
        print("❌ Email client manquant")
        sys.exit(1)

    pdfs = sorted(Path("out").glob("*.pdf"))
    if not pdfs:
        print("❌ Aucun PDF à envoyer")
        sys.exit(1)

    client_name = ""
    total_text = ""

    if Path(config_path).is_file():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            client_name = config.get("client", {}).get("nom", "")
            devise = config.get("devise", "Ar")
            total = calculer_total(config)
            total_text = formater_montant(total, devise)
        except Exception:
            pass

    subject = "Votre facture / devis"
    body = f"Bonjour {client_name},\n\n"
    body += "Veuillez trouver votre document en pièce jointe.\n\n"
    if total_text:
        body += f"Montant total : {total_text}\n\n"
    body += "Merci de votre confiance.\n"

    attachments = []
    for pdf in pdfs:
        pdf_bytes = pdf.read_bytes()
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        attachments.append({
            "filename": pdf.name,
            "content": pdf_b64
        })

    payload = {
        "from": email_from,
        "to": [email_to],
        "subject": subject,
        "text": body,
        "attachments": attachments
    }

    headers = {
        "Authorization": f"Bearer {resend_api_key}",
        "Content-Type": "application/json"
    }

    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers=headers,
            json=payload,
            timeout=30
        )

        if resp.status_code == 200:
            print(f"✅ Email envoyé à {email_to}")
        else:
            print(f"❌ Erreur Resend ({resp.status_code}): {resp.text}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Erreur lors de l'envoi : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
