from lib_carotte import *
import functools
import encodedecode
import bitshift
import fulladder
import comparer
import multiplie

def adder(a: Variable, b: Variable, c_in: Variable, i: int | None = None) -> typing.Tuple[Variable, Variable]:
    '''n-bit full-adder implementation'''
    assert a.bus_size == b.bus_size
    if i is None:
        i = a.bus_size-1
    assert 0 <= i < a.bus_size
    if i == 0:
        return fulladder.full_adder(a[i], b[i], c_in)
    (res_rest, c_rest) = adder(a, b, c_in, i-1)
    (res_i, c_out) = fulladder.full_adder(a[i], b[i], c_rest)
    return (res_rest + res_i, c_out)

def inverse_bits(a: Variable) -> Variable:
    r = ~a[0]
    for i in range(1, a.bus_size):
        r = r + (~a[i])
    return r

def decale_exposant_addition_signe_different(mantisse: Variable, exposant: Variable) -> typing.Tuple[Variable, Variable]:
    compteur = Constant("0"*exposant.bus_size)
    a_trouve_un = Constant("0")
    for i in range(mantisse.bus_size-1,-1,-1):
        compteur = adder(compteur,Constant("0"*compteur.bus_size),(~mantisse[i] & ~a_trouve_un))[0]
        a_trouve_un = a_trouve_un | mantisse[i]
    return (bitshift.ajouter_zeros_gauche(mantisse,compteur), adder(exposant, inverse_bits(compteur), Constant("1"))[0])

def fadd(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    signe_a, exposant_a, mantisse_a = encodedecode.fdecode(a)
    signe_b, exposant_b, mantisse_b = encodedecode.fdecode(b)

    

    condition = comparer.plus_grand_strict(exposant_a,exposant_b) | (comparer.egal(exposant_a,exposant_b) & comparer.plus_grand_large(mantisse_a,mantisse_b))
    
    # Fonction réalisant l'addition mais qui demande que l'exposant de a plus grand que celui de b
    def fadd_temp(a: Variable, b: Variable) -> Variable:
        assert a.bus_size == b.bus_size

        signe_a, exposant_a, mantisse_a = encodedecode.fdecode(a)
        signe_b, exposant_b, mantisse_b = encodedecode.fdecode(b)
        
        diff_exp = adder(exposant_a,inverse_bits(exposant_b),Constant("1"))[0]

        signe_different = signe_a ^ signe_b
        new_mantisse_b = bitshift.ajouter_zeros_droite(mantisse_b,diff_exp)
        new_mantisse_b = Mux(signe_different,new_mantisse_b,inverse_bits(new_mantisse_b))
        res, cout = adder(mantisse_a,new_mantisse_b,signe_different)

        new_mantisse, new_exposant = decale_exposant_addition_signe_different(res,exposant_a)
        new_mantisse = Mux(cout & ~signe_different, new_mantisse, res[1:]+Constant("1"))
        new_exposant = Mux(cout & ~signe_different, new_exposant, adder(exposant_a,Constant("0"*exposant_a.bus_size),Constant("1"))[0])

        return encodedecode.fencode(signe_a,new_exposant,new_mantisse)

    return Mux(condition, fadd_temp(b,a), fadd_temp(a,b))

def retire_zeros_gauche(mantisse: Variable, exposant: Variable) -> typing.Tuple[Variable, Variable]:
    compteur = Constant("0"*exposant.bus_size)
    a_trouve_un = Constant("0")
    for i in range(mantisse.bus_size):
        compteur = adder(compteur,Constant("0"*compteur.bus_size),(~mantisse[i] & ~a_trouve_un))[0]
        a_trouve_un = a_trouve_un | mantisse[i]
    return (bitshift.ajouter_zeros_droite(mantisse,compteur), adder(exposant, compteur, Constant("0"))[0])


def fmultiplie(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    signe_a, exposant_a, mantisse_a = encodedecode.fdecode(a)
    signe_b, exposant_b, mantisse_b = encodedecode.fdecode(b)

    new_mantisse = multiplie.multiplier_recursive(mantisse_a+Constant("00000"),mantisse_b+Constant("00000"))
    new_exposant = adder(exposant_a,exposant_b,Constant("0"))[0]
    new_signe = signe_a ^ signe_b

    new_mantisse, new_exposant = retire_zeros_gauche(new_mantisse,new_exposant)

    return encodedecode.fencode(new_signe,new_exposant,new_mantisse[:11])


def main() -> None:
    n = 16
    a = Input(n)
    b = Input(n)
    r = fmultiplie(a,b)
    r.set_as_output("z")
