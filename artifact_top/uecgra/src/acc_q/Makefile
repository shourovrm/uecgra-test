default: simv-accum

simv-accum: accum.t.v accum.v
	vcs -full64 -sverilog -debug_pp accum.t.v -f flist.vcs -o $@;
	./$@

clean:
	rm -rf simv csrc *.daidir ucli.key simv-* DVEfiles *.vpd

waveform:
	dve -full64 -vpd vcdplus.vpd &
