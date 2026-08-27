from .base import Style, register

# Exemple : ce fichier a pris 1 minute à écrire, aucune autre modification
# nécessaire ailleurs dans le projet pour qu'il fonctionne.
register(Style(
    nom="violet",
    couleurs_accent=["#7C3AED", "#9333EA", "#A78BFA"],  # dégradé 3 tons
    couleur_fond_alternee="#f5f0fe",
    police_titre="Helvetica-Bold",
    en_tete_style="bande_couleur",
    tableau_entete_degrade=True,
    ligne_total_degrade=True,
))
