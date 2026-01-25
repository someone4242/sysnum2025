from lib_carotte import *
from alu import *

pc_size = 8
opcode_len = 5
reg_desc_size = 5
reg_size = 32
reg_nb = 32
instr_size = 32
word_size = 32
one = true = Constant("1")
pc_incr = Constant("1" + ("0" * (pc_size - 1)))
zero = false = Constant("0")
val = [zero, one]

# sub, xor, and, or, not, ISRC, RegWrite, MemWrite, jmp, ALU src, branch

str_signal = [
    "00000" + "010010", # add  
    "00000" + "110010", # addi 
    "00100" + "010010", # and  
    "00100" + "110010", # andi 
    "00010" + "010010", # or   
    "00010" + "110010", # ori  
    "01000" + "010010", # xor  
    "01000" + "110010", # xori 
    "10000" + "010010", # sub  
    "10000" + "010010", # sll TODO
    "10000" + "010010", # slli TODO
    "10000" + "010010", # srl TODO
    "10000" + "010010", # srli TODO
    "10000" + "010010", # mul TODO
    "10000" + "010010", # jal TODO
    "10000" + "010011", # beq 
    "10000" + "010011", # bne 
    "10000" + "010011", # blt 
    "10000" + "010011", # bge 
    "10000" + "010010", # fadd TODO
    "10000" + "010010", # fsub TODO
    "10000" + "010010", # fmul TODO
    "10000" + "010010", # fdiv TODO
    "10000" + "010010", # ffisqrt TODO
    "10000" + "010010", # feq TODO
    "00000" + "010000", # load 
    "00000" + "001000", # store 
    "00000" + "000100", # jmp
    "00000" + "000100"  # jz
]
ctrl_signal = [Constant(str_signal[i]) if i < len(str_signal)
                else Constant("0" * len(str_signal[0])) for i in range(32)]

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
    stop = Input(1)
    #RAM(addr_size, word_size, read_addr, write_enable, write_addr, write_data)
    pc = RAM(1, pc_size, zero, one, zero, Defer(pc_size, lambda: next_pc)) # program counter
    reg = [RAM(1, reg_size, zero, true, zero, Defer(reg_size, lambda i=i: mov_to_reg[i])) for i in range(2**reg_desc_size)]
    reg[0] = Constant("0" * word_size)

    instr = ROM(pc_size, instr_size, pc)
    instr.set_as_output("instruction")

    signal_tree = mux_tree(instr[1:7], opcode_len, ctrl_signal)
    sub_alu, xor_alu, and_alu, or_alu, not_alu, isrc, reg_write, mem_write, jmp, alu_sr, branch = signal_tree[1]
    slr_alu = false 
    sll_alu = false
    mul_alu = false

    imm_i = Concat(instr[20:32], Constant("0"*20))
    imm_s = Concat(instr[7:12], instr[25:32])[0:pc_size]
    reg_dest = instr[7:12]
    reg_src1 = instr[15:20]
    reg_src2 = instr[20:25]
    reg_src1.set_as_output("rs1")
    reg_src2.set_as_output("rs2")
    A = mux_tree(reg_src1, reg_desc_size, reg)[1]
    B = Mux(isrc, mux_tree(reg_src2, reg_desc_size, reg)[1], imm_i)

    reg_dest.set_as_output("reg_dest")
    sub_alu.set_as_output("sub")
    xor_alu.set_as_output("xor")
    and_alu.set_as_output("and")
    or_alu.set_as_output("or")
    not_alu.set_as_output("not")
    isrc.set_as_output("isrc")
    imm_i.set_as_output()
    A.set_as_output("A")
    B.set_as_output("B")

    write_enable = demux_tree(reg_dest, reg_desc_size, [reg_write])
    ALU_res, C, V, N, Z = ALU(5, A, B, sub_alu, xor_alu, and_alu, or_alu, not_alu, sll_alu, slr_alu, mul_alu)
    E, LT = Z, N 
    NE, GE = ~E, ~LT

    ALU_res.set_as_output("ALU_result")
    mov_value = ALU_res

    #condition = mux_tree(instr[1:3], 2, [NE, LT, GE, E])
    condition = Mux(instr[2], Mux(instr[1], GE, E), Mux(instr[1], NE, LT))
    pc_offset = Mux(branch & condition, pc_incr, imm_s)
    next_pc, c, v, n, z = ALU(3, pc, pc_offset, false, false, false, false, false, false, false, false)
    mov_to_reg = [Mux(write_enable[i], reg[i], mov_value) for i in range(32)]

    pc.set_as_output("program_counter")
    for i in range(32):
        reg[i].set_as_output("x" + str(i))
    # for i in range(len(write_enable)):
    #     write_enable[i].set_as_output("write_x" + str(i))
    all_write = concat(write_enable)
    all_write.set_as_output("write")
    reg_write.set_as_output("reg_write")