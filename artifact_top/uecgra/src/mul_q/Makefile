default: simv-mul

simv-mul: mul.t.v mul.v
	vcs -full64 -sverilog -debug_pp mul.t.v -f flist.vcs -o $@;
	./$@

waveform:
	dve -full64 -vpd vcdplus.vpd &

clean:
	rm -rf simv csrc *.daidir ucli.key simv-* DVEfiles *.vpd
