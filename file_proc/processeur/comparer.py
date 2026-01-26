from lib_carotte import *
import functools


def fegal_zero(a: Variable) -> Variable:
    res = Constant("0")
    for i in range(a.bus_size-1): #pas le bit de signe
        res = res | a[i]
    return ~res


def fegal(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    a_egal_zero = fegal_zero(a)
    b_egal_zero = fegal_zero(b)

    res = Constant("1")
    for i in range(a.bus_size):
        res = res & ~(a[i] ^ b[i])

    return (a_egal_zero & b_egal_zero) | res

def egal(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    res = Constant("1")
    for i in range(a.bus_size):
        res = res & ~(a[i] ^ b[i])

    return res

def plus_grand_large(a: Variable, b: Variable) -> Variable: # a >= b
    assert a.bus_size == b.bus_size

    res = Constant("1")
    a_strictement_plus_grand = Constant("0")
    for i in range(a.bus_size-1,-1,-1):
        a_strictement_plus_grand = (a_strictement_plus_grand | (a[i] & ~b[i])) & res
        res = (res & (a[i] | ~b[i])) | a_strictement_plus_grand

    return res

def plus_grand_strict(a: Variable, b: Variable) -> Variable:
    assert a.bus_size == b.bus_size

    return plus_grand_large(a,b) & ~egal(a,b)

def main() -> None:
    n = 2
    a = Input(n)
    b = Input(n)
    r = plus_grand_strict(a,b)
    r.set_as_output("result")

