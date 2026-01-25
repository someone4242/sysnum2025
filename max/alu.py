
from lib_carotte import *

# (2**N_exp)-bit integers (signed or unsigned two-complement)

# Utils

def bus_unfold_def(bus_size, lam):
    bus = lam(0)
    for i in range(1, bus_size):
        bus = bus + lam(i)
    return bus

def multi_And(var_list):
    if len(var_list) == 1:
        return var_list[0]
    n = len(var_list) // 2
    return And(multi_And(var_list[:n]), multi_And(var_list[n:]))

def multi_Or(var_list):
    if len(var_list) == 1:
        return var_list[0]
    n = len(var_list) // 2
    return Or(multi_Or(var_list[:n]), multi_Or(var_list[n:]))

def is_null(bus):
    if bus.bus_size == 1:
        return ~bus[0]
    elif bus.bus_size == 2:
        return And(~bus[0], ~bus[1])
    elif bus.bus_size == 3:
        return And(~bus[0], And(~bus[1], ~bus[2]))
 
    n = bus.bus_size // 2
    return is_null(bus[:n]) & is_null(bus[n:])


# Bitshifts de Pierre

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


# Carry-Lookahead Adder

def gen_prop_1_bit_adder(a, b, c):
    return (a^b^c, a^b, a&b) # R, P, G

def nadder(N_exp, A, B, C0):
    N = 2**N_exp
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

# ALU

def ALU(N_exp, A, B, Sub_inp, Xor_inp, And_inp, Or_inp, Not_inp,
        Sll_inp, Srl_inp, Mul_inp):
    N = 2**N_exp
    nadder_A = A
    nadder_B = bus_unfold_def(N, lambda i : (B[i] ^ Sub_inp) | Not_inp)
    nadder_X = Sub_inp

    nadder_S, nadder_C, nadder_XOR, nadder_AND = nadder(
            N_exp, nadder_A, nadder_B, nadder_X)

    sll_S = ajouter_zeros_droite(A, B[:N_exp])
    srl_S = ajouter_zeros_gauche(A, B[:N_exp])
    mul_S = multiplie(A, B)


    arith_out = multi_And([~Xor_inp, ~And_inp, ~Or_inp, ~Not_inp])
    S = bus_unfold_def(N, lambda i : multi_Or([
            arith_out & nadder_S[i],
            And_inp & nadder_AND[i],
            (Xor_inp | Not_inp) & nadder_XOR[i],
            Or_inp & (nadder_AND[i] | nadder_XOR[i]),
            Sll_inp & sll_S[i],
            Srl_inp & srl_S[i],
            Mul_inp & mul_S[i]
        ]))



    flag_C = nadder_C
    flag_V = And( ~(Xor(A[N-1],B[N-1])), Xor(A[N-1], S[N-1]))
    flag_N = S[N-1]
    flag_Z = is_null(S)

    return S, flag_C, flag_V, flag_N, flag_Z

"""
def main():
    N_exp = 5
    N = 2**N_exp
    A, B = Input(N, "A"), Input(N, "B")
    Sub_inp = Input(1, "Sub")
    Xor_inp = Input(1, "Xor")
    And_inp = Input(1, "And")
    Or_inp = Input(1, "Or")
    Not_inp = Input(1, "Not")

    S, C, flag_V, flag_N, flag_Z = ALU(
            N_exp, A, B,
            Sub_inp, Xor_inp, And_inp, Or_inp, Not_inp)

    S.set_as_output("S")
    C.set_as_output("C")
    flag_V.set_as_output("V")
    flag_N.set_as_output("N")
    flag_Z.set_as_output("Z")
"""

