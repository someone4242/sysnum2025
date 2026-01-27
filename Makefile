simu:
	./script_compil_simu.sh

clean:
	-rm -rf simulation/_build
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
	python3 compilation.py -o clocks/horloge_rdtime.txt clocks/horloge_rdtime.sus
	./netlist_simulator.byte -rom clocks/horloge_rdtime.txt processeur.net

clockff:
	make all
	python3 compilation.py -o clocks/horloge_ff.txt clocks/horloge_ff.sus
	./netlist_simulator.byte -rom clocks/horloge_ff.txt processeur.net
