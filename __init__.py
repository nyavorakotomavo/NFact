"""
Point d'entrée du package styles.

Pour ajouter un nouveau style :
1. Créer styles/mon_style.py (copier un fichier existant comme modèle)
2. Ajouter une ligne d'import ci-dessous
C'est tout — NFact.py n'a jamais besoin d'être modifié.
"""
from .base import Style, get_style, liste_styles, REGISTRY  # noqa: F401

# Chaque import déclenche l'enregistrement du style via register()
from . import classique      # noqa: F401,E402
from . import stripe         # noqa: F401,E402
from . import quickbooks     # noqa: F401,E402
from . import freshbooks_modern  # noqa: F401,E402
from . import violet         # noqa: F401,E402
