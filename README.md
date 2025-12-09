
https://github.com/hbens/sysnum-2025

https://docs.riscv.org/reference/isa/_attachments/riscv-unprivileged.pdf (add: page 26)

# Rapport de conception du microprocesseur

Fragment de RISC-V avec architecture de type Harvard.

Instructions de base : add, xor, and, or, addi, load, store, jmp, jz.

ALU comme en TD, avec flags NZCV.

Registres : RV32I (registres x1 à x31, avec x0 le registre NULL).

Propositions d'instructions supplémentaires :
- min, max
- bit shift
- multiplicateur: mul

