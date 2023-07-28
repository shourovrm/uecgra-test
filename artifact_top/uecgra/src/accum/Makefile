default: simv-accum

simv-accum: accum.t.v accum.v
	vcs -full64 -sverilog -debug_pp accum.t.v -v accum.v -v ../test/Source.v -v ../test/Sink.v -o $@

clean:
	rm -rf simv csrc *.daidir ucli.key simv-* DVEfiles *.vpd

