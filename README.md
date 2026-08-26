# NFact

[![GitHub license](https://img.shields.io/github/license/nyavorakotomavo/NFact)](https://github.com/nyavorakotomavo/NFact/blob/main/LICENSE)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/)
[![GitHub stars](https://img.shields.io/github/stars/nyavorakotomavo/NFact?style=social)](https://github.com/nyavorakotomavo/NFact/stargazers)

**NFact** est un outil Python polyvalent conçu pour la génération et la gestion de faits. Que vous ayez besoin de générer des faits aléatoires, de les organiser ou de les analyser, NFact offre une solution simple et efficace.

## 📌 À propos du projet

NFact est né du besoin d'un outil flexible pour travailler avec des faits structurés. Ce projet vise à fournir :

- Génération de faits aléatoires
- Gestion et organisation de collections de faits
- Analyse et traitement de données factuelles
- Intégration facile avec d'autres systèmes

## ✨ Fonctionnalités

- **Génération de faits** : Créez des faits aléatoires ou basés sur des modèles
- **Stockage structuré** : Organisez vos faits dans des catégories et sous-catégories
- **Recherche puissante** : Trouvez rapidement les faits dont vous avez besoin
- **Export/Import** : Échangez des collections de faits avec d'autres utilisateurs
- **API simple** : Intégration facile dans vos propres applications
- **Personnalisation** : Adaptez NFact à vos besoins spécifiques

## 🛠 Installation

### Prérequis

- Python 3.7 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation

```bash
# Cloner le dépôt
git clone https://github.com/nyavorakotomavo/NFact.git

# Accéder au répertoire du projet
cd NFact

# Installer les dépendances
pip install -r requirements.txt
```

## 🚀 Utilisation rapide

### Exemple de base

```python
from NFact import FactGenerator

# Créer un générateur de faits
generator = FactGenerator()

# Générer un fait aléatoire
random_fact = generator.generate()
print(random_fact)

# Générer un fait d'une catégorie spécifique
category_fact = generator.generate(category="science")
print(category_fact)
```

### Avec le script CLI

```bash
# Générer un fait aléatoire
python NFact.py --random

# Lister toutes les catégories disponibles
python NFact.py --list-categories

# Exporter les faits vers un fichier
python NFact.py --export facts.json

# Importer des faits depuis un fichier
python NFact.py --import new_facts.json
```

## 📂 Structure du projet

```
NFact/
├── NFact.py           # Module principal
├── fact              # Fichier de données de faits
├── config/           # Fichiers de configuration
├── logos/            # Logos et assets visuels
├── scripts/          # Scripts utilitaires
├── .github/          # Configuration GitHub
├── .gitignore        # Fichiers ignorés par Git
└── README.md         # Documentation du projet
```

## 📖 Documentation

Une documentation complète est disponible dans le [wiki du projet](https://github.com/nyavorakotomavo/NFact/wiki).

### Configuration

Créez un fichier `config.json` dans le dossier `config/` pour personnaliser NFact :

```json
{
  "default_category": "general",
  "fact_length": "medium",
  "language": "fr",
  "enable_cache": true
}
```

### Personnalisation

Vous pouvez étendre NFact en :

1. Ajoutant de nouveaux générateurs de faits dans le dossier `scripts/`
2. Créant des fichiers de faits personnalisés
3. Modifiant les paramètres de configuration

## 🤝 Contribution

Les contributions sont les bienvenues ! Voici comment contribuer :

1. **Forker le projet**
2. **Créer votre branche de fonctionnalité** (`git checkout -b feature/AmazingFeature`)
3. **Valider vos modifications** (`git commit -m 'Add some AmazingFeature'`)
4. **Pousser vers la branche** (`git push origin feature/AmazingFeature`)
5. **Ouvrir une Pull Request**

### Bonnes pratiques

- Respectez le style de code existant
- Ajoutez des tests pour les nouvelles fonctionnalités
- Mettez à jour la documentation
- Gardez vos commits atomiques

## 📜 Licence

Ce projet est sous licence **MIT** - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🙏 Remerciements

- À tous ceux qui contribuent à l'open source
- Aux utilisateurs qui testent et rapportent des bugs
- À la communauté Python pour ses excellents outils

## 📞 Contact

Pour toute question ou suggestion, n'hésitez pas à :

- Ouvrir une [issue](https://github.com/nyavorakotomavo/NFact/issues)
- Envoyer un email à : nyavorakotomavo@gmail.com
- Me contacter sur [LinkedIn](https://www.linkedin.com/in/nyavo-rakotomavo/)

---

⭐ **Étoilez ce dépôt** si vous le trouvez utile !

*Made with ❤️ by [Nyavo Rakotomavo](https://github.com/nyavorakotomavo)*
