Nombres flottants 16 bits:
1 bit de signe
5 bits d'exposant
10 bits de mantisse (le premier 1, implicite, donc 11 bits)

Nombres flottants 32 bits:
1 bit de signe
8 bits d'exposant
23 bits de mantisse (le premier 1, implicite, donc 24 bits)

NaN: tous les bits à 1


Listes des fonctions: Les fonctions flottantes ont leur nom commençant par f

- *bitshift.py*:
    - **ajouter_zeros_droite**: réalise un bitshift vers la gauche
    - **ajouter_zeros_gauche**: réalise un bitshift vers la droite

- *comparer.py*:
    - **fegal_zero**: renvoie Constant("1) ssi le nombre est un flottant nul (donc sans traiter le bit de signe)
    - **fegal**: renvoie Constant("1") ssi les deux flottants sont strictement égaux
    - **egal**: renvoie Constant("1") ssi les deux int sont égaux
    - **plus_grand_large**: renvoie Constant("1") ssi le premier int est plus grand ou égal au second
    - **plus_grand_strict**: renvoie Constant("1") ssi le premier int est strictement plus grand que le second

- *convert.py*:
    - **fround_down**: arrondi à l'entier inférieur
    - **fround_up**: arrondi à l'entier supérieur
    - **fround_nearest_to_even**: arrondi à l'entier le plus proche, avec arrondi au nombre pair le plus proche si sa partie fractionnaire vaut 0.5 (pour éviter les biais)

- *encodedecode.py*: fichier principal à modifier pour passer de 16 à 32 bits
    - **fdecode**: renvoie (signe,exposant,mantisse avec biais implicite)
    - **fencode**: renvoie le flottant à partir de signe, exposant, mantisse avec biais implicite
    - **biais**: renvoie le biais (hardcodé)
    - **nan**: renvoie un nan (hardcodé) 

- *fadder_et_fmultiplie.py*:
    - **fadd**: réalise l'addition des deux flottants donnés (on aligne les deux exposants, puis on somme)
    - **fmultiplie**: réalise la multiplication des deux flottants donnés (on additionne les exposants et multiplie les deux mantisses)
    - **fdivise**: réalise la division des deux flottants donnés (on soustrait les exposants et divise les deux mantisses). En cas de division par zéro, ou si un des terme est NaN, on renvoie NaN

- *fast_inverse_square_root.py*: uniquement flottants 32 bits
    - **fast_inverse_square_root**: renvoie l'inverse de la racine carrée du flottant donné

- *multiplie.py*:
    - **multiplie**: réalise la multiplication des deux entiers donnés par diviser pour régner (les entiers doivent être de taille une puissance de deux)


Que modifier pour avoir les flottants en 32 bits au lieu de 16?

| *encodedecode.py* | 16 bits                    | 32 bits                    |
|----------------------------|----------------------------|----------------------------|
| *fdecode* | `assert a.bus_size == 16`    | `assert a.bus_size == 32`    |
| *fdecode* | `signe = a[15]`              | `signe = a[31]`              |
| *fdecode* | `exposant = a[10:15]`        | `exposant = a[23:31]`        |
| *fdecode* | `mantisse = a[0:10]`         | `mantisse = a[0:23]`         |
| *fdecode* | `exposant_different_zero = exposant[0] \| exposant[1] \| exposant[2] \| exposant[3] \| exposant[4]` | `exposant_different_zero = exposant[0] \| exposant[1] \| exposant[2] \| exposant[3] \| exposant[4] \| exposant[5] \| exposant[6] \| exposant[7]` |
| *fencode* | `return m[0:10] + e[0:5] + s` | `return m[0:23] + e[0:8] + s` |
| *biais* | `return Constant("1111")` | `return Constant("1111111")` |
| *nan* | `return Constant("1"*16)` | `return Constant("1"*32)` |

| *fadder_et_fmultiplie.py* | 16 bits                    | 32 bits                    |
|----------------------------|----------------------------|----------------------------|
| *retire_zeros_gauche* | `exposant = adder(exposant,Constant("0"*exposant.bus_size),mantisse[21])[0]`    | `exposant = adder(exposant,Constant("0"*exposant.bus_size),mantisse[47])[0]`    |
| *retire_zeros_gauche* | `doit_sarreter = comparer.fegal_zero(mantisse[11:])` | `doit_sarreter = comparer.fegal_zero(mantisse[23:])` |
| *retire_zeros_gauche* | `doit_sarreter = doit_sarreter \| comparer.fegal_zero(mantisse[11:])` | `doit_sarreter = doit_sarreter \| comparer.fegal_zero(mantisse[23:])` |

| *convert.py* | 16 bits                    | 32 bits                    |
|----------------------------|----------------------------|----------------------------|
| *fround_down* | `assert a.bus_size == 16` | `assert a.bus_size == 32` |
| *fround_down* | `mantisse = mantisse + Constant("0"*(32-mantisse.bus_size+10))` | `mantisse = mantisse + Constant("0"*(32-mantisse.bus_size+23))` |
| *fround_down* | `entier = entier[10:]` | `entier = entier[23:]` |
| *round_nearest_to_even* | `assert a.bus_size == 16` | `assert a.bus_size == 32` |
| *round_nearest_to_even* | `mantisse = mantisse + Constant("0"*(32-mantisse.bus_size+10))` | `mantisse = mantisse + Constant("0"*(32-mantisse.bus_size+23))` |
| *round_nearest_to_even* | `condition_aller_superieur = entier[9] & ((entier[10] & comparer.fegal_zero(entier[:10])) \| ~comparer.fegal_zero(entier[:10]))` | `condition_aller_superieur = entier[22] & ((entier[23] & comparer.fegal_zero(entier[:23])) \| ~comparer.fegal_zero(entier[:23]))` |
| *round_nearest_to_even* | `entier = entier[10:]` | `entier = entier[23:]` |
