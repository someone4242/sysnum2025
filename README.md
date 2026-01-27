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

Les registres vont de `x0` à `x31` avec la particularité que `x0` est hard wired
à 0 (comme en RISC-V). Dans la suite, `rd`, `rs1` et `rs2` désigneront des 
registres, et `imm` un immediate (qui doit donc être connu à la compilation),
qui doit être représentable en 12 bits (signés). (Note: pour des plus grands 
immediate, on peut utiliser un bitshift et une addition avec un autre 
immediate)

Voici la liste des instructions qui peuvent remplir les autres lignes :

- `add rd rs1 rs2` : Place le résultat de `rs1 + rs2` dans `rd`
- `addi rd rs1 imm` : Place le résultat de `rs1 + imm` dans `rd`
- `xor`, `or` et `and`, ainsi que leurs versions immediate `xori`, `ori` et 
`andi` suivent la même syntaxe.
- `sub` et `mul` également, mais n'ont pas de version immediate.
- `sw rs2 offset(rs1)` : Stocke le contenu de `rs2` à l'adresse `rs1 + offset` 
où `offset` est un entier qui est le nombre de mot de décalage par rapport à 
l'adresse `rs1`
- `lw rd offset(rs1)`: Fait l'opération inverse, charge le contenu de la mémoire
dans `rd`
- `sll rd rs1 rs2` : Effectue un left logical bit_shift sur `rs1` de `rs2` bits
(sur les bits de poids faibles).
- `slli rd rs1 imm` : De même avec un immediate.
- `srl` et `srli` : De même pour le right logical shift
- `jal rd label` : Effectue un saut inconditionnel à l'étiquette `label` et 
place l'adresse de retour dans `rd`
- `beq rs1 rs2 label` : Effectue un saut à l'étiquette `label` si `rs1` et
`rs2` sont égaux.
- `bne`, `blt`, `bge` : Même syntaxe, mais sautent respectivement si
`rs1 =\= rs2`, `rs1 < rs2` et `rs1 >= rs2`
- `rditme rd` : Place le nombre de secondes depuis 01/01/2026 dans `rd`
- `rdclock rd` : Indique dans `rd` si l'horloge est en front montant ou 
descendant
- `fadd`, `fsub`, `fmul` et `fdiv` : Ont la même syntaxe que `add` et 
correspondent aux opérations usuelles sur les flottants
- `fes rd rs1 rs2` : Place 1 dans `rd` si les flottants `rs1` et `rs2` sont 
égaux, et 0 sinon.
- `ffisqrt rd rs1` : Cette opération capitale et à usage très courant place
la racine carré inverse de rs1 dans rd.
- `fcvt.w rd rs1` : Convertit le flottant `rs1` en entier dans `rd`
- `fcvt.s` : De même mais pour la conversion entier vers flottant

## Note sur l'utilisation de l'IA

Malgré notre avance déraisonnable sur la deadline, nous avons demandé à 
Gemini de nous faire l'affichage stylé de l'horloge, car nous ne sommes pas des 
élèves du département des arts . 
L'entièreté du code restant a été écrit à la main.