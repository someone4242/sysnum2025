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
one_8 = Constant("1" + ("0" * 7))
zero = false = Constant("0")
val = [zero, one]

# sub, xor, and, or, not, ISRC, Mem to Reg, MemWrite, jmp, ALU sr

str_signal = [
    "00000" + "00001", # add
    "01000" + "00001", # xor
    "00100" + "00001", # and 
    "00010" + "00001", # or 
    "00000" + "10000", # addi 
    "00000" + "01000", # load 
    "00000" + "00100", # store 
    "00000" + "00010", # jmp
    "00000" + "00010"  # jz
]
ctrl_signal = [Constant(str_signal[i]) if i < len(str_signal)
                else Constant("0" * len(str_signal[0])) for i in range(32)]

def mux_tree(instr, nb_bits, data):
    tree = [zero for i in range(1 << (nb_bits + 1))]
    def build_tree(i, pos):
        if pos == nb_bits:
            tree[i] = data[i - (1 << nb_bits)]
        else:
            tree[i] = Mux(instr[pos], build_tree(i*2, pos+1), build_tree(i*2+1, pos+1))
        return tree[i]
    build_tree(1, 0)
    return tree

def main():
    write_enable = 1
    stop = Input(1)
    #RAM(addr_size, word_size, read_addr, write_enable, write_addr, write_data)
    pc = RAM(1, pc_size, zero, one, zero, Defer(pc_size, lambda: next_pc)) # program counter
    reg = [RAM(1, reg_size, zero, Defer(1, lambda: write_enable[i]), zero, Defer(reg_size, lambda: mov_value)) for i in range(2**reg_desc_size)]
    reg[0] = Constant("0" * word_size)

    instr = ROM(pc_size, instr_size, pc)
    instr.set_as_output("instruction")

    signal_tree = mux_tree(instr, opcode_len, ctrl_signal)
    sub_alu, xor_alu, and_alu, or_alu, not_alu, isrc, mem_to_reg, mem_write, jmp, alu_sr = signal_tree[1]

    imm_i = Concat(instr[20:32], Constant("0"*20))
    imm_s = Concat(instr[7:12], instr[25:32])
    reg_dest = instr[7:12]
    reg_src1 = instr[15:20]
    reg_src2 = instr[20:25]
    A = mux_tree(reg_src1, reg_desc_size, reg)[1]
    B = Mux(isrc, mux_tree(reg_src2, reg_desc_size, reg)[1], imm_i)
    A.set_as_output("X")
    B.set_as_output("Y")
    ALU_res, C, V, N, Z = ALU(5, A, B, sub_alu, xor_alu, and_alu, or_alu, not_alu)
    
    ALU_res.set_as_output("ALU_result")

    next_pc, c, v, n, z = ALU(3, pc, one_8, false, false, false, false, false)
    pc.set_as_output("program_counter")
    # for i in range(32):
    #     reg[i].set_as_output("x" + str(i))
    #ALU_res.set_as_output("ALU_output")
    write_enable = [one for i in range(reg_nb)]
    mov_value = Constant("0" * word_size)