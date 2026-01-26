from lib_carotte import *
from alu import *

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
one_8bit = Constant("1" + ("0" * (pc_size - 1)))
zero = false = Constant("0")
val = [zero, one]

# sub, xor, and, or, not, sll, srl, mul, i_src, RegWrite, MemWrite, jmp, MemRead, branch, rdtime

str_signal = [
    "00000000" + "0100000", # add  
    "00000000" + "1100000", # addi 
    "00100000" + "0100000", # and  
    "00100000" + "1100000", # andi 
    "00010000" + "0100000", # or   
    "00010000" + "1100000", # ori  
    "01000000" + "0100000", # xor  
    "01000000" + "1100000", # xori 
    "10000000" + "0100000", # sub  
    "00000000" + "0010000", # sw TO check
    "00000010" + "0100000", # sll
    "00000010" + "1100000", # slli
    "00000100" + "0100000", # srl
    "00000100" + "1100000", # srli
    "00000001" + "0100000", # mul 
    "00000000" + "0100100", # lw TO check
    "00000000" + "0101000", # jal TO check
    "00000000" + "0100010", # beq 
    "00000000" + "0100010", # bne 
    "00000000" + "0100010", # blt 
    "00000000" + "0100010", # bge 
    "00000000" + "0100001", # rdtime TO check
    "00000000" + "0100000", # fadd TODO
    "00000000" + "0100000", # fsub TODO
    "00000000" + "0100000", # fmul TODO
    "00000000" + "0100000", # fdiv TODO
    "00000000" + "0100000", # ffisqrt TODO
    "00000000" + "0100000", # feq TODO
]
ctrl_signal = [Constant(str_signal[i]) if i < len(str_signal)
                else Constant("0" * len(str_signal[0])) for i in range(1 << opcode_len)]

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
    return Concat(concat(data[:mid]), concat(data[mid:]))

def main():
    write_enable = 1
    clock = Input(32)
    #stop = Input(1)
    #RAM(addr_size, word_size, read_addr, write_enable, write_addr, write_data)
    pc = RAM(1, pc_size, zero, one, zero, Defer(pc_size, lambda: next_pc)) # program counter
    reg = [RAM(1, reg_size, zero, true, zero, Defer(reg_size, lambda i=i: mov_to_reg[i])) for i in range(2**reg_desc_size)]
    reg[0] = Constant("0" * word_size)

    # lecture de l'instruction et préparation des signaux
    instr = ROM(pc_size, instr_size, pc)
    signal_tree = mux_tree(instr[1:1+opcode_len], opcode_len, ctrl_signal)
    sub_alu, xor_alu, and_alu, or_alu, not_alu, sll_alu, srl_alu, mul_alu, isrc, reg_write, mem_write, jmp, mem_read, branch, rdtime = signal_tree[1]
    imm_i = Concat(instr[20:32], Constant("0"*20))
    imm_s = Concat(instr[7:12], instr[25:32])[0:pc_size]
    reg_dest = instr[7:12]
    reg_src1 = instr[15:20]
    reg_src2 = instr[20:25]
    jmp_offset = instr[12:12+pc_size]
    mem_offset = Concat(instr[20:32], Constant("0"*20))
    rs1_value = mux_tree(reg_src1, reg_desc_size, reg)[1]
    rs2_value = mux_tree(reg_src2, reg_desc_size, reg)[1]
    A = rs1_value
    B = Mux(isrc, rs2_value, imm_i)
    mem_addr, n, z, c, v = ALU(5, A, mem_offset, false, false, false, false, false, false, false, false)

    # calcul de la mémoire 
    mem_value = RAM(ram_addr_size, word_size, mem_addr[0:8], mem_write, mem_addr[0:8], rs2_value)

    # calcul du résultat de l'ALU et des flags
    write_enable = demux_tree(reg_dest, reg_desc_size, [reg_write])
    ALU_res, C, V, N, Z = ALU(5, A, B, sub_alu, xor_alu, and_alu, or_alu, not_alu, sll_alu, srl_alu, mul_alu)
    E, LT = Z, N 
    NE, GE = ~E, ~LT

    #calcul du program counter
    #condition = mux_tree(instr[1:3], 2, [NE, LT, GE, E])
    pc_incr, c, v, n, z = ALU(3, pc, one_8bit, false, false, false, false, false, false, false, false)
    condition = Mux(instr[2], Mux(instr[1], GE, E), Mux(instr[1], NE, LT))
    pc_offset = Mux(branch & condition, Mux(jmp, one_8bit, jmp_offset), imm_s)
    next_pc, c, v, n, z = ALU(3, pc, pc_offset, false, false, false, false, false, false, false, false)


    # calcul de mov_value
    mov_value = Mux(rdtime, Mux(mem_read, Mux(jmp, ALU_res, Concat(pc_incr, Constant("0"*(reg_size - pc_size)))), mem_value), clock)
    mov_to_reg = [Mux(write_enable[i], reg[i], mov_value) for i in range(reg_nb)]


    instr.set_as_output("instruction")
    reg_src1.set_as_output("rs1")
    reg_src2.set_as_output("rs2")
    reg_dest.set_as_output("reg_dest")
    sub_alu.set_as_output("sub")
    xor_alu.set_as_output("xor")
    and_alu.set_as_output("and")
    or_alu.set_as_output("or")
    not_alu.set_as_output("not")
    sll_alu.set_as_output("sll")
    srl_alu.set_as_output("srl")
    mul_alu.set_as_output("mul")
    isrc.set_as_output("isrc")
    imm_i.set_as_output()
    A.set_as_output("A")
    B.set_as_output("B")
    ALU_res.set_as_output("ALU_result")

    pc.set_as_output("program_counter")

    for i in range(1, 9):
        reg[i].set_as_output("x" + str(i))
    reg[30].set_as_output("x" + str(30))
    all_write = concat(write_enable)
    all_write.set_as_output("write")
    reg_write.set_as_output("reg_write")
    GE.set_as_output("ge")
    E.set_as_output("e")
    NE.set_as_output("ne")
    LT.set_as_output("lt")
    branch.set_as_output("branch")
    condition.set_as_output("condition")
    imm_s.set_as_output("imm_s")
    jmp.set_as_output("jmp")
    jmp_offset.set_as_output("jmp_offset")
    pc_offset.set_as_output("pc_offset")
    pc.set_as_output("program_counter")
    next_pc.set_as_output("next_program_counter")
    mov_value.set_as_output("mov_value")
    pc_incr.set_as_output("pc_incr")
    clock.set_as_output("clock")
    rdtime.set_as_output("rdtime")