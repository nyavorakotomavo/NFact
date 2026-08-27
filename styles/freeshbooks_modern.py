from .base import Style, register

register(Style(
    nom="freshbooks_modern",
    couleurs_accent=["#00A8E1"],
    couleur_fond_alternee="#f0f9fc",
    police_titre="Helvetica-Bold",
    en_tete_style="bande_couleur",
    tableau_entete_degrade=True,
    ligne_total_degrade=True,
))