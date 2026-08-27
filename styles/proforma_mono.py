from .base import Style, register

register(Style(
    nom="proforma_mono",
    couleurs_accent=["#000000"],
    couleur_texte="#000000",
    couleur_fond_alternee="#ffffff",
    police_titre="Courier-Bold",
    police_normale="Courier",
    taille_titre=26,
    en_tete_style="classique",
    tableau_entete_degrade=False,
    ligne_total_degrade=False,
))
