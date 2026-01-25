op_codes = {
    "add" : "0000000",
    "addi" : "0000010",
    "and" : "0000100",
    "andi" : "0000110",
    "or" : "00001000",
    "ori" : "00001010",
    "xor" : "00001100",
    "xori" : "00001110"
}

three_bits = {
    "add" : "000",
    "addi" : "000",
    "and" : "111",
    "andi" : "111",
    "or" : "110",
    "ori" : "110",
    "xor" : "100",
    "or" : "100"
}

fd = open('../opcode.md', 'w')
for (key, value) in op_codes.items():
    print(f"{key} -> {value}", file=fd)
fd.close()