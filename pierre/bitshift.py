from lib_carotte import *

def ajouter_zeros_droite(a: Variable, decalage: Variable) -> Variable:
    for i in range(decalage.bus_size):
        bit = decalage[i]        
        shift_for_bit = 1 << i
        if shift_for_bit < a.bus_size:
            shifted_version = a[shift_for_bit:] + Constant("0" * shift_for_bit)
            a = Mux(bit, a, shifted_version)
        else:
            a = Mux(bit, a, Constant("0"*a.bus_size))
    
    return a

def ajouter_zeros_gauche(a: Variable, decalage: Variable) -> Variable:
    for i in range(decalage.bus_size):
        bit = decalage[i]
        shift_for_bit = 1 << i
        if shift_for_bit < a.bus_size:
            shifted_version = Constant("0" * shift_for_bit) + a[:a.bus_size-shift_for_bit]
            a = Mux(bit, a, shifted_version)
        else:
            a = Mux(bit, a, Constant("0"*a.bus_size))
    
    return a

def main() -> None:
    a = Input(4)
    decalage = Input(4)
    result = ajouter_zeros_droite(a, decalage)
    result.set_as_output("final_bitshift")