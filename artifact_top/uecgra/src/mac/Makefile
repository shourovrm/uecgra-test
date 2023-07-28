default: simv-mac

simv-mac: mac.t.v mac.v
	vcs -full64 -sverilog -debug_pp mac.t.v -v mac.v -v ../mul/mul.v -v ../accum/accum.v -v ../test/Source.v -v ../test/Sink.v -o $@

clean:
	rm -rf simv csrc *.daidir ucli.key simv-* DVEfiles *.vpd

