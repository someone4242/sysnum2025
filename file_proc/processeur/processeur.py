from lib_carotte import *
from alu import *
from convert import *
from comparer import *
from fadder_et_fmultiplie import *
from fast_inverse_square_root import *

ram_addr_size = 8
ram_size = 2**ram_addr_size
pc_size = 8
opcode_len = 5
reg_desc_size = 5
reg_size = 32
reg_nb = 32
instr_size = 32
word_size = 32
one = true = Constant("1")
zero = false = Constant("0")
val = [zero, one]

zero_32bit = Constant("0" * word_size)
one_8bit = Constant("1" + ("0" * (pc_size - 1)))
one_32bit = Constant("1" + ("0" * (word_size - 1)))

# floats, div/isqrt, conversion, sub, xor, and, or, not, sll, srl, mul, i_src, RegWrite, MemWrite, jmp, MemRead, compare, rdtime

signal_lookup_table = [
    "000" + "00000000" + "0100000", # add  
    "000" + "00000000" + "1100000", # addi 
    "000" + "00100000" + "0100000", # and  
    "000" + "00100000" + "1100000", # andi 
    "000" + "00010000" + "0100000", # or   
    "000" + "00010000" + "1100000", # ori  
    "000" + "01000000" + "0100000", # xor  
    "000" + "01000000" + "1100000", # xori 
    "000" + "10000000" + "0100000", # sub  
    "000" + "00000000" + "0010000", # sw 
    "000" + "00000010" + "0100000", # sll
    "000" + "00000010" + "1100000", # slli
    "000" + "00000100" + "0100000", # srl
    "000" + "00000100" + "1100000", # srli
    "000" + "00000001" + "0100000", # mul 
    "000" + "00000000" + "0100100", # lw 
    "000" + "00000000" + "0101000", # jal 
    "000" + "10000000" + "0000010", # beq 
    "000" + "10000000" + "0000010", # bne 
    "000" + "10000000" + "0000010", # blt 
    "000" + "10000000" + "0000010", # bge 
    "000" + "00000000" + "0100001", # rdtime
    "100" + "00000000" + "0000000", # fadd 
    "100" + "00000000" + "0000000", # fsub
    "100" + "00000000" + "0000000", # fmul 
    "110" + "00000000" + "0000000", # fdiv 
    "110" + "00000000" + "0000000", # ffisqrt 
    "100" + "00000000" + "0000010", # feq
    "001" + "00000000" + "0000000", # fcvt.w flottant vers entier
    "001" + "00000000" + "0000000", # fcvt.s entier vers flottant
    "000" + "00000000" + "0100001"  # rdclock
]
ctrl_signal = [Constant(signal_lookup_table[i]) if i < len(signal_lookup_table)
                else Constant("0" * len(signal_lookup_table[0])) for i in range(1 << opcode_len)]

def mux_tree(opcode, nb_bits, data):
    tree = [zero for i in range(1 << (nb_bits + 1))]
    def build_tree(i, pos):
        if pos < 0:
            tree[i] = data[i - (1 << nb_bits)]
        else:
            tree[i] = Mux(opcode[pos], build_tree(i*2, pos-1), build_tree(i*2+1, pos-1))
        return tree[i]
    build_tree(1, nb_bits-1)
    return tree

def demux_tree(code, nb_bits, data):
    def build_tree(pos, layer):
        if pos < 0:
            return layer 
        else: 
            next_layer = []
            for i in range(len(layer)):
                next_layer.append(Mux(code[pos], layer[i], false))
                next_layer.append(Mux(code[pos], false, layer[i]))
            return build_tree(pos-1, next_layer)
    return build_tree(nb_bits-1, data)

def concat(data):
    if len(data) == 1:
        return data[0]
    mid = len(data)//2 
    return concat(data[:mid]) + concat(data[mid:])

def sign_extend(data, length):
    return concat([data] + ([data[len(data)-1]] * (length - len(data))))

def float_operation(A, B, eq, sub, mul, div, isqrt):
    B_opp = B[:(word_size - 1)] + ~B[word_size - 1]
    B_true = bus_unfold_def(word_size, lambda i : Mux(sub, B[i], B_opp[i]))

    A_op_B = fadd(A, B)
    A_eq_B = fegal(A, B) + Constant("0" * (word_size - 1))
    AB = fmultiplie(A, B)
    A_div_B = fdivise(A, B)
    isqrtA = fast_inverse_square_root(A)
    return Mux(~eq, A_eq_B, Mux(~mul, AB, Mux(~div, A_div_B, Mux(~isqrt, isqrtA, A_op_B))))

def main():
    write_enable = 1
    clock = Input(word_size)
    time = Input(word_size)
    #stop = Input(1)
    #RAM(addr_size, word_size, read_addr, write_enable, write_addr, write_data)
    pc = RAM(1, pc_size, zero, one, zero, Defer(pc_size, lambda: next_pc)) # program counter
    reg = [RAM(1, reg_size, zero, true, zero, Defer(reg_size, lambda i=i: mov_to_reg[i])) for i in range(2**reg_desc_size)]
    reg[0] = Constant("0" * word_size)

    # lecture de l'instruction et préparation des signaux
    instr = ROM(pc_size, instr_size, pc)
    signal_tree = mux_tree(instr[0:opcode_len], opcode_len, ctrl_signal)
    (is_float, float_opcode, convert, sub_alu, xor_alu, and_alu, or_alu, not_alu, sll_alu,
    srl_alu, mul_alu, isrc, reg_write, mem_write, jmp, mem_read, compare, 
    rdtime) = signal_tree[1]

    imm_i = sign_extend(instr[20:32], word_size)
    imm_s = (instr[7:12] + instr[25:32])[0:pc_size]
    reg_dest = instr[7:12]
    reg_src1 = instr[15:20]
    reg_src2 = instr[20:25]
    jmp_offset = instr[12:12+pc_size]
    mem_offset = imm_i
    rs1_value = mux_tree(reg_src1, reg_desc_size, reg)[1]
    rs2_value = mux_tree(reg_src2, reg_desc_size, reg)[1]
    A = rs1_value
    B = Mux(isrc, rs2_value, imm_i)
    mem_addr, n, z, c, v = ALU(5, A, mem_offset, false, false, false, false, false, false, false, false)

    # calcul de la mémoire 
    mem_value = RAM(ram_addr_size, word_size, mem_addr[0:8], mem_write, mem_addr[0:8], rs2_value)

    # calcul du résultat de l'ALU et des flags
    float_div = Mux(float_opcode, false, instr[0])
    float_isqrt = Mux(float_opcode, false, instr[1])
    float_res = zero_32bit # remplacer par float_operation(A, B, compare, sub_alu, mul_alu, float_div, float_isqrt) pour activer les opérations flottantes
    write_enable = demux_tree(reg_dest, reg_desc_size, [reg_write])
    ALU_res, C, V, N, Z = ALU(5, A, B, sub_alu, xor_alu, and_alu, or_alu, not_alu, sll_alu, srl_alu, mul_alu)
    E, LT = Z, N 
    NE, GE = ~E, ~LT

    #calcul du program counter
    #condition = mux_tree(instr[1:3], 2, [NE, LT, GE, E])
    branch = compare & (~is_float)
    pc_incr, c, v, n, z = ALU(3, pc, one_8bit, false, false, false, false, false, false, false, false)
    condition = Mux(instr[1], Mux(instr[0], GE, E), Mux(instr[0], NE, LT))
    pc_offset = Mux(branch & condition, Mux(jmp, one_8bit, jmp_offset), imm_s)
    next_pc, c, v, n, z = ALU(3, pc, pc_offset, false, false, false, false, false, false, false, false)


    # calcul de mov_value
    computed_val = Mux(jmp, Mux(is_float, ALU_res, float_res), sign_extend(pc_incr, reg_size))
    mov_value = Mux(convert, Mux(rdtime, Mux(mem_read, computed_val, mem_value), Mux(instr[0], clock, time)), Mux(instr[0], fround_down(rs1_value), rs1_value))
    mov_to_reg = [Mux(write_enable[i], reg[i], mov_value) for i in range(reg_nb)]

    reg[2].set_as_output("secondes")
    reg[3].set_as_output("minutes")
    reg[4].set_as_output("heures")
    reg[5].set_as_output("jours")
    reg[6].set_as_output("annees")
    reg[8].set_as_output("mois")

    instr.set_as_output("instruction")