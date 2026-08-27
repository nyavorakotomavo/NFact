#!/usr/bin/env python3
"""
Régénère automatiquement la liste déroulante des styles dans
.github/workflows/facture-ia.yml en lisant les styles réellement
enregistrés dans le package styles/.

Ne jamais éditer la liste des styles à la main dans le workflow :
ce script est la seule source de vérité, déclenché automatiquement
par sync-styles-choices.yml à chaque ajout/modif de fichier styles/*.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from styles import liste_styles  # noqa: E402

WORKFLOW_PATH = ROOT / ".github" / "workflows" / "facture-ia.yml"


def build_style_block(styles):
    default = "classique" if "classique" in styles else styles[0]
    lignes = [
        "      style:",
        '        description: "Style visuel du PDF"',
        "        required: true",
        "        type: choice",
        "        options:",
    ]
    for s in styles:
        lignes.append(f"          - {s}")
    lignes.append(f"        default: {default}")
    return "\n".join(lignes) + "\n"


def main():
    styles = liste_styles()
    if not styles:
        print("❌ Aucun style trouvé dans styles/ — abandon, workflow non modifié.")
        sys.exit(1)

    if not WORKFLOW_PATH.is_file():
        print(f"❌ Fichier introuvable : {WORKFLOW_PATH}")
        sys.exit(1)

    content = WORKFLOW_PATH.read_text(encoding="utf-8")

    # Capture le bloc "      style:" + toutes ses lignes filles (indentées à 8+ espaces)
    pattern = re.compile(r"^ {6}style:\n(?: {8}.*\n)+", re.MULTILINE)
    if not pattern.search(content):
        print("❌ Bloc 'style:' introuvable dans le workflow — format inattendu, abandon.")
        sys.exit(1)

    nouveau_bloc = build_style_block(styles)
    nouveau_contenu = pattern.sub(nouveau_bloc, content, count=1)

    if nouveau_contenu == content:
        print(f"✅ Déjà à jour. Styles : {', '.join(styles)}")
    else:
        WORKFLOW_PATH.write_text(nouveau_contenu, encoding="utf-8")
        print(f"✅ Workflow mis à jour — {len(styles)} styles : {', '.join(styles)}")


if __name__ == "__main__":
    main()