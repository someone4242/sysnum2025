# Rapport de conception microprocesseur

## Organisation du dossier

Le dossier contient différents éléments qui sont listés ici :

- Un `makefile` dont les fonctionnalités sont détaillées ci-dessous
- Les fichiers `compilation.py` et `op_code.py` qui servent au compilateur
du langage assembleur (détaillé plus loin)
- Un dossier `clocks` qui contient les codes sources des horloges
- Un dossier `test` avec quelques programmes assembleurs utilisés pour les 
phases de test
- Un dossier `simulation` qui contient les fichiers sources du simulateur de
netlist
- Un dossier `file_proc` avec les fichiers sources du compilateur
- Un fichier `script_compil_simu.sh` dont il ne faut pas trop se soucier si vous
tenez à votre vie ainsi qu'à celle de votre famille

## Makefile

Voici les fonctionnalités du makefile :

- `make simu` : construit `netlist_simulator.byte` dans le répoertoir source
- `make proc` : construit la netlist du processeur `processeur.net`
- `make all` : réalise les 2 opérations précédentes
- `make clean` : nettoie les fichiers crées par les 2 opérations précédentes
- `make clock` : construit le simulateur et le processeur et éxécute l'horloge
- `make clockff` : construit le simulateur et le processeur et éxécute l'horloge
en mode fast forward

## Utiliser les compilateur et le simulateur

Pour utiliser le compilateur assembleur et éxectuer un petit programme, il
faut faire ainsi :

- écrire un petit programme dans `nom_de_fichier_source`
- éxécuter `python3 compilateur.py -o nom_de_fichier_destination nom_de_fichier_source`
- éxécuter `./netlist_simulator.byte -rom nom_de_fichier_destination processeur.net`

## Syntaxe du langage assembleur

Notre langage assembleur utilise des fichiers **avec l'extensions *.sus*** 
(sans celle-ci le programme pourrait **NE PAS FONCTIONNER !!!!!** (croyez moi !
(j'ai vu des choses terribles)))

Chaque ligne doit contenir une instruction, une étiquette, ou une ligne vide.

Une ligne avec étiquette est de la forme `label:`.

Voici la liste des instructions qui peuvent remplir les autres lignes :