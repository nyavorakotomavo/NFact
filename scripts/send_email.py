#!/usr/bin/env python3
"""Envoie le PDF au client par email."""

import os
import sys
import json
import smtplib
from pathlib import Path
from email.message import EmailMessage


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
    smtp_host = os.getenv("EMAIL_SMTP_HOST")
    smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587") or 587)
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")
    email_to = os.getenv("EMAIL_TO")
    config_path = os.getenv("CONFIG_PATH", "invoice.json")
    if not smtp_host:
        print("❌ Secret manquant : EMAIL_SMTP_HOST")
        sys.exit(1)
    if not email_user:
        print("❌ Secret manquant : EMAIL_USER")
        sys.exit(1)
    if not email_pass:
        print("❌ Secret manquant : EMAIL_PASS")
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
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = email_user
    msg["To"] = email_to
    msg.set_content(body)
    for pdf in pdfs:
        msg.add_attachment(pdf.read_bytes(), maintype="application", subtype="pdf", filename=pdf.name)
    try:
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        server.login(email_user, email_pass)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email envoyé à {email_to}")
    except Exception as e:
        print(f"❌ Erreur email : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
