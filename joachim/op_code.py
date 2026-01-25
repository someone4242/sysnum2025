op_codes = {
    "add" : "0000000",
    "addi" : "0000010",
    "and" : "0000100",
    "andi" : "0000110",
    "or" : "0001000",
    "ori" : "0001010",
    "xor" : "0001100",
    "xori" : "0001110",
    "sub" : "0010000",
    "sll" : "0010100",
    "srl" : "0011000"
}

three_bits = {
    "add" : "000",
    "addi" : "000",
    "and" : "111",
    "andi" : "111",
    "or" : "110",
    "ori" : "110",
    "xor" : "100",
    "or" : "100",
    "sll" : "001",
    "srl" : "101"
}

fd = open('../opcode.md', 'w')
for (key, value) in op_codes.items():
    print(f"{key} -> {value}", file=fd)
fd.close()