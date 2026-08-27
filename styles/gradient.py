"""
Génération de dégradés pour reportlab.
Fonctionne avec 1 couleur (couleur unie) ou plusieurs (dégradé linéaire).
"""
from reportlab.lib import colors as rl_colors
from reportlab.platypus import Flowable


def _to_rl(hex_list):
    return [rl_colors.HexColor(h) for h in hex_list]


def interpolate_colors(hex_list, steps):
    """Retourne une liste de `steps` couleurs reportlab interpolées
    linéairement entre les couleurs fournies (1 ou plusieurs)."""
    cols = _to_rl(hex_list)
    if len(cols) == 1 or steps <= 1:
        return [cols[0]] * max(steps, 1)

    result = []
    segments = len(cols) - 1
    per_segment = max(1, steps // segments)
    for i in range(segments):
        c0, c1 = cols[i], cols[i + 1]
        for s in range(per_segment):
            t = s / per_segment
            result.append(rl_colors.Color(
                c0.red + (c1.red - c0.red) * t,
                c0.green + (c1.green - c0.green) * t,
                c0.blue + (c1.blue - c0.blue) * t,
            ))
    result.append(cols[-1])
    # Ajuste à la taille exacte demandée
    if len(result) > steps:
        result = result[:steps]
    while len(result) < steps:
        result.append(cols[-1])
    return result


class GradientBar(Flowable):
    """Barre horizontale pleine largeur, unie ou en dégradé selon le nombre
    de couleurs fournies. Utilisée pour les styles 'bande_couleur'."""

    def __init__(self, width, height, hex_colors, steps=80):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.couleurs = interpolate_colors(hex_colors, steps)

    def wrap(self, *args):
        return (self.width, self.height)

    def draw(self):
        c = self.canv
        n = len(self.couleurs)
        step_w = self.width / n
        for i, col in enumerate(self.couleurs):
            c.setFillColor(col)
            # +0.75 pour éviter les micro-liserés blancs entre bandes
            c.rect(i * step_w, 0, step_w + 0.75, self.height, fill=1, stroke=0)


def couleurs_par_colonne(hex_colors, nb_colonnes):
    """Pour appliquer un effet dégradé sur l'en-tête d'un Table reportlab
    (une couleur unie par colonne, interpolée à travers la ligne)."""
    return interpolate_colors(hex_colors, nb_colonnes)
