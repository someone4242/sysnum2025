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

def decale_exposant_addition_signe_different(mantisse: Variable, exposant: Variable) -> typing.Tuple[Variable, Variable]:
    compteur = Constant("0"*exposant.bus_size)
    a_trouve_un = Constant("0")
    for i in range(mantisse.bus_size-1,-1,-1):
        compteur = adder(compteur,Constant("0"*compteur.bus_size),(~mantisse[i] & ~a_trouve_un))[0]
        a_trouve_un = a_trouve_un | mantisse[i]
    return (bitshift.ajouter_zeros_gauche(mantisse,compteur), adder(exposant, inverse_bits(compteur), Constant("1"))[0])


def fadd_gros(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    signe_a, exposant_a, mantisse_a = a[a.bus_size-1], a[32:a.bus_size-1], a[:32]
    signe_b, exposant_b, mantisse_b = b[b.bus_size-1], b[32:b.bus_size-1], b[:32]

    

    condition = comparer.plus_grand_strict(exposant_a,exposant_b) | (comparer.egal(exposant_a,exposant_b) & comparer.plus_grand_large(mantisse_a,mantisse_b))
    
    # Fonction réalisant l'addition mais qui demande que l'exposant de a plus grand que celui de b
    def fadd_temp(a: Variable, b: Variable) -> Variable:
        assert a.bus_size == b.bus_size

        signe_a, exposant_a, mantisse_a = a[a.bus_size-1], a[32:a.bus_size-1], a[:32]
        signe_b, exposant_b, mantisse_b = b[b.bus_size-1], b[32:b.bus_size-1], b[:32]
        
        diff_exp = adder(exposant_a,inverse_bits(exposant_b),Constant("1"))[0]

        signe_different = signe_a ^ signe_b
        new_mantisse_b = bitshift.ajouter_zeros_droite(mantisse_b,diff_exp)
        new_mantisse_b = Mux(signe_different,new_mantisse_b,inverse_bits(new_mantisse_b))
        res, cout = adder(mantisse_a,new_mantisse_b,signe_different)

        new_mantisse, new_exposant = decale_exposant_addition_signe_different(res,exposant_a)
        new_mantisse = Mux(cout & ~signe_different, new_mantisse, res[1:]+Constant("1"))
        new_exposant = Mux(cout & ~signe_different, new_exposant, adder(exposant_a,Constant("0"*exposant_a.bus_size),Constant("1"))[0])

        return new_mantisse[:new_mantisse.bus_size-1]+new_exposant+signe_a

    return Mux(condition, fadd_temp(b,a), fadd_temp(a,b))


def inverse_bits(a: Variable) -> Variable:
    r = ~a[0]
    for i in range(1, a.bus_size):
        r = r + (~a[i])
    return r

def round_down(a: Variable) -> Variable:
    assert a.bus_size == 16
    signe,exposant,mantisse = encodedecode.fdecode(a)
    mantisse = mantisse + Constant("0"*(32-mantisse.bus_size+10))
    biais = encodedecode.biais()+Constant("0"*(exposant.bus_size-encodedecode.biais().bus_size))
    exposant_positif = comparer.plus_grand_large(exposant,biais)

    entier = Mux(exposant_positif,
                 bitshift.ajouter_zeros_droite(mantisse, adder(biais,inverse_bits(exposant),Constant("1"))[0]),
                 bitshift.ajouter_zeros_gauche(mantisse, adder(exposant,inverse_bits(biais),Constant("1"))[0]))
    entier = entier[10:]
    entier = Mux(signe, entier, adder(inverse_bits(entier),Constant("0"*entier.bus_size),Constant("0"))[0]) # Si négatif, on ajoute 0 car round(-3.5) = -4
    return entier

def round_up(a: Variable) -> Variable:
    return adder(round_down(a),Constant("0"*32),Constant("1"))[0]

def round_nearest_to_even(a: Variable) -> Variable:
    """
    biais = encodedecode.biais()
    s,e,m = encodedecode.fdecode(a)
    down = round_down(a)
    gros_a = Constant("0"*(down.bus_size-m.bus_size+1))+a
    diff_down = fadd_gros(gros_a,down+biais+Constant("0"*(e.bus_size-biais.bus_size))+Constant("1"))
    up = round_up(a)
    diff_up = fadd_gros(up+biais+Constant("0"*(e.bus_size-biais.bus_size))+Constant("1"),gros_a)
    ed,md = diff_down[down.bus_size:diff_down.bus_size-2], diff_down[:down.bus_size]
    eu,mu = diff_up[down.bus_size:diff_down.bus_size-2], diff_up[:down.bus_size]
    condition = comparer.plus_grand_strict(ed,eu) | (comparer.egal(ed,eu) & comparer.plus_grand_large(md,mu))
    return Mux(condition,up,down)
    """
    assert a.bus_size == 16
    signe,exposant,mantisse = encodedecode.fdecode(a)
    mantisse = mantisse + Constant("0"*(32-mantisse.bus_size+10))
    biais = encodedecode.biais()+Constant("0"*(exposant.bus_size-encodedecode.biais().bus_size))
    exposant_positif = comparer.plus_grand_large(exposant,biais)

    entier = Mux(exposant_positif,
                 bitshift.ajouter_zeros_droite(mantisse, adder(biais,inverse_bits(exposant),Constant("1"))[0]),
                 bitshift.ajouter_zeros_gauche(mantisse, adder(exposant,inverse_bits(biais),Constant("1"))[0]))
    condition_aller_superieur = entier[9] & ((entier[10] & comparer.fegal_zero(Constant("0")+entier[:9])) | ~comparer.fegal_zero(Constant("0")+entier[:9]))
    #return entier[:10],entier[10:]
    entier = entier[10:]
    entier = Mux(signe, entier, adder(inverse_bits(entier),Constant("0"*entier.bus_size),Constant("0"))[0]) # Si négatif, on ajoute 0 car round(-3.5) = -4
    return Mux(condition_aller_superieur, entier, adder(entier,Constant("0"*32),Constant("1"))[0])



def main() -> None:
    n = 16
    a = Input(n)
    r = round_nearest_to_even(a)
    r.set_as_output("z")
