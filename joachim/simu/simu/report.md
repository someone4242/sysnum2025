# Project part 1 : Netlist simulator

## General comments

The files netlist_simulator.ml and graph.ml contain my work of the lab session 1 (part one of the project). The other files were the ones provided, alongside with some other test I have added, and a makefile which can build netlist_simulator.byte. I have also implmented a calculation of the critical path (suggested in an other lab session), which is printed at the beginning of the execution.

## Implementation

To begin with, as suggested in the lab session 1, the program schedules the netlist to compute the variable in the good order. Then it initializes everything it will need ; the RAMs (filled with 0 at first), the ROMs (specified below), the registers...

Then for each step, the program asks the input to the user, then after parsing computes the value of each variable in the netlist in the order given by the scheduler. The values are stored in an environment. The program delays the write instructions in the RAMs to the end.

## Difficulties encountered

The scheduler and the basic operation (AND, OR...) were easy enough to implement. However, when it came to RAM and ROM, I struggled to understand the excepected behaviour (since no examples were provided). I had to come up with my own implementation, in a way that seems to make sense for me.

## ROM specification

The ROM from a netlist is to be provided in another file, whose name must be specified with "-rom {filename}" when running netlist_simulator.byte. The file must consist of several block separated by empty lines : the first line of the block must be the identifier of the gate where the ROM instruction is used (for instance "o" in o = ROM addr_size word_size read_addr) and the lines which follow must be the words stored in the ROM, one by line. Note that if there are too few or too many words, the program will accept the ROM anyways and fill the rest with 0, and ignore the excessive words. There can be additional ROMs in the file that are not used in the program : the program will ignore them, so they can be filled with anything (the program uses empty lines to make the distinction between ROMs). An exemple of usage is provided in "2rom.txt" which comes along "2rom.net" in the test file.

## Executing the program

- make build : compiles the program.
- ./netlist_simulator.bytes (-n number_of_step) (-rom rom_filename) filename : execute the simulator on the file filename, where number_of_step is an optional argument which indicates the number of times the netlist is to be simulated, and rom_filename specifies the file containing the ROMs if ROMs are used in the program.