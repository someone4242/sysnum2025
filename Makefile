simu:
	ocamlbuild simulation/netlist_simulator.byte

processeur.net:
	rm -f processeur.net && ./charles/carotte/carotte.py ./charles/carotte/processeur/processeur.py |> processeur.net

run: processeur.net simulation/netlist_simulator.byte
	rm -f processeur.net &&	./charles/carotte/carotte.py ./charles/carotte/processeur/processeur.py |> processeur.net && simulation/netlist_simulator.byte -rom program.txt processeur.net 