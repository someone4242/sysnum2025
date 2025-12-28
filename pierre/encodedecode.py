from lib_carotte import *
import functools

def fdecode(a: Variable) -> typing.Tuple[Variable, Variable, Variable]: # Renvoie SIGNE, EXPOSANT, MANTISSE
    assert a.bus_size == 16
    signe = a[15]
    exposant = a[10:15]
    mantisse = a[0:10]
    
    exposant_different_zero = exposant[0] | exposant[1] | exposant[2] | exposant[3] | exposant[4]
    return (signe, exposant,mantisse + exposant_different_zero)

def fencode(s: Variable, e: Variable, m: Variable) -> Variable:
    return m[0:10] + e + s

def biais():
    return Constant("1111")

def nan():
    return Constant("1"*16)

def main() -> None:
    n = 16
    a = Input(n)
    signe,exposant,mantisse = fdecode(a)
    r = fencode(signe,exposant,mantisse)
    signe.set_as_output("signe")
    exposant.set_as_output("exposant")
    mantisse.set_as_output("mantisse")
    r.set_as_output("result")
