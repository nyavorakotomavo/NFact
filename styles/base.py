"""
Interface de style pour NFact.

Un style = uniquement des VALEURS de présentation (couleurs, polices, layout).
Aucune logique de rendu ici. La logique de rendu (comment dessiner le PDF)
vit dans NFact.py et ne change jamais quand on ajoute un style.

Pour ajouter un nouveau style : créer un fichier styles/mon_style.py
qui appelle register(Style(...)), puis l'importer dans styles/__init__.py.
Rien d'autre à toucher.
"""
from dataclasses import dataclass, field
from typing import List, Optional
import copy


@dataclass
class Style:
    nom: str
    # Couleurs par défaut du style (écrasées si l'utilisateur en fournit)
    couleurs_accent: List[str] = field(default_factory=lambda: ["#1a3c6e"])
    couleur_texte: str = "#000000"
    couleur_fond_alternee: str = "#f5f5f5"

    # Typographie
    police_titre: str = "Helvetica-Bold"
    police_normale: str = "Helvetica"
    taille_titre: int = 22

    # Layout — doit correspondre à une variante gérée dans NFact.py
    # Variantes disponibles : "classique", "bande_couleur"
    en_tete_style: str = "classique"

    # Dégradé multi-couleurs sur l'en-tête du tableau d'articles
    tableau_entete_degrade: bool = True
    # Dégradé sur la ligne TOTAL
    ligne_total_degrade: bool = False


REGISTRY = {}


def register(style: Style) -> Style:
    REGISTRY[style.nom] = style
    return style


def get_style(nom: str, couleurs_override: Optional[List[str]] = None) -> Style:
    """Récupère un style par nom. Si couleurs_override est fourni
    (ex: plusieurs couleurs pour un dégradé), il remplace les couleurs
    par défaut du style sans toucher au reste (polices, layout)."""
    base = REGISTRY.get(nom, REGISTRY.get("classique"))
    if base is None:
        raise ValueError("Aucun style 'classique' enregistré — vérifie styles/__init__.py")
    if couleurs_override:
        s = copy.deepcopy(base)
        s.couleurs_accent = couleurs_override
        return s
    return copy.deepcopy(base)


def liste_styles() -> List[str]:
    return sorted(REGISTRY.keys())
