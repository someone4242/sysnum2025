simulation/netlist_simulator.byte:
	cd simulation && make build && cd ..

simulation/processeur.net:
	cd charles/carotte && \
	rm -f ../../simulation/processeur.net && \ 
	./carotte.py processeur/processeur.py |> ../../simulation/processeur.net && \ 
	cd ../..

run: simulation/processeur.net simulation/netlist_simulator.byte
	cd simulation && \
	./netlist_simulator.byte -rom program.txt processeur.net 