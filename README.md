
https://github.com/hbens/sysnum-2025

https://docs.riscv.org/reference/isa/_attachments/riscv-unprivileged.pdf (add: page 28)

# Rapport de conception du microprocesseur

Fragment de RISC-V avec architecture de type Harvard.

Instructions de base : add, xor, and, or, addi, load, store, jmp, jz.

ALU comme en TD, avec flags NZCV.

Registres : RV32I (registres x1 à x31, avec x0 le registre NULL).

Propositions d'instructions supplémentaires :
- min, max
- bit shift
- multiplicateur: mul (riscv: page 69)

multiplication inverse rapide avec flottant 16 bits . (page 119 pour 32bits)
NE SURTOUT PAS RESPECTER LA NORME STANDARD!!!!!


Ceci est un test pour mon fichier de configuration:
| encodedecode.py | 16 bits                    | 32 bits                    |
|-----------------|----------------------------|----------------------------|
| bus_size        | assert a.bus_size == 16    | assert a.bus_size == 32    |
| signe           | signe = a[15]              | signe = a[31]              |
| exposant        | exposant = a[10:15]        | exposant = a[23:31]        |
| mantisse        | mantisse = a[0:10]         | mantisse = a[0:23]         |
