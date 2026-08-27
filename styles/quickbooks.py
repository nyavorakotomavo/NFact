from .base import Style, register

register(Style(
    nom="quickbooks",
    couleurs_accent=["#2CA01C"],
    couleur_fond_alternee="#f2f8f1",
    police_titre="Helvetica-Bold",
    en_tete_style="bande_couleur",
    tableau_entete_degrade=True,
))
