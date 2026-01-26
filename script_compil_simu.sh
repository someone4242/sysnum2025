cd simulation
ocamlbuild netlist_simulator.byte
cd ..
cp simulation/netlist_simulator.byte netlist_simulator.byte
rm simulation/netlist_simulator.byte