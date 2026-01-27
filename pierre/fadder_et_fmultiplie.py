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
    exposant = adder(exposant,Constant("0"*exposant.bus_size),mantisse[21])[0]
    doit_sarreter = comparer.fegal_zero(mantisse[11:])
    for i in range(mantisse.bus_size):
        mantisse = Mux(doit_sarreter, mantisse[1:]+Constant("0"), mantisse)
        doit_sarreter = doit_sarreter | comparer.fegal_zero(mantisse[11:])
    return mantisse,exposant


def fmultiplie(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    signe_a, exposant_a, mantisse_a = encodedecode.fdecode(a)
    signe_b, exposant_b, mantisse_b = encodedecode.fdecode(b)
    exposant_a = exposant_a + Constant("00000000000")
    exposant_b = exposant_b + Constant("00000000000")
    
    new_mantisse = multiplie.multiplie(mantisse_a+Constant("0"*(a.bus_size-mantisse_a.bus_size)),mantisse_b+Constant("0"*(b.bus_size-mantisse_b.bus_size)))
    new_exposant = adder(exposant_a,exposant_b,Constant("0"))[0]
    new_exposant = adder(new_exposant,inverse_bits(encodedecode.biais()+Constant("0"*(new_exposant.bus_size-encodedecode.biais().bus_size))),Constant("1"))[0]
    new_signe = signe_a ^ signe_b
    new_mantisse, new_exposant = retire_zeros_gauche(new_mantisse,new_exposant)

    return encodedecode.fencode(new_signe,new_exposant,new_mantisse)


def mantisse_divise(a: Variable, b: Variable) -> Variable:
    # On augmente la taille de 1 pour pouvoir gérer les cas où a < b
    a = a + Constant("0")
    b = b + Constant("0")

    taille = b.bus_size
    moins_b = inverse_bits(b)

    condition = comparer.plus_grand_large(a,b)
    q = condition
    a =  Mux(condition, a, adder(a,moins_b,Constant("1"))[0])
    a = Constant("0") + a[:taille-1] # bitshift

    for _ in range(a.bus_size-2):
        condition = comparer.plus_grand_large(a,b)
        q = condition + q
        a =  Mux(condition, a, adder(a,moins_b,Constant("1"))[0])
        a = Constant("0") + a[:taille-1] # bitshift
    return q

def fdivise(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    signe_a, exposant_a, mantisse_a = encodedecode.fdecode(a)
    signe_b, exposant_b, mantisse_b = encodedecode.fdecode(b)

    new_mantisse = mantisse_divise(mantisse_a,mantisse_b)
    new_exposant = adder(exposant_a,encodedecode.biais()+Constant("0"*(exposant_a.bus_size-encodedecode.biais().bus_size)),Constant("0"))[0]
    new_exposant = adder(new_exposant,inverse_bits(exposant_b),Constant("1"))[0]
    new_signe = signe_a ^ signe_b
    #return mantisse_a,mantisse_b
    #new_mantisse, new_exposant = retire_zeros_gauche(new_mantisse,new_exposant)

    a_est_nan = Constant("1")
    b_est_nan = Constant("1")
    for i in range(exposant_a.bus_size):
        a_est_nan = a_est_nan & exposant_a[i]
        b_est_nan = b_est_nan & exposant_b[i]
    
    return Mux(a_est_nan | b_est_nan | comparer.fegal_zero(b), encodedecode.fencode(new_signe,new_exposant,new_mantisse, encodedecode.nan()))

def main() -> None:
    n = 16
    a = Input(n)
    b = Input(n)
    #r = fmultiplie(a,b)
    r = fdivise(a,b)
    r.set_as_output("z")



