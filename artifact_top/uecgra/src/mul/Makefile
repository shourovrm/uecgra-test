default: simv-mul

simv-mul: mul.t.v mul.v
	vcs -full64 -sverilog -debug_pp mul.t.v -v mul.v -v ../test/Source.v -v ../test/Sink.v -o $@

clean:
	rm -rf simv csrc *.daidir ucli.key simv-* DVEfiles *.vpd

