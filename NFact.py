#!/usr/bin/env python3
"""
Générateur de Factures / Devis PDF — Masterclass Edition
=========================================================
10 styles professionnels inspirés des références du marché :
Stripe, QuickBooks, FreshBooks, Wave, Square, Canva, etc.

Usage :
    python NFact.py                            → mode interactif
    python NFact.py --config client.json       → mode automatique
    python NFact.py --config client.json --style wave
    python NFact.py --list-styles              → liste des styles
    python NFact.py --new-config out.json      → modèle JSON vide

Dépendances :
    pip install reportlab --break-system-packages
"""

import json
import os
import sys
import argparse
from datetime import datetime
from typing import Optional, Callable, List, Dict, Any

from reportlab.lib.pagesizes import A4, letter, A5
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    Image as RLImage,
)

# ═══════════════════════════════════════════════════════════════════════════
#  1. DÉFINITION DES 10 STYLES PROFESSIONNELS
# ═══════════════════════════════════════════════════════════════════════════

THEMES: Dict[str, dict] = {

    # ── 1. Stripe Minimaliste ──────────────────────────────────────────────
    "stripe": {
        "nom": "Stripe Minimaliste",
        "description": "Épuré, moderne, inspiré de Stripe. Idéal tech / startups.",
        "couleur_primaire": "#635BFF",
        "couleur_texte": "#0A2540",
        "couleur_secondaire": "#425466",
        "couleur_ligne_tableau": "#E6E6E6",
        "couleur_fond_entete": None,
        "couleur_fond_total": "#F6F9FC",
        "couleur_fond_alternee": None,
        "couleur_texte_entete_tableau": "#425466",
        "marge": 18,
        "espacement_sections": 10,
        "type_entete": "standard",
        "bordure_externe": False,
        "barre_laterale": False,
        "epaisseur_ligne": 0.5,
        "lignes_verticales": False,
        "padding_lignes": 6,
        "police": "Helvetica",
        "police_gras": "Helvetica-Bold",
        "taille_titre": 22,
        "taille_corps": 9,
        "taille_total": 13,
    },

    # ── 2. QuickBooks Classique ────────────────────────────────────────────
    "quickbooks": {
        "nom": "QuickBooks Classique",
        "description": "Structuré, professionnel, aspect document officiel.",
        "couleur_primaire": "#2CA01C",
        "couleur_texte": "#262626",
        "couleur_secondaire": "#555555",
        "couleur_ligne_tableau": "#D9D9D9",
        "couleur_fond_entete": "#F5F5F5",
        "couleur_fond_total": "#FAFAFA",
        "couleur_fond_alternee": None,
        "couleur_texte_entete_tableau": "#262626",
        "marge": 15,
        "espacement_sections": 8,
        "type_entete": "standard",
        "bordure_externe": True,
        "barre_laterale": False,
        "epaisseur_ligne": 0.75,
        "lignes_verticales": False,
        "padding_lignes": 5,
        "police": "Helvetica",
        "police_gras": "Helvetica-Bold",
        "taille_titre": 20,
        "taille_corps": 9,
        "taille_total": 13,
    },

    # ── 3. FreshBooks Simple ───────────────────────────────────────────────
    "freshbooks_simple": {
        "nom": "FreshBooks Simple",
        "description": "Clair, aéré, parfait pour freelances et TPE.",
        "couleur_primaire": "#00A8E1",
        "couleur_texte": "#333333",
        "couleur_secondaire": "#666666",
        "couleur_ligne_tableau": "#E0E0E0",
        "couleur_fond_entete": None,
        "couleur_fond_total": None,
        "couleur_fond_alternee": None,
        "couleur_texte_entete_tableau": "#666666",
        "marge": 16,
        "espacement_sections": 12,
        "type_entete": "standard",
        "bordure_externe": False,
        "barre_laterale": False,
        "epaisseur_ligne": 0.5,
        "lignes_verticales": False,
        "padding_lignes": 7,
        "police": "Helvetica",
        "police_gras": "Helvetica-Bold",
        "taille_titre": 22,
        "taille_corps": 9,
        "taille_total": 14,
    },

    # ── 4. FreshBooks Modern ───────────────────────────────────────────────
    "freshbooks_modern": {
        "nom": "FreshBooks Modern",
        "description": "Bannière colorée pleine largeur, impact visuel fort.",
        "couleur_primaire": "#00A8E1",
        "couleur_texte": "#333333",
        "couleur_secondaire": "#666666",
        "couleur_ligne_tableau": "#E0E0E0",
        "couleur_fond_entete": None,
        "couleur_fond_total": "#E6F7FE",
        "couleur_fond_alternee": None,
        "couleur_texte_entete_tableau": "#666666",
        "marge": 16,
        "espacement_sections": 10,
        "type_entete": "banniere",
        "bordure_externe": False,
        "barre_laterale": False,
        "epaisseur_ligne": 0.5,
        "lignes_verticales": False,
        "padding_lignes": 6,
        "police": "Helvetica",
        "police_gras": "Helvetica-Bold",
        "taille_titre": 22,
        "taille_corps": 9,
        "taille_total": 13,
    },

    # ── 5. Wave Épuré ─────────────────────────────────────────────────────
    "wave": {
        "nom": "Wave Épuré",
        "description": "Titre à gauche, logo à droite. Moderne et accessible.",
        "couleur_primaire": "#00C492",
        "couleur_texte": "#2B2B2B",
        "couleur_secondaire": "#5C5C5C",
        "couleur_ligne_tableau": "#E8E8E8",
        "couleur_fond_entete": None,
        "couleur_fond_total": None,
        "couleur_fond_alternee": None,
        "couleur_texte_entete_tableau": "#5C5C5C",
        "marge": 16,
        "espacement_sections": 10,
        "type_entete": "inverse",
        "bordure_externe": False,
        "barre_laterale": False,
        "epaisseur_ligne": 0.5,
        "lignes_verticales": False,
        "padding_lignes": 6,
        "police": "Helvetica",
        "police_gras": "Helvetica-Bold",
        "taille_titre": 24,
        "taille_corps": 9,
        "taille_total": 14,
    },

    # ── 6. Square Minimaliste ──────────────────────────────────────────────
    "square": {
        "nom": "Square Minimaliste",
        "description": "Minimalisme radical, marges larges, focus contenu.",
        "couleur_primaire": "#006AFF",
        "couleur_texte": "#1A1A1A",
        "couleur_secondaire": "#595959",
        "couleur_ligne_tableau": "#E0E0E0",
        "couleur_fond_entete": None,
        "couleur_fond_total": None,
        "couleur_fond_alternee": None,
        "couleur_texte_entete_tableau": "#595959",
        "marge": 22,
        "espacement_sections": 14,
        "type_entete": "standard",
        "bordure_externe": False,
        "barre_laterale": False,
        "epaisseur_ligne": 0.3,
        "lignes_verticales": False,
        "padding_lignes": 7,
        "police": "Helvetica",
        "police_gras": "Helvetica-Bold",
        "taille_titre": 18,
        "taille_corps": 9,
        "taille_total": 13,
    },

    # ── 7. Canva Minimaliste Blanc ─────────────────────────────────────────
    "canva_minimal": {
        "nom": "Canva Minimaliste Blanc",
        "description": "Blanc maximal, élégance par la simplicité.",
        "couleur_primaire": "#000000",
        "couleur_texte": "#1A1A1A",
        "couleur_secondaire": "#6B6B6B",
        "couleur_ligne_tableau": "#E8E8E8",
        "couleur_fond_entete": None,
        "couleur_fond_total": None,
        "couleur_fond_alternee": None,
        "couleur_texte_entete_tableau": "#6B6B6B",
        "marge": 22,
        "espacement_sections": 14,
        "type_entete": "standard",
        "bordure_externe": False,
        "barre_laterale": False,
        "epaisseur_ligne": 0.3,
        "lignes_verticales": False,
        "padding_lignes": 7,
        "police": "Helvetica",
        "police_gras": "Helvetica-Bold",
        "taille_titre": 18,
        "taille_corps": 9,
        "taille_total": 12,
    },

    # ── 8. Canva Moderne Géométrique ───────────────────────────────────────
    "canva_geometric": {
        "nom": "Canva Moderne Géométrique",
        "description": "Formes géométriques, couleurs vives, design créatif.",
        "couleur_primaire": "#2E5CFF",
        "couleur_secondaire_visuel": "#FFC107",
        "couleur_texte": "#1A1A1A",
        "couleur_secondaire": "#595959",
        "couleur_ligne_tableau": "#2E5CFF",
        "couleur_fond_entete": "#2E5CFF",
        "couleur_fond_total": "#2E5CFF",
        "couleur_fond_alternee": "#F0F4FF",
        "couleur_texte_entete_tableau": "#FFFFFF",
        "marge": 16,
        "espacement_sections": 10,
        "type_entete": "geometrique",
        "bordure_externe": False,
        "barre_laterale": False,
        "epaisseur_ligne": 0.75,
        "lignes_verticales": False,
        "padding_lignes": 6,
        "police": "Helvetica",
        "police_gras": "Helvetica-Bold",
        "taille_titre": 22,
        "taille_corps": 9,
        "taille_total": 13,
    },

    # ── 9. Classique Traditionnel (Corporate) ──────────────────────────────
    "classique": {
        "nom": "Classique Traditionnel",
        "description": "Serif, formel, institutionnel. Avocats, comptables.",
        "couleur_primaire": "#1E3A5F",
        "couleur_texte": "#000000",
        "couleur_secondaire": "#4A4A4A",
        "couleur_ligne_tableau": "#CCCCCC",
        "couleur_fond_entete": "#F0F0F0",
        "couleur_fond_total": None,
        "couleur_fond_alternee": None,
        "couleur_texte_entete_tableau": "#000000",
        "marge": 15,
        "espacement_sections": 8,
        "type_entete": "standard",
        "bordure_externe": True,
        "barre_laterale": False,
        "bordure_totale": True,
        "epaisseur_ligne": 0.75,
        "lignes_verticales": True,
        "padding_lignes": 5,
        "police": "Times-Roman",
        "police_gras": "Times-Bold",
        "taille_titre": 20,
        "taille_corps": 10,
        "taille_total": 14,
    },

    # ── 10. Créatif Freelance ──────────────────────────────────────────────
    "creatif": {
        "nom": "Créatif Freelance",
        "description": "Barre latérale colorée, typographie bold, personnalité.",
        "couleur_primaire": "#FF6B6B",
        "couleur_secondaire_visuel": "#4ECDC4",
        "couleur_texte": "#1A1A1A",
        "couleur_secondaire": "#595959",
        "couleur_ligne_tableau": "#FF6B6B",
        "couleur_fond_entete": None,
        "couleur_fond_total": "#FF6B6B",
        "couleur_fond_alternee": "#FFF5F5",
        "couleur_texte_entete_tableau": "#FF6B6B",
        "marge": 18,
        "marge_gauche_sup": 7,
        "espacement_sections": 10,
        "type_entete": "standard",
        "bordure_externe": False,
        "barre_laterale": True,
        "epaisseur_ligne": 0.75,
        "lignes_verticales": False,
        "padding_lignes": 6,
        "police": "Helvetica",
        "police_gras": "Helvetica-Bold",
        "taille_titre": 24,
        "taille_corps": 9,
        "taille_total": 14,
    },
}

PAPIER_DISPONIBLE = {"A4": A4, "LETTER": letter, "A5": A5}
COMPTEUR_FILE = ".facture_compteur.json"
STYLE_DEFAUT = "stripe"


# ═══════════════════════════════════════════════════════════════════════════
#  2. CONFIGURATION PAR DÉFAUT
# ═══════════════════════════════════════════════════════════════════════════

DEFAULT_CONFIG: Dict[str, Any] = {
    "type_document": "FACTURE",
    "numero": None,
    "date": None,
    "style": STYLE_DEFAUT,
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
    "client": {
        "nom": "Client",
        "adresse": "",
        "telephone": "",
    },
    "articles": [],
    "tva_pourcentage": 0,
    "remise_pourcentage": 0,
    "remise_montant": 0,
    "conditions_paiement": "Paiement à réception de facture.",
    "mentions_legales": "",
    "couleur_accent": None,
    "couleur_texte": None,
    "couleur_fond_alternee": None,
    "taille_papier": "A4",
    "dossier_sortie": "factures_generees",
}


# ═══════════════════════════════════════════════════════════════════════════
#  3. ERREURS & UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════

class FactureError(Exception):
    """Erreur métier claire, affichée proprement à l'utilisateur."""


def deep_merge(default: dict, override: dict) -> dict:
    result = dict(default)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def prochain_numero(prefixe: str = "FAC") -> str:
    compteur = 1
    if os.path.exists(COMPTEUR_FILE):
        try:
            with open(COMPTEUR_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            compteur = data.get(prefixe, 0) + 1
        except (json.JSONDecodeError, OSError):
            compteur = 1
    try:
        data = {}
        if os.path.exists(COMPTEUR_FILE):
            with open(COMPTEUR_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[prefixe] = compteur
        with open(COMPTEUR_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass
    annee = datetime.now().strftime("%Y")
    return f"{prefixe}-{annee}-{compteur:04d}"


def hex_color(valeur: str, defaut: str) -> colors.Color:
    try:
        return colors.HexColor(valeur)
    except Exception:
        return colors.HexColor(defaut)


def valider_config(config: dict) -> List[str]:
    erreurs: List[str] = []
    if not config["vendeur"].get("nom", "").strip():
        erreurs.append("Le nom du vendeur/entreprise est obligatoire.")
    if not config["client"].get("nom", "").strip():
        erreurs.append("Le nom du client est obligatoire.")
    if not config["articles"]:
        erreurs.append("Il faut au moins un article/service.")
    for i, art in enumerate(config["articles"], start=1):
        if not str(art.get("designation", "")).strip():
            erreurs.append(f"Article #{i} : désignation manquante.")
        try:
            qte = float(art.get("quantite", 0))
            if qte <= 0:
                erreurs.append(f"Article #{i} : la quantité doit être positive.")
        except (TypeError, ValueError):
            erreurs.append(f"Article #{i} : quantité invalide.")
        try:
            prix = float(art.get("prix_unitaire", -1))
            if prix < 0:
                erreurs.append(f"Article #{i} : prix unitaire invalide.")
        except (TypeError, ValueError):
            erreurs.append(f"Article #{i} : prix unitaire invalide.")
    tva = config.get("tva_pourcentage", 0)
    try:
        if not (0 <= float(tva) <= 100):
            erreurs.append("Le pourcentage de TVA doit être entre 0 et 100.")
    except (TypeError, ValueError):
        erreurs.append(f"TVA invalide ({tva!r}).")
    logo = config["vendeur"].get("logo", "")
    if logo and not os.path.isfile(logo):
        erreurs.append(
            f"AVERTISSEMENT (non bloquant) : logo introuvable '{logo}', "
            "la facture sera générée sans logo."
        )
    style = config.get("style", STYLE_DEFAUT)
    if style not in THEMES:
        erreurs.append(
            f"AVERTISSEMENT (non bloquant) : style '{style}' inconnu, "
            f"utilisation de '{STYLE_DEFAUT}'."
        )
    papier = str(config.get("taille_papier", "A4")).upper()
    if papier not in PAPIER_DISPONIBLE:
        erreurs.append(
            f"AVERTISSEMENT (non bloquant) : taille de papier '{papier}' inconnue, "
            "utilisation de A4."
        )
    return erreurs


def formater_montant(montant: float, devise: str) -> str:
    try:
        entier = int(round(montant))
        formatte = f"{entier:,}".replace(",", " ")
        return f"{formatte} {devise}"
    except (TypeError, ValueError):
        return f"0 {devise}"


def calculer_totaux(config: dict) -> dict:
    sous_total = 0.0
    lignes_calculees = []
    for art in config["articles"]:
        qte = float(art.get("quantite", 0))
        prix = float(art.get("prix_unitaire", 0))
        total_ligne = qte * prix
        sous_total += total_ligne
        lignes_calculees.append({
            "designation": art.get("designation", ""),
            "quantite": qte,
            "prix_unitaire": prix,
            "total_ligne": total_ligne,
        })
    remise_pct = float(config.get("remise_pourcentage", 0) or 0)
    remise_fixe = float(config.get("remise_montant", 0) or 0)
    remise_totale = min((sous_total * remise_pct / 100.0) + remise_fixe, sous_total)
    base_apres_remise = sous_total - remise_totale
    tva_pct = float(config.get("tva_pourcentage", 0) or 0)
    montant_tva = base_apres_remise * tva_pct / 100.0
    total_final = base_apres_remise + montant_tva
    return {
        "lignes": lignes_calculees,
        "sous_total": sous_total,
        "remise_totale": remise_totale,
        "base_apres_remise": base_apres_remise,
        "tva_pct": tva_pct,
        "montant_tva": montant_tva,
        "total_final": total_final,
    }


# ═══════════════════════════════════════════════════════════════════════════
#  4. MOTEUR DE GÉNÉRATION PDF
# ═══════════════════════════════════════════════════════════════════════════

class FacturePDFBuilder:

    def __init__(self, config: dict):
        self.config = config
        self.theme = self._resolve_theme()
        self.totaux = calculer_totaux(config)
        self.devise = config.get("devise", "Ar")
        self.type_doc = config.get("type_document", "FACTURE").upper()
        self.numero = config.get("numero") or prochain_numero(
            "FAC" if self.type_doc == "FACTURE" else "DEV"
        )
        self.date_doc = config.get("date") or datetime.now().strftime("%d/%m/%Y")

        self.couleur_primaire = hex_color(
            config.get("couleur_accent") or self.theme["couleur_primaire"],
            self.theme["couleur_primaire"],
        )
        self.couleur_texte = hex_color(
            config.get("couleur_texte") or self.theme["couleur_texte"],
            self.theme["couleur_texte"],
        )
        self.couleur_secondaire = hex_color(
            self.theme.get("couleur_secondaire", "#666666"), "#666666"
        )
        self.couleur_ligne = hex_color(
            self.theme.get("couleur_ligne_tableau", "#E0E0E0"), "#E0E0E0"
        )

        papier_nom = str(config.get("taille_papier", "A4")).upper()
        self.taille_page = PAPIER_DISPONIBLE.get(papier_nom, A4)
        self.marge = self.theme["marge"] * mm
        if self.theme.get("barre_laterale"):
            self.marge_gauche = (self.theme["marge"] + self.theme.get("marge_gauche_sup", 7)) * mm
        else:
            self.marge_gauche = self.marge
        self.largeur_utile = self.taille_page[0] - self.marge_gauche - self.marge

        self._create_paragraph_styles()

    def _resolve_theme(self) -> dict:
        style_name = self.config.get("style", STYLE_DEFAUT)
        if style_name not in THEMES:
            style_name = STYLE_DEFAUT
        return dict(THEMES[style_name])

    def _create_paragraph_styles(self):
        base = getSampleStyleSheet()
        t = self.theme
        self.pstyles = {
            "titre": ParagraphStyle(
                "TitreDoc", parent=base["Title"],
                fontName=t["police_gras"], fontSize=t["taille_titre"],
                textColor=self.couleur_primaire, alignment=TA_RIGHT,
                spaceAfter=2, leading=t["taille_titre"] + 4,
            ),
            "titre_gauche": ParagraphStyle(
                "TitreGauche", parent=base["Title"],
                fontName=t["police_gras"], fontSize=t["taille_titre"],
                textColor=self.couleur_primaire, alignment=TA_LEFT,
                spaceAfter=2, leading=t["taille_titre"] + 4,
            ),
            "titre_banniere": ParagraphStyle(
                "TitreBanniere", parent=base["Title"],
                fontName=t["police_gras"], fontSize=t["taille_titre"],
                textColor=colors.white, alignment=TA_RIGHT,
                spaceAfter=2, leading=t["taille_titre"] + 4,
            ),
            "normal": ParagraphStyle(
                "NormalPerso", parent=base["Normal"],
                fontName=t["police"], fontSize=t["taille_corps"],
                textColor=self.couleur_texte, leading=t["taille_corps"] + 3,
            ),
            "normal_droite": ParagraphStyle(
                "NormalDroite", parent=base["Normal"],
                fontName=t["police"], fontSize=t["taille_corps"],
                textColor=self.couleur_texte, alignment=TA_RIGHT,
                leading=t["taille_corps"] + 3,
            ),
            "normal_blanc": ParagraphStyle(
                "NormalBlanc", parent=base["Normal"],
                fontName=t["police"], fontSize=t["taille_corps"],
                textColor=colors.white, leading=t["taille_corps"] + 3,
            ),
            "entreprise": ParagraphStyle(
                "Entreprise", parent=base["Normal"],
                fontName=t["police_gras"], fontSize=12,
                textColor=self.couleur_primaire, spaceAfter=2, leading=15,
            ),
            "entreprise_blanc": ParagraphStyle(
                "EntrepriseBlanc", parent=base["Normal"],
                fontName=t["police_gras"], fontSize=12,
                textColor=colors.white, spaceAfter=2, leading=15,
            ),
            "section": ParagraphStyle(
                "Section", parent=base["Normal"],
                fontName=t["police_gras"], fontSize=8,
                textColor=self.couleur_secondaire, spaceAfter=4, leading=10,
            ),
            "petit": ParagraphStyle(
                "Petit", parent=base["Normal"],
                fontName=t["police"], fontSize=7.5,
                textColor=colors.grey, leading=10,
            ),
        }

    def build(self, chemin_sortie: str) -> str:
        doc = SimpleDocTemplate(
            chemin_sortie,
            pagesize=self.taille_page,
            topMargin=self.marge,
            bottomMargin=self.marge,
            leftMargin=self.marge_gauche,
            rightMargin=self.marge,
            title=f"{self.type_doc} {self.numero}",
            author=self.config["vendeur"].get("nom", ""),
        )
        story = self._build_story()
        on_page = self._get_on_page()
        if on_page:
            doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
        else:
            doc.build(story)
        return self.numero

    def _build_story(self) -> list:
        story: list = []
        esp = self.theme["espacement_sections"] * mm
        story.extend(self._build_header())
        story.append(Spacer(1, esp))
        story.extend(self._build_client_block())
        story.append(Spacer(1, esp * 0.8))
        story.append(self._build_table())
        story.append(Spacer(1, esp * 0.6))
        story.append(self._build_totals())
        story.append(Spacer(1, esp))
        story.extend(self._build_footer())
        return story

    def _build_header(self) -> list:
        entete_type = self.theme.get("type_entete", "standard")
        if entete_type == "banniere":
            return self._header_banniere()
        if entete_type == "inverse":
            return self._header_inverse()
        return self._header_standard()

    def _header_standard(self) -> list:
        entete_gauche = self._build_vendeur_flowables()
        entete_droite = [
            Paragraph(self.type_doc, self.pstyles["titre"]),
            Paragraph(f"N° {self.numero}", self.pstyles["normal_droite"]),
            Paragraph(f"Date : {self.date_doc}", self.pstyles["normal_droite"]),
        ]
        table = Table(
            [[entete_gauche, entete_droite]],
            colWidths=[self.largeur_utile * 0.57, self.largeur_utile * 0.43],
        )
        table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return [table]

    def _header_inverse(self) -> list:
        entete_gauche = [
            Paragraph(self.type_doc, self.pstyles["titre_gauche"]),
            Paragraph(f"N° {self.numero}", self.pstyles["normal"]),
            Paragraph(f"Date : {self.date_doc}", self.pstyles["normal"]),
        ]
        entete_droite = self._build_vendeur_flowables()
        table = Table(
            [[entete_gauche, entete_droite]],
            colWidths=[self.largeur_utile * 0.45, self.largeur_utile * 0.55],
        )
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ]))
        return [table]

    def _header_banniere(self) -> list:
        vendeur = self.config["vendeur"]
        nom_vendeur = vendeur.get("nom", "")
        logo_path = vendeur.get("logo", "")
        contenu_gauche = []
        if logo_path and os.path.isfile(logo_path):
            try:
                contenu_gauche.append(
                    RLImage(logo_path, width=28 * mm, height=28 * mm, kind="proportional")
                )
            except Exception:
                pass
        contenu_gauche.append(Paragraph(nom_vendeur, self.pstyles["entreprise_blanc"]))
        contenu_droite = [
            Paragraph(self.type_doc, self.pstyles["titre_banniere"]),
            Paragraph(f"N° {self.numero}", self.pstyles["normal_blanc"]),
            Paragraph(f"Date : {self.date_doc}", self.pstyles["normal_blanc"]),
        ]
        table = Table(
            [[contenu_gauche, contenu_droite]],
            colWidths=[self.largeur_utile * 0.55, self.largeur_utile * 0.45],
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), self.couleur_primaire),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 12),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        return [table]

    def _build_vendeur_flowables(self) -> list:
        vendeur = self.config["vendeur"]
        elements: list = []
        logo_path = vendeur.get("logo", "")
        if logo_path and os.path.isfile(logo_path):
            try:
                elements.append(
                    RLImage(logo_path, width=30 * mm, height=30 * mm, kind="proportional")
                )
            except Exception:
                pass
        infos = f"<b>{vendeur.get('nom', '')}</b><br/>"
        if vendeur.get("adresse"):
            infos += f"{vendeur['adresse']}<br/>"
        if vendeur.get("telephone"):
            infos += f"Tél : {vendeur['telephone']}<br/>"
        if vendeur.get("email"):
            infos += f"{vendeur['email']}<br/>"
        if vendeur.get("nif"):
            infos += f"NIF : {vendeur['nif']} "
        if vendeur.get("stat"):
            infos += f"STAT : {vendeur['stat']}"
        elements.append(Paragraph(infos, self.pstyles["normal"]))
        return elements

    def _build_client_block(self) -> list:
        client = self.config["client"]
        label = "FACTURÉ À" if self.type_doc == "FACTURE" else "DEVIS POUR"
        infos = f"<b>{client.get('nom', '')}</b><br/>"
        if client.get("adresse"):
            infos += f"{client['adresse']}<br/>"
        if client.get("telephone"):
            infos += f"Tél : {client['telephone']}"
        return [
            Paragraph(label, self.pstyles["section"]),
            Paragraph(infos, self.pstyles["normal"]),
        ]

    def _build_table(self) -> Table:
        t = self.theme
        entetes = ["Désignation", "Qté", "Prix Unit.", "Total"]
        data: list = [entetes]
        for ligne in self.totaux["lignes"]:
            data.append([
                Paragraph(ligne["designation"], self.pstyles["normal"]),
                f"{ligne['quantite']:g}",
                formater_montant(ligne["prix_unitaire"], self.devise),
                formater_montant(ligne["total_ligne"], self.devise),
            ])
        w = self.largeur_utile
        col_widths = [w * 0.44, w * 0.13, w * 0.215, w * 0.215]
        table = Table(data, colWidths=col_widths)
        cmds: list = [
            ("FONTNAME", (0, 0), (-1, 0), t["police_gras"]),
            ("FONTSIZE", (0, 0), (-1, -1), t["taille_corps"]),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), t["padding_lignes"]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), t["padding_lignes"]),
            ("TEXTCOLOR", (0, 1), (-1, -1), self.couleur_texte),
        ]
        fond_entete = t.get("couleur_fond_entete")
        if fond_entete:
            cmds.append(("BACKGROUND", (0, 0), (-1, 0), hex_color(fond_entete, fond_entete)))
            couleur_txt_entete = t.get("couleur_texte_entete_tableau", "#FFFFFF")
            cmds.append(("TEXTCOLOR", (0, 0), (-1, 0), hex_color(couleur_txt_entete, "#FFFFFF")))
        else:
            cmds.append(("TEXTCOLOR", (0, 0), (-1, 0), self.couleur_secondaire))
            cmds.append(("LINEBELOW", (0, 0), (-1, 0), 1, self.couleur_primaire))
        if t.get("lignes_verticales"):
            cmds.append(("GRID", (0, 0), (-1, -1), t["epaisseur_ligne"], self.couleur_ligne))
        else:
            cmds.append(("LINEBELOW", (0, 1), (-1, -1), t["epaisseur_ligne"], self.couleur_ligne))
        fond_alt = self.config.get("couleur_fond_alternee") or t.get("couleur_fond_alternee")
        if fond_alt:
            cmds.append(("ROWBACKGROUNDS", (0, 1), (-1, -1),
                          [colors.white, hex_color(fond_alt, "#F5F5F5")]))
        table.setStyle(TableStyle(cmds))
        return table

    def _build_totals(self) -> Table:
        t = self.theme
        lignes = [["Sous-total", formater_montant(self.totaux["sous_total"], self.devise)]]
        if self.totaux["remise_totale"] > 0:
            lignes.append(["Remise", "- " + formater_montant(self.totaux["remise_totale"], self.devise)])
        if self.totaux["tva_pct"] > 0:
            lignes.append([f"TVA ({self.totaux['tva_pct']:g}%)",
                           formater_montant(self.totaux["montant_tva"], self.devise)])
        lignes.append(["TOTAL", formater_montant(self.totaux["total_final"], self.devise)])
        w = self.largeur_utile
        table = Table(lignes, colWidths=[w * 0.22, w * 0.22])
        cmds: list = [
            ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
            ("FONTSIZE", (0, 0), (-1, -2), t["taille_corps"] + 1),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("FONTNAME", (0, -1), (-1, -1), t["police_gras"]),
            ("FONTSIZE", (0, -1), (-1, -1), t["taille_total"]),
            ("LINEABOVE", (0, -1), (-1, -1), 1, self.couleur_primaire),
        ]
        fond_total = t.get("couleur_fond_total")
        bordure_totale = t.get("bordure_totale", False)
        if fond_total:
            cmds.append(("BACKGROUND", (0, -1), (-1, -1), hex_color(fond_total, fond_total)))
            cmds.append(("TEXTCOLOR", (0, -1), (-1, -1), self.couleur_primaire))
            cmds.append(("TOPPADDING", (0, -1), (-1, -1), 6))
            cmds.append(("BOTTOMPADDING", (0, -1), (-1, -1), 6))
        elif bordure_totale:
            cmds.append(("BOX", (0, -1), (-1, -1), 0.75, self.couleur_primaire))
            cmds.append(("TEXTCOLOR", (0, -1), (-1, -1), self.couleur_primaire))
        else:
            cmds.append(("TEXTCOLOR", (0, -1), (-1, -1), self.couleur_primaire))
        table.setStyle(TableStyle(cmds))
        wrapper = Table([[None, table]], colWidths=[w * 0.56, w * 0.44])
        wrapper.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return wrapper

    def _build_footer(self) -> list:
        elements: list = []
        if self.config.get("conditions_paiement"):
            elements.append(Paragraph("CONDITIONS DE PAIEMENT", self.pstyles["section"]))
            elements.append(Paragraph(self.config["conditions_paiement"], self.pstyles["normal"]))
            elements.append(Spacer(1, 4 * mm))
        if self.config.get("mentions_legales"):
            elements.append(Paragraph(self.config["mentions_legales"], self.pstyles["petit"]))
            elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph(
            f"Document généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}",
            self.pstyles["petit"],
        ))
        return elements

    def _get_on_page(self) -> Optional[Callable]:
        t = self.theme
        if t.get("bordure_externe"):
            return self._deco_bordure
        if t.get("type_entete") == "geometrique":
            return self._deco_geometrique
        if t.get("barre_laterale"):
            return self._deco_barre_laterale
        return None

    def _deco_bordure(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(self.couleur_ligne)
        canvas.setLineWidth(0.75)
        m = 10 * mm
        canvas.rect(m, m, doc.pagesize[0] - 2 * m, doc.pagesize[1] - 2 * m, fill=0, stroke=1)
        canvas.restoreState()

    def _deco_geometrique(self, canvas, doc):
        canvas.saveState()
        pw, ph = doc.pagesize
        couleur2 = hex_color(self.theme.get("couleur_secondaire_visuel", "#FFC107"), "#FFC107")
        canvas.setFillColor(self.couleur_primaire)
        path = canvas.beginPath()
        path.moveTo(pw - 80 * mm, ph)
        path.lineTo(pw, ph)
        path.lineTo(pw, ph - 80 * mm)
        path.close()
        canvas.drawPath(path, fill=1, stroke=0)
        canvas.setFillColor(couleur2)
        path2 = canvas.beginPath()
        path2.moveTo(pw - 35 * mm, ph)
        path2.lineTo(pw, ph)
        path2.lineTo(pw, ph - 35 * mm)
        path2.close()
        canvas.drawPath(path2, fill=1, stroke=0)
        canvas.setFillColor(self.couleur_primaire)
        canvas.rect(0, 0, pw, 3 * mm, fill=1, stroke=0)
        canvas.restoreState()

    def _deco_barre_laterale(self, canvas, doc):
        canvas.saveState()
        pw, ph = doc.pagesize
        largeur_barre = 6 * mm
        canvas.setFillColor(self.couleur_primaire)
        canvas.rect(0, 0, largeur_barre, ph, fill=1, stroke=0)
        couleur2 = hex_color(self.theme.get("couleur_secondaire_visuel", "#4ECDC4"), "#4ECDC4")
        canvas.setFillColor(couleur2)
        canvas.rect(0, 0, largeur_barre, 40 * mm, fill=1, stroke=0)
        canvas.restoreState()


# ═══════════════════════════════════════════════════════════════════════════
#  5. MODE INTERACTIF
# ═══════════════════════════════════════════════════════════════════════════

def demander(question: str, defaut: str = "") -> str:
    reponse = input(f"{question}" + (f" [{defaut}]" if defaut else "") + " : ").strip()
    return reponse if reponse else defaut


def demander_nombre(question: str, defaut: float = 0.0) -> float:
    while True:
        brut = demander(question, str(defaut))
        try:
            return float(brut.replace(",", "."))
        except ValueError:
            print("  → Merci d'entrer un nombre valide (ex : 1500 ou 1500.50).")


def choisir_style_interactif() -> str:
    print("\n┌─────────────────────────────────────────────────────────────┐")
    print("│  STYLES DE MISE EN PAGE DISPONIBLES                         │")
    print("├─────────────────────────────────────────────────────────────┤")
    cles = list(THEMES.keys())
    for i, cle in enumerate(cles, 1):
        t = THEMES[cle]
        print(f"│  {i:>2}. {cle:<20s} {t['nom']:<33s}│")
    print("└─────────────────────────────────────────────────────────────┘")
    while True:
        choix = demander("Numéro ou nom du style", "1")
        try:
            idx = int(choix) - 1
            if 0 <= idx < len(cles):
                return cles[idx]
        except ValueError:
            pass
        if choix in THEMES:
            return choix
        print("  → Choix invalide, entre un numéro (1-10) ou un nom de style.")


def mode_interactif() -> dict:
    print("=" * 55)
    print("  GÉNÉRATEUR DE FACTURE / DEVIS — Mode interactif")
    print("=" * 55)
    config = json.loads(json.dumps(DEFAULT_CONFIG))
    type_doc = demander("Type de document (FACTURE / DEVIS)", "FACTURE").upper()
    config["type_document"] = type_doc if type_doc in ("FACTURE", "DEVIS") else "FACTURE"
    config["style"] = choisir_style_interactif()
    print("\n--- Informations de votre entreprise (vendeur) ---")
    config["vendeur"]["nom"] = demander("Nom de l'entreprise")
    config["vendeur"]["adresse"] = demander("Adresse", "")
    config["vendeur"]["telephone"] = demander("Téléphone", "")
    config["vendeur"]["email"] = demander("Email", "")
    config["vendeur"]["logo"] = demander("Chemin du logo (vide = aucun)", "")
    print("\n--- Informations du client ---")
    config["client"]["nom"] = demander("Nom du client")
    config["client"]["adresse"] = demander("Adresse du client", "")
    config["client"]["telephone"] = demander("Téléphone du client", "")
    config["devise"] = demander("Devise (Ar, EUR, USD…)", "Ar")
    print("\n--- Mise en page ---")
    papier = demander("Taille de papier (A4 / LETTER / A5)", "A4").upper()
    config["taille_papier"] = papier if papier in PAPIER_DISPONIBLE else "A4"
    print("\n--- Articles / Services (désignation vide = fin) ---")
    articles = []
    while True:
        desig = demander(f"Article #{len(articles) + 1} – désignation (vide = fin)")
        if not desig:
            break
        qte = demander_nombre("  Quantité", 1)
        prix = demander_nombre("  Prix unitaire", 0)
        articles.append({"designation": desig, "quantite": qte, "prix_unitaire": prix})
    config["articles"] = articles
    config["tva_pourcentage"] = demander_nombre("TVA en % (0 si aucune)", 0)
    config["remise_pourcentage"] = demander_nombre("Remise en % (0 si aucune)", 0)
    config["conditions_paiement"] = demander(
        "Conditions de paiement", "Paiement à réception de facture."
    )
    return config


# ═══════════════════════════════════════════════════════════════════════════
#  6. CHARGEMENT CONFIG & CLI
# ═══════════════════════════════════════════════════════════════════════════

def charger_config_depuis_fichier(chemin: str) -> dict:
    if not os.path.isfile(chemin):
        raise FactureError(f"Fichier de config introuvable : {chemin}")
    try:
        with open(chemin, "r", encoding="utf-8") as f:
            user_config = json.load(f)
    except json.JSONDecodeError as e:
        raise FactureError(f"Le fichier JSON '{chemin}' est mal formé : {e}")
    except OSError as e:
        raise FactureError(f"Impossible de lire '{chemin}' : {e}")
    return deep_merge(DEFAULT_CONFIG, user_config)


def generer_modele_config(chemin: str, style: Optional[str] = None):
    exemple = json.loads(json.dumps(DEFAULT_CONFIG))
    exemple["style"] = style or STYLE_DEFAUT
    exemple["vendeur"]["nom"] = "Ma Boutique"
    exemple["vendeur"]["adresse"] = "Ilaka Centre, Madagascar"
    exemple["vendeur"]["telephone"] = "034 XX XXX XX"
    exemple["client"]["nom"] = "Nom du client"
    exemple["articles"] = [
        {"designation": "Produit ou service A", "quantite": 2, "prix_unitaire": 15000},
        {"designation": "Produit ou service B", "quantite": 1, "prix_unitaire": 30000},
    ]
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(exemple, f, ensure_ascii=False, indent=2)
    print(f"✅ Modèle de configuration créé : {chemin}")
    print(f"   Style : {exemple['style']}")
    print(f"   Remplis-le puis relance :")
    print(f"   python NFact.py --config {chemin}")


def lister_styles():
    print("\n  STYLES DE FACTURE DISPONIBLES")
    print("  " + "─" * 60)
    for cle, t in THEMES.items():
        print(f"  {cle:<22s}  {t['nom']}")
        print(f"  {'':<22s}  {t['description']}")
        print(f"  {'':<22s}  Accent : {t['couleur_primaire']}")
        print()
    print(f"  Utilisation : --style <nom>")
    print(f"  Exemple     : python NFact.py --config client.json --style wave\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Générateur de factures/devis PDF – 10 styles professionnels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemples :\n"
            "  python NFact.py --config client.json\n"
            "  python NFact.py --config client.json --style wave\n"
            "  python NFact.py --list-styles\n"
            "  python NFact.py --new-config client.json --style stripe\n"
        ),
    )
    parser.add_argument("--config", help="Chemin vers un fichier JSON de configuration")
    parser.add_argument("--new-config", help="Génère un fichier modèle JSON vide")
    parser.add_argument("--style", help="Nom du style visuel (voir --list-styles)")
    parser.add_argument("--output-dir", help="Dossier de sortie pour le PDF", default=None)
    parser.add_argument("--list-styles", action="store_true", help="Liste les styles disponibles")
    args = parser.parse_args()

    try:
        if args.list_styles:
            lister_styles()
            return 0

        if args.new_config:
            generer_modele_config(args.new_config, style=args.style)
            return 0

        if args.config:
            config = charger_config_depuis_fichier(args.config)
        else:
            config = mode_interactif()

        if args.style:
            config["style"] = args.style

        if args.output_dir:
            config["dossier_sortie"] = args.output_dir

        erreurs = valider_config(config)
        erreurs_bloquantes = [e for e in erreurs if not e.startswith("AVERTISSEMENT")]
        avertissements = [e for e in erreurs if e.startswith("AVERTISSEMENT")]
        for a in avertissements:
            print(f"  ⚠️  {a}")
        if erreurs_bloquantes:
            print("\n  ❌ Impossible de générer la facture, corrige ces erreurs :")
            for e in erreurs_bloquantes:
                print(f"     • {e}")
            return 1

        style_name = config.get("style", STYLE_DEFAUT)
        if style_name not in THEMES:
            style_name = STYLE_DEFAUT

        dossier_sortie = config.get("dossier_sortie", "factures_generees")
        try:
            os.makedirs(dossier_sortie, exist_ok=True)
        except OSError as e:
            raise FactureError(f"Impossible de créer le dossier '{dossier_sortie}' : {e}")

        client_slug = "".join(
            c if c.isalnum() else "_" for c in config["client"]["nom"]
        ).strip("_") or "client"
        date_slug = datetime.now().strftime("%Y-%m-%d")
        nom_fichier = f"{config.get('type_document', 'FACTURE').lower()}_{date_slug}_{client_slug}.pdf"
        chemin_sortie = os.path.join(dossier_sortie, nom_fichier)

        builder = FacturePDFBuilder(config)
        numero = builder.build(chemin_sortie)

        print(f"\n  ✅ {config.get('type_document', 'FACTURE')} générée avec succès !")
        print(f"     Numéro  : {numero}")
        print(f"     Style   : {style_name} ({THEMES[style_name]['nom']})")
        print(f"     Fichier : {os.path.abspath(chemin_sortie)}\n")
        return 0

    except FactureError as e:
        print(f"\n  ❌ Erreur : {e}\n")
        return 1
    except KeyboardInterrupt:
        print("\n  Annulé par l'utilisateur.")
        return 1
    except Exception as e:
        print(f"\n  ❌ Erreur inattendue : {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
