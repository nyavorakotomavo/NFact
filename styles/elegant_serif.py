from .base import Style, register

register(Style(
    nom="elegant_serif",
    couleurs_accent=["#1a1a1a"],
    couleur_texte="#1a1a1a",
    couleur_fond_alternee="#f7f6f2",
    police_titre="Times-Italic",
    police_normale="Times-Roman",
    taille_titre=30,
    en_tete_style="classique",
    tableau_entete_degrade=False,
    ligne_total_degrade=False,
))
