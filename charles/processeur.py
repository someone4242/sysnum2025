from lib_carotte import *

pc_size = 8
reg_size = 32
instr_size = 32
one = true = Constant("1")
zero = false = Constant("0")
val = [zero, one]

# ALU ctrl 0, ALU ctrl 1, ISRC, Mem to Reg, MemWrite, jmp, ALU sr

str_signal = [
    "1100001", # add
    "1000001", # xor
    "0100001", # and 
    "0000001", # or 
    "1100000", # addi 
    "1101000", # load 
    "1110100", # store 
    "1110010", # jmp
    "1110010"  #jz
]
ctrl_signal = [Constant(str_signal[i]) if i < len(str_signal)
                else Constant("0" * 7) for i in range(32)]

def ctrl_signal_select_tree(instr):
    nb_bits = 5
    tree = [zero for i in range(1 << (nb_bits + 1))]
    def build_tree(i, pos):
        if pos == nb_bits:
            tree[i] = ctrl_signal[i - (1 << nb_bits)]
        else:
            tree[i] = Mux(instr[pos], build_tree(i*2, pos+1), build_tree(i*2+1, pos+1))
        return tree[i]
    build_tree(1, 0)
    return tree

def main():
    addr_size = 0
    write_enable = 1
    write_data = Input(pc_size)
    # RAM(addr_size, word_size, read_addr, write_enable, write_addr, write_data)
    pc = RAM(1, pc_size, zero, one, zero, Defer(pc_size, lambda: next_pc)) # program counter
    reg = [RAM(1, reg_size, zero, Defer(1, lambda: write_enable[i]), zero, Defer(reg_size, lambda: mov_value)) for i in range(32)]
    reg[0] = Constant("0" * 32)

    instruction = ROM(pc_size, instr_size, pc)

    signal_tree = ctrl_signal_select_tree(instruction)
    alu_ctrl_0, alu_ctrl_1, isrc, mem_to_reg, mem_write, jmp, alu_sr = signal_tree[1]

    write_enable = [one for i in range(32)]
    mov_value = Constant("0" * 32)

    next_pc = Constant("0" * 8)
    pc.set_as_output("program_counter")
    for i in range(32):
        reg[i].set_as_output("x" + str(i))