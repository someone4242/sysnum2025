from lib_carotte import *
import functools
import bitshift
import fulladder
import comparer
import multiplie

def fdecode32(a: Variable) -> typing.Tuple[Variable, Variable, Variable]: # Renvoie SIGNE, EXPOSANT, MANTISSE
    assert a.bus_size == 32
    signe = a[31]
    exposant = a[23:31]
    mantisse = a[0:23]
    
    exposant_different_zero = exposant[0] | exposant[1] | exposant[2] | exposant[3] | exposant[4] | exposant[5] | exposant[6] | exposant[7]
    return (signe, exposant,mantisse + exposant_different_zero)

def fencode32(s: Variable, e: Variable, m: Variable) -> Variable:
    return m[0:23] + e[0:8] + s

def biais32():
    return Constant("1111111000000000000")

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

def nadder(A, B, C0):
    N = 32
    assert A.bus_size == N and B.bus_size == N

    def carry_lookahead(height, a, b, c):
        if height == 0:
            r, p, g = gen_prop_1_bit_adder(a, b, c)
            return r, p, g, p, g
        n = len(a)//2
        r0, p0, g0, xor_bus0, and_bus0 = carry_lookahead(
                height -1, a[0:n], b[0:n], c)
        c1 = g0 | (p0 & c)
        r1, p1, g1, xor_bus1, and_bus1 = carry_lookahead(
                height -1, a[n:2*n], b[n:2*n], c1)

        r, p, g = (r0+r1), (p0 & p1), (g1 | (g0 & p1))
        xor_bus, and_bus = xor_bus0 + xor_bus1, and_bus0 + and_bus1
        return r, p, g, xor_bus, and_bus

    R, P, G, X, A = carry_lookahead(N_exp, A, B, C0)
    return R, (G | (P & C0)), X, A

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

def fadd32(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    signe_a, exposant_a, mantisse_a = fdecode32(a)
    signe_b, exposant_b, mantisse_b = fdecode32(b)

    

    condition = comparer.plus_grand_strict(exposant_a,exposant_b) | (comparer.egal(exposant_a,exposant_b) & comparer.plus_grand_large(mantisse_a,mantisse_b))
    
    # Fonction réalisant l'addition mais qui demande que l'exposant de a plus grand que celui de b
    def fadd_temp(a: Variable, b: Variable) -> Variable:
        assert a.bus_size == b.bus_size

        signe_a, exposant_a, mantisse_a = fdecode32(a)
        signe_b, exposant_b, mantisse_b = fdecode32(b)
        
        diff_exp = adder(exposant_a,inverse_bits(exposant_b),Constant("1"))[0]

        signe_different = signe_a ^ signe_b
        new_mantisse_b = bitshift.ajouter_zeros_droite(mantisse_b,diff_exp)
        new_mantisse_b = Mux(signe_different,new_mantisse_b,inverse_bits(new_mantisse_b))
        res, cout = adder(mantisse_a,new_mantisse_b,signe_different)

        new_mantisse, new_exposant = decale_exposant_addition_signe_different(res,exposant_a)
        new_mantisse = Mux(cout & ~signe_different, new_mantisse, res[1:]+Constant("1"))
        new_exposant = Mux(cout & ~signe_different, new_exposant, adder(exposant_a,Constant("0"*exposant_a.bus_size),Constant("1"))[0])

        return fencode32(signe_a,new_exposant,new_mantisse)

    return Mux(condition, fadd_temp(b,a), fadd_temp(a,b))

def retire_zeros_gauche(mantisse: Variable, exposant: Variable) -> typing.Tuple[Variable, Variable]:
    exposant = adder(exposant,Constant("0"*exposant.bus_size),mantisse[47])[0]
    doit_sarreter = comparer.fegal_zero(mantisse[23:])
    for i in range(mantisse.bus_size):
        mantisse = Mux(doit_sarreter, mantisse[1:]+Constant("0"), mantisse)
        doit_sarreter = doit_sarreter | comparer.fegal_zero(mantisse[23:])
    return mantisse,exposant



def fmultiplie32(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    signe_a, exposant_a, mantisse_a = fdecode32(a)
    signe_b, exposant_b, mantisse_b = fdecode32(b)
    exposant_a = exposant_a + Constant("00000000000")
    exposant_b = exposant_b + Constant("00000000000")
    
    new_mantisse = multiplie.multiplie(mantisse_a+Constant("0"*(a.bus_size-mantisse_a.bus_size)),mantisse_b+Constant("0"*(b.bus_size-mantisse_b.bus_size)))
    new_exposant = adder(exposant_a,exposant_b,Constant("0"))[0]
    new_exposant = adder(new_exposant,inverse_bits(biais32()),Constant("1"))[0]
    new_signe = signe_a ^ signe_b
    new_mantisse, new_exposant = retire_zeros_gauche(new_mantisse,new_exposant)

    return fencode32(new_signe,new_exposant[:8],new_mantisse[:23])


def fast_inverse_square_root(number: Variable) -> Variable:
    trois_demi = Constant("00000000000000000000001111111100")
    x2 = fmultiplie32(number,Constant("00000000000000000000000011111100"))
    i = number # i est un int
    i = adder(Constant("11111011100110101110110011111010"), inverse_bits(number[1:]+Constant("0")), Constant("1"))[0]
    y = i # y est un float
    y2 = fmultiplie32(y,y)
    xy = fmultiplie32(x2,y2)
    s = fadd32(trois_demi,xy[:31] + ~xy[31]) # On change le signe du 2e terme pour faire une soustraction
    y = fmultiplie32(y, s)
    return y


def main() -> None:
    n = 32
    a = Input(n)
    r = fast_inverse_square_root(a)
    r.set_as_output("result")
