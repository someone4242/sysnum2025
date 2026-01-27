simu:
	./script_compil_simu.sh

clean:
	-rm -r simulation/_build
	-rm -r _build
	-rm -r __pycache__
	-rm netlist_simulator.byte
	-rm -f processeur.net 

proc:
	-rm -f processeur.net 
	./file_proc/carotte.py -o processeur.net ./file_proc/processeur/processeur.py

all:
	make simu
	make proc

clock:
	make all
	python3 compilation.py -o clock/horloge_rdtime.txt clock/horloge_rdtime.sus
	./netlist_simulator.byte -rom clock/horloge_rdtime.txt processeur.net

clockff:
	make all
	python3 compilation.py -o clock/horloge_ff.txt clock/horloge_ff.sus
	./netlist_simulator.byte -rom clock/horloge_ff.txt processeur.net