from lib_carotte import *
import functools
import encodedecode
import comparer
import bitshift
import fulladder

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

def fround_down(a: Variable) -> Variable:
    assert a.bus_size == 32
    signe,exposant,mantisse = encodedecode.fdecode(a)
    mantisse = mantisse + Constant("0"*(32-mantisse.bus_size+23))
    biais = encodedecode.biais()+Constant("0"*(exposant.bus_size-encodedecode.biais().bus_size))
    exposant_positif = comparer.plus_grand_large(exposant,biais)

    entier = Mux(exposant_positif,
                 bitshift.ajouter_zeros_droite(mantisse, adder(biais,inverse_bits(exposant),Constant("1"))[0]),
                 bitshift.ajouter_zeros_gauche(mantisse, adder(exposant,inverse_bits(biais),Constant("1"))[0]))
    entier = entier[23:]
    entier = Mux(signe, entier, adder(inverse_bits(entier),Constant("0"*entier.bus_size),Constant("0"))[0]) # Si négatif, on ajoute 0 car round(-3.5) = -4
    return entier

def fround_up(a: Variable) -> Variable:
    return adder(round_down(a),Constant("0"*32),Constant("1"))[0]

def fround_nearest_to_even(a: Variable) -> Variable:
    assert a.bus_size == 32
    signe,exposant,mantisse = encodedecode.fdecode(a)
    mantisse = mantisse + Constant("0"*(32-mantisse.bus_size+23))
    biais = encodedecode.biais()+Constant("0"*(exposant.bus_size-encodedecode.biais().bus_size))
    exposant_positif = comparer.plus_grand_large(exposant,biais)

    entier = Mux(exposant_positif,
                 bitshift.ajouter_zeros_droite(mantisse, adder(biais,inverse_bits(exposant),Constant("1"))[0]),
                 bitshift.ajouter_zeros_gauche(mantisse, adder(exposant,inverse_bits(biais),Constant("1"))[0]))
    condition_aller_superieur = entier[22] & ((entier[23] & comparer.fegal_zero(entier[:23])) | ~comparer.fegal_zero(entier[:23]))
    #return entier[:10],entier[10:]
    entier = entier[23:]
    entier = Mux(signe, entier, adder(inverse_bits(entier),Constant("0"*entier.bus_size),Constant("0"))[0]) # Si négatif, on ajoute 0 car round(-3.5) = -4
    return Mux(condition_aller_superieur, entier, adder(entier,Constant("0"*32),Constant("1"))[0])



def main() -> None:
    n = 32
    a = Input(n)
    r = round_nearest_to_even(a)
    r.set_as_output("z")
