default: simv-ClockDivider

simv-ClockDivider: ClockDivider.t.v ClockDivider.v
	vcs -full64 -sverilog -debug_pp ClockDivider.t.v -v ClockDivider.v -o $@

clean:
	rm -rf simv csrc *.daidir ucli.key simv-* DVEfiles *.vpd

