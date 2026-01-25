import sys
from op_code import op_codes, three_bits

# Méthode : fichier avec une ligne par instruction

def read_reg(str):
    if str[0] != 'x':
        raise ValueError(f"{str} is not a register")
    return int(str[1:])

def to_base_2(a: int, size: int):
    if (a >= 0):
        res = bin(a)[2:]
        if (len(res) > size):
            return res[(len(res)-size):]
        return (size - len(res))*"0" + res
    if (len(bin(-a)[2:]) > size):
        raise ValueError('Int too large')
    a_opp = "0"*(size - len(bin(-a)[2:])) + (bin(-a)[2:])
    res = bin(int('0b' + (''.join([str(1 - int(x)) for x in a_opp])), 2)+1)[2:]
    return (size - len(res))*"1" + res

rom_name = "temp"
file_write_name = "temp.txt"
file_name = sys.argv[1]

i = 1
while i < len(sys.argv):
    entree = sys.argv[i]
    if entree[0] != '-':
        file_name = entree
        break
    if entree == '-o':
        i += 1
        file_write_name = sys.argv[i]
        i += 1

fd = open(file_name, 'r')
fdw = open(file_write_name, 'w')
print(rom_name, file=fdw)

labels = {}

instr = []
for line_raw in fd:
    line = line_raw.strip().lower()
    args = line.split()
    if (len(args) == 0):
        continue
    if (len(args) <= 1):
        if (args[0][-1] != ':'):
            raise ValueError("Labels must end with ':'")
        etiquette = args[0][:-1]
        labels[etiquette] = len(instr)
        continue
    instr.append(args)

for i in range(len(instr)):
    args = instr[i]
    op = args[0]
    if op in ["add", "and", "or", "xor"]:
        if (len(args) != 4):
            raise ValueError(f"Line {i} : {op} takes 3 arguments")
        rd = read_reg(args[1])
        rs1 = read_reg(args[2])
        rs2 = read_reg(args[3])
        result = "0"*7 + to_base_2(rs2, 5) + to_base_2(rs1, 5) + three_bits[op] + to_base_2(rd, 5) + op_codes[op]
        print(result[::-1], file=fdw)
    elif op in ["addi", "andi", "ori", "xori"]:
        if (len(args) != 4):
            raise ValueError(f"Line {i} : {op} takes 3 arguments")
        rd = read_reg(args[1])
        rs1 = read_reg(args[2])
        rs2 = int(args[3])
        result = to_base_2(rs2, 12) + to_base_2(rs1, 5) + three_bits[op] + to_base_2(rd, 5) + op_codes[op]
        print(result[::-1], file=fdw)
    else:
        raise ValueError("Opération non existante")
        
    

fd.close()
fdw.close()