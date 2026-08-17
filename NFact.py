#!/usr/bin/env python3
"""
NFact - Générateur de factures/devis PDF (version offline)
Usage:
    python NFact.py                              → mode interactif
    python NFact.py --config client.json         → depuis un JSON
    python NFact.py --list                       → liste des clients
"""
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4, letter, A5
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image as RLImage,
)

# Emplacements
PROJECT_DIR = Path(__file__).parent.resolve()
CLIENTS_DIR = PROJECT_DIR / "clients"
COMPTEUR_FILE = PROJECT_DIR / ".compteur.json"
DEFAULT_OUTPUT = PROJECT_DIR / "output"

DEFAULT_CONFIG = {
    "type_document": "FACTURE",
    "devise": "Ar",
    "vendeur": {
        "nom": "Mon Entreprise",
        "adresse": "",
        "telephone": "",
        "email": "",
        "nif": "",
        "stat": "",
        "logo": "",
    },
    "client": {"nom": "Client", "adresse": "", "telephone": "", "email": ""},
    "articles": [],
    "tva_pourcentage": 0,
    "remise_pourcentage": 0,
    "remise_montant": 0,
    "conditions_paiement": "Paiement à réception de facture.",
    "mentions_legales": "",
    "couleur_accent": "#1a3c6e",
    "couleur_texte": "#000000",
    "couleur_fond_alternee": "#f5f5f5",
    "taille_papier": "A4",
}

PAPIER = {"A4": A4, "LETTER": letter, "A5": A5}


def deep_merge(default, override):
    result = dict(default)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def prochain_numero(prefixe="FAC"):
    compteur = 1
    if COMPTEUR_FILE.exists():
        try:
            data = json.loads(COMPTEUR_FILE.read_text())
            compteur = data.get(prefixe, 0) + 1
        except Exception:
            compteur = 1
    try:
        data = {}
        if COMPTEUR_FILE.exists():
            data = json.loads(COMPTEUR_FILE.read_text())
        data[prefixe] = compteur
        COMPTEUR_FILE.write_text(json.dumps(data))
    except Exception:
        pass
    return f"{prefixe}-{datetime.now().strftime('%Y')}-{compteur:04d}"


def formater(montant, devise):
    try:
        entier = int(round(montant))
        return f"{entier:,}".replace(",", " ") + f" {devise}"
    except Exception:
        return f"0 {devise}"


def calculer_totaux(config):
    sous_total = sum(
        float(a.get("quantite", 0)) * float(a.get("prix_unitaire", 0))
        for a in config["articles"]
    )
    remise = min(
        (sous_total * float(config.get("remise_pourcentage", 0)) / 100)
        + float(config.get("remise_montant", 0)),
        sous_total,
    )
    base = sous_total - remise
    tva_pct = float(config.get("tva_pourcentage", 0))
    montant_tva = base * tva_pct / 100
    return {
        "lignes": [
            {
                "designation": a.get("designation", ""),
                "quantite": float(a.get("quantite", 0)),
                "prix_unitaire": float(a.get("prix_unitaire", 0)),
                "total_ligne": float(a.get("quantite", 0)) * float(a.get("prix_unitaire", 0)),
            }
            for a in config["articles"]
        ],
        "sous_total": sous_total,
        "remise_totale": remise,
        "tva_pct": tva_pct,
        "montant_tva": montant_tva,
        "total_final": base + montant_tva,
    }


def hex_color(v, defaut):
    try:
        return colors.HexColor(v)
    except Exception:
        return colors.HexColor(defaut)


def generer_pdf(config, chemin_sortie):
    devise = config.get("devise", "Ar")
    c_accent = hex_color(config.get("couleur_accent", "#1a3c6e"), "#1a3c6e")
    c_texte = hex_color(config.get("couleur_texte", "#000000"), "#000000")
    c_fond = hex_color(config.get("couleur_fond_alternee", "#f5f5f5"), "#f5f5f5")
    papier = str(config.get("taille_papier", "A4")).upper()
    taille = PAPIER.get(papier, A4)
    totaux = calculer_totaux(config)

    marge = 15 * mm
    doc = SimpleDocTemplate(
        str(chemin_sortie), pagesize=taille,
        topMargin=marge, bottomMargin=marge,
        leftMargin=marge, rightMargin=marge,
    )
    largeur = taille[0] - 2 * marge
    styles = getSampleStyleSheet()

    s_titre = ParagraphStyle("T", parent=styles["Title"], textColor=c_accent,
                             fontSize=22, alignment=TA_RIGHT, spaceAfter=2)
    s_norm_d = ParagraphStyle("ND", parent=styles["Normal"],
                              alignment=TA_RIGHT, textColor=c_texte)
    s_norm = ParagraphStyle("N", parent=styles["Normal"], textColor=c_texte)
    s_sec = ParagraphStyle("S", parent=styles["Normal"], fontSize=10,
                           textColor=colors.grey, fontName="Helvetica-Bold", spaceAfter=4)
    s_petit = ParagraphStyle("P", parent=styles["Normal"],
                             fontSize=8, textColor=colors.grey)

    story = []
    vendeur = config["vendeur"]
    logo = vendeur.get("logo", "")

    # En-tête
    gauche = []
    if logo and os.path.isfile(logo):
        try:
            gauche.append(RLImage(logo, width=35 * mm, height=35 * mm, kind="proportional"))
        except Exception:
            pass
    infos_v = f"<b>{vendeur.get('nom','')}</b><br/>"
    for c, l in [("adresse", ""), ("telephone", "Tél: "), ("email", ""),
                 ("nif", "NIF: "), ("stat", "STAT: ")]:
        if vendeur.get(c):
            prefix = l
            infos_v += f"{prefix}{vendeur[c]}<br/>"
    gauche.append(Paragraph(infos_v, s_norm))

    type_doc = config.get("type_document", "FACTURE").upper()
    numero = config.get("numero") or prochain_numero("FAC" if type_doc == "FACTURE" else "DEV")
    date_doc = config.get("date") or datetime.now().strftime("%d/%m/%Y")

    droite = [
        Paragraph(type_doc, s_titre),
        Paragraph(f"N° {numero}", s_norm_d),
        Paragraph(f"Date: {date_doc}", s_norm_d),
    ]

    t_entete = Table([[gauche, droite]],
                     colWidths=[largeur * 0.57, largeur * 0.43])
    t_entete.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(t_entete)
    story.append(Spacer(1, 10 * mm))

    # Client
    client = config["client"]
    infos_c = f"<b>{client.get('nom','')}</b><br/>"
    if client.get("adresse"):
        infos_c += f"{client['adresse']}<br/>"
    if client.get("telephone"):
        infos_c += f"Tél: {client['telephone']}<br/>"
    if client.get("email"):
        infos_c += f"{client['email']}"
    story.append(Paragraph("FACTURÉ À" if type_doc == "FACTURE" else "DEVIS POUR", s_sec))
    story.append(Paragraph(infos_c, s_norm))
    story.append(Spacer(1, 8 * mm))

    # Articles
    data_t = [["Désignation", "Qté", "Prix Unit.", "Total"]]
    for l in totaux["lignes"]:
        data_t.append([
            Paragraph(l["designation"], s_norm),
            f"{l['quantite']:g}",
            formater(l["prix_unitaire"], devise),
            formater(l["total_ligne"], devise),
        ])
    t_art = Table(data_t, colWidths=[largeur * 0.44, largeur * 0.13,
                                      largeur * 0.215, largeur * 0.215])
    t_art.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_fond]),
        ("TEXTCOLOR", (0, 1), (-1, -1), c_texte),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_art)
    story.append(Spacer(1, 6 * mm))

    # Totaux
    lignes_t = [["Sous-total", formater(totaux["sous_total"], devise)]]
    if totaux["remise_totale"] > 0:
        lignes_t.append(["Remise", "- " + formater(totaux["remise_totale"], devise)])
    if totaux["tva_pct"] > 0:
        lignes_t.append([f"TVA ({totaux['tva_pct']:g}%)",
                         formater(totaux["montant_tva"], devise)])
    lignes_t.append(["TOTAL", formater(totaux["total_final"], devise)])
    t_tot = Table(lignes_t, colWidths=[largeur * 0.21, largeur * 0.21])
    t_tot.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (0, -1), (-1, -1), 1, c_accent),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("TEXTCOLOR", (0, -1), (-1, -1), c_accent),
    ]))
    wrapper = Table([[None, t_tot]],
                    colWidths=[largeur * 0.55, largeur * 0.45])
    story.append(wrapper)
    story.append(Spacer(1, 12 * mm))

    if config.get("conditions_paiement"):
        story.append(Paragraph("CONDITIONS DE PAIEMENT", s_sec))
        story.append(Paragraph(config["conditions_paiement"], s_norm))
        story.append(Spacer(1, 4 * mm))
    if config.get("mentions_legales"):
        story.append(Paragraph(config["mentions_legales"], s_petit))
        story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}", s_petit))

    doc.build(story)
    return numero


def demander(q, d=""):
    r = input(f"{q}" + (f" [{d}]" if d else "") + " : ").strip()
    return r if r else d


def demander_nb(q, d=0.0):
    while True:
        try:
            return float(demander(q, str(d)).replace(",", "."))
        except ValueError:
            print("  → Nombre invalide.")


def mode_interactif():
    print("\n" + "=" * 50)
    print("  NFact - Mode interactif (offline)")
    print("=" * 50)
    config = json.loads(json.dumps(DEFAULT_CONFIG))

    # Charger vendeur par défaut si existe
    vend_file = PROJECT_DIR / "config" / "vendeur.json"
    if vend_file.exists():
        try:
            v = json.loads(vend_file.read_text())
            config["vendeur"] = deep_merge(config["vendeur"], v)
            print(f"✅ Vendeur chargé : {v.get('nom')}")
        except Exception:
            pass

    type_doc = demander("Type (FACTURE/DEVIS)", "FACTURE").upper()
    config["type_document"] = type_doc if type_doc in ("FACTURE", "DEVIS") else "FACTURE"

    print("\n--- Client ---")
    config["client"]["nom"] = demander("Nom du client")
    config["client"]["adresse"] = demander("Adresse", "")
    config["client"]["telephone"] = demander("Téléphone", "")
    config["client"]["email"] = demander("Email", "")

    config["devise"] = demander("Devise (Ar/EUR/USD)", "Ar")

    print("\n--- Articles (désignation vide = fin) ---")
    articles = []
    while True:
        d = demander(f"Article #{len(articles)+1} - désignation")
        if not d:
            break
        q = demander_nb("  Quantité", 1)
        p = demander_nb("  Prix unitaire", 0)
        articles.append({"designation": d, "quantite": q, "prix_unitaire": p})
    config["articles"] = articles

    config["tva_pourcentage"] = demander_nb("TVA % (0 si aucune)", 0)
    config["remise_pourcentage"] = demander_nb("Remise % (0 si aucune)", 0)
    config["conditions_paiement"] = demander("Conditions", "Paiement à réception.")

    # Sauvegarder le client si demandé
    if input("\nSauvegarder ce client pour plus tard ? (o/N) : ").strip().lower() == "o":
        slug = "".join(c if c.isalnum() else "_" for c in config["client"]["nom"]).strip("_")
        client_file = CLIENTS_DIR / f"{slug}.json"
        client_file.write_text(json.dumps({
            "client": config["client"],
            "vendeur": config["vendeur"],
            "devise": config["devise"],
            "conditions_paiement": config["conditions_paiement"],
        }, ensure_ascii=False, indent=2))
        print(f"💾 Client sauvegardé : clients/{slug}.json")

    return config


def lister_clients():
    print("\n📋 Clients enregistrés :")
    print("-" * 50)
    if not CLIENTS_DIR.exists():
        print("  (aucun)")
        return
    clients = sorted(CLIENTS_DIR.glob("*.json"))
    if not clients:
        print("  (aucun)")
        return
    for c in clients:
        try:
            data = json.loads(c.read_text())
            nom = data.get("client", {}).get("nom", "?")
            print(f"  • {c.stem:<25} → {nom}")
        except Exception:
            print(f"  • {c.stem} (erreur de lecture)")
    print(f"\nUsage : python NFact.py --config clients/NOM.json")


def charger_config(chemin):
    p = Path(chemin)
    if not p.exists():
        # Essayer dans clients/
        p = CLIENTS_DIR / f"{chemin}.json"
    if not p.exists():
        print(f"❌ Fichier introuvable : {chemin}")
        sys.exit(1)
    user = json.loads(p.read_text())
    return deep_merge(DEFAULT_CONFIG, user)


def main():
    parser = argparse.ArgumentParser(description="NFact - Générateur de factures offline")
    parser.add_argument("--config", help="Fichier JSON client (ou nom dans clients/)")
    parser.add_argument("--list", action="store_true", help="Liste des clients")
    parser.add_argument("--output-dir", help="Dossier de sortie")
    parser.add_argument("--type", choices=["FACTURE", "DEVIS"], help="Type de document")
    parser.add_argument("--articles", nargs="*", help="Articles : 'desc:prix:qte'")
    args = parser.parse_args()

    if args.list:
        lister_clients()
        return 0

    if args.config:
        config = charger_config(args.config)
    else:
        config = mode_interactif()

    if args.type:
        config["type_document"] = args.type

    if args.articles:
        arts = []
        for a in args.articles:
            parts = a.split(":")
            if len(parts) == 1:
                arts.append({"designation": parts[0], "quantite": 1, "prix_unitaire": 0})
            elif len(parts) == 2:
                arts.append({"designation": parts[0], "quantite": 1,
                             "prix_unitaire": float(parts[1])})
            elif len(parts) >= 3:
                arts.append({"designation": parts[0], "quantite": float(parts[2]),
                             "prix_unitaire": float(parts[1])})
        if arts:
            config["articles"] = arts

    # Validation minimale
    if not config["vendeur"].get("nom"):
        print("❌ Nom du vendeur manquant")
        return 1
    if not config["client"].get("nom"):
        print("❌ Nom du client manquant")
        return 1
    if not config["articles"]:
        print("❌ Aucun article")
        return 1

    # Dossier de sortie : prioritaire > Android Download > local
    if args.output_dir:
        out = Path(args.output_dir)
    elif (Path.home() / "storage" / "shared" / "Download").exists():
        out = Path.home() / "storage" / "shared" / "Download" / "NFact"
    elif Path("/sdcard/Download").exists():
        out = Path("/sdcard/Download") / "NFact"
    else:
        out = DEFAULT_OUTPUT
    out.mkdir(parents=True, exist_ok=True)

    client_slug = "".join(c if c.isalnum() else "_"
                          for c in config["client"]["nom"]).strip("_") or "client"
    date_slug = datetime.now().strftime("%Y-%m-%d")
    nom_pdf = f"{config['type_document'].lower()}_{date_slug}_{client_slug}.pdf"
    chemin = out / nom_pdf

    numero = generer_pdf(config, chemin)
    print(f"\n✅ {config['type_document']} générée !")
    print(f"   Numéro  : {numero}")
    print(f"   Total   : {formater(calculer_totaux(config)['total_final'], config['devise'])}")
    print(f"   Fichier : {chemin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
