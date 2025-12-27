from lib_carotte import *
import functools

def full_adder(a: Variable, b: Variable, c: Variable) -> typing.Tuple[Variable, Variable]:
    '''1-bit full adder implementation'''
    tmp = a ^ b
    return (tmp ^ c, (tmp & c) | (a & b))

def adder(a: Variable, b: Variable, c_in: Variable, i: int | None = None):
    assert a.bus_size == b.bus_size
    if a.bus_size == 1:
        # Cas spécial : les entrées sont déjà des bits simples
        return full_adder(a, b, c_in)

    if i is None:
        i = a.bus_size-1
    assert 0 <= i < a.bus_size
    if i == 0:
        return full_adder(a[i], b[i], c_in)
    (res_rest, c_rest) = adder(a, b, c_in, i-1)
    (res_i, c_out) = full_adder(a[i], b[i], c_rest)
    return (res_rest + res_i, c_out)

def multiplier_recursive(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size
    n = a.bus_size
    if n == 1:
        return a & b
    if n == 2:
        return multiplier2bits(a, b)
    half = n // 2

    a_low = a[0:half]
    a_high = a[half:n]
    b_low = b[0:half]
    b_high = b[half:n]

    p_hh = multiplier_recursive(a_high, b_high)
    p_hl = multiplier_recursive(a_high, b_low)
    p_lh = multiplier_recursive(a_low, b_high)
    p_ll = multiplier_recursive(a_low, b_low)

    s, c1 = adder(p_hl, p_lh, Constant("0"))

    s1, c2 = adder(p_ll[half:2*half], s[0:half], Constant("0"))
    s2, c3 = adder(p_hh[0:half], s[half:2*half], c2)
    s3, c4 = adder(p_hh[half:2*half], extend_to_size(c1, half), c3)

    return p_ll[0:half] + s1 + s2 + s3 + c4

def multiplier2bits(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == 2
    assert b.bus_size == 2

    r1 = a[1] & b[1]
    r2 = a[0] & b[1]
    r3 = a[1] & b[0]
    r4 = a[0] & b[0]

    r5, c5 = full_adder(r2, r3, Constant("0"))
    r6, c6 = full_adder(r1, c5, Constant("0"))

    return r4 + r5 + r6 + c6

def extend_to_size(a: Variable, taille: int) -> Variable:
    if a.bus_size == taille:
        return a
    zeros = taille - a.bus_size
    return Constant("0" * zeros) + a

def main() -> None:
    n = 32
    a = Input(n)
    b = Input(n)
    result = multiplier_recursive(a,b)
    result.set_as_output("result")