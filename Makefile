simu:
	./script_compil_simu.sh

clean:
	rm -r simulation/_build
	rm -r _build
	rm -r __pycache__
	rm netlist_simulator.byte
	rm -f processeur.net 

proc:
	rm -f processeur.net 
	./file_proc/carotte.py -o processeur.net ./file_proc/processeur/processeur.py

all:
	make simu
	make proc