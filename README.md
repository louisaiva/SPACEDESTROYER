# SPACEDESTROYER

petit jeu dans l'espace en python avec OpenGL
aivazian louis & charpenay arthur 4eti - CPE Lyon

## but du jeu

il faut trouver le portail hypervitesse le plus vite possible
attention aux meteorites !!

le portail est arc-en-ciel et sa distance est affichée en bas de l'écran.
certaines meteorites vertes vous soignent lorsque vous rentrez en collision avec elles.

attention aux planètes, elles vous tueront instantanément si vous essayer d'y atterrir !

vous pouvez sélectionner votre vaisseau dans le menu principal.

## commandes

toutes les commandes possèdent leur équivalent joystick (pour manette xbox, ps4, ...). L'équivalent joystick sera affiché entre parenthèses.

### menu principal

- `fleche gauche / droite` (`left joystick - left / right`) : changer de vaisseau
- `q / d` (`left joystick - left / right`) : changer de vaisseau
- `espace / entrée` (`A`) : lancer le jeu
- `echap` (`B`) : quitter le programme

### en jeu

- `z / fleche haut` (`left joystick - up`) : monter
- `s / fleche bas` (`left joystick - down`) : descendre
- `q / fleche gauche` (`left joystick - left`) : aller à gauche
- `d / fleche droite` (`left joystick - right`) : aller à droite

- `c` (`Y`) : regarder derrière le vaisseau
- `espace` (`gachette R1 / L1`) : tirer un missile

- `echap` (`B`) : retour au menu principal


## fichiers du projet

### `/`

tous les fichiers de code source sont dans le dossier racine du projet (qu'on appelera ici `/`)

- `/main.py` : fichier principal du projet, à lancer pour jouer
- `/world.py` : fichier contenant la classe World (et d'autres), qui gère le monde du jeu
- `/README.md` : ce fichier

- `/aivazian_charpenay_rendu.pdf` : rapport explicitant les différentes parties du projet, leurs fonctionnalités et leurs difficultés

- `/shaders/` : dossier contenant les 4 shaders utilisés pour le jeu


### `/ressources/`

ce dossier contient toutes les ressources utilisées par le jeu (textures, modèles 3D, sons, ...)

- `/ressources/*.obj` : tous les modèles 3D utilisés dans le jeu
- `/ressources/*.jpg` : textures principales utilisées dans le jeu (notamment les polices d'écriture)
- `/ressources/planets/*.jpg` : textures des planètes

- `/ressources/spaceships.json` : fichier json contenant les caractéristiques de chaque vaisseau

## tests et débogage

Vous pouvez changer quelques paramètres rapides du jeu en haut de différents fichiers afin d'améliorer vos tests et expériences de jeu.

variables modifiables :

- `FULLSCREEN` dans `/main.py` : si `False`, la fenêtre du jeu sera 800x800 px
- `INVINCIBLE` dans `/viewerGL.py` : si `True`, le vaisseau ne pourra pas mourir, utile pour tester tout et n'importe quoi
- `NB_PLANET` dans `/world.py` : int qui définit le nombre de planètes dans le monde.
- `NB_METEOR` dans `/world.py` : int qui définit le nombre de météorites utilisées et regénérées dans le monde.
- `HEAL_RATIO` dans `/world.py` : float entre 0 et 1 qui définit le pourcentage de météorites qui soignent le vaisseau.
- `REMOVE_METEORITE_DISTANCE` dans `/world.py` : int qui définit la distance à laquelle une météorite est regénérée car trop loin du vaisseau. Cette variable impacte aussi la distance de suppression des rayons lasers lancés par le vaisseau.


## informations complémentaires

### dépendances

le projet utilise la library `json` pour lire le fichier .json

### collisions

les collisions ne sont pas parfaites, surtout celles des planètes. S'en approcher même de loin peut être fatal.
Il y a une chance minime qu'une planète soit générée sur le vaisseau, ce qui le tuerait instantanément.
De plus, il est possible que le portail soit généré dans une planète, ce qui rendrait le jeu impossible à gagner.
Ces quelques problèmes ne sont pas très gênants pour un petit projet comme ça mais ça serait évidemment à corriger pour un jeu plus sérieux.

### pour aller plus loin

on voulait ajouter des ennemis qui suivent le vaisseau et l'attaquent, mais on a pas eu le temps de le faire.