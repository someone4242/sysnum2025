from lib_carotte import *
import functools

def fdecode(a: Variable) -> typing.Tuple[Variable, Variable, Variable]: # Renvoie SIGNE, EXPOSANT, MANTISSE
    assert a.bus_size == 32
    signe = a[31]
    exposant = a[23:31]
    mantisse = a[0:23]
    
    exposant_different_zero = exposant[0] | exposant[1] | exposant[2] | exposant[3] | exposant[4] | exposant[5] | exposant[6] | exposant[7]
    return (signe, exposant,mantisse + exposant_different_zero)

def fencode(s: Variable, e: Variable, m: Variable) -> Variable:
    return m[0:23] + e[0:8] + s

def biais():
    return Constant("1111111")

def nan():
    return Constant("1"*32)

def main() -> None:
    n = 32
    a = Input(n)
    signe,exposant,mantisse = fdecode(a)
    r = fencode(signe,exposant,mantisse)
    signe.set_as_output("signe")
    exposant.set_as_output("exposant")
    mantisse.set_as_output("mantisse")
    r.set_as_output("result")

