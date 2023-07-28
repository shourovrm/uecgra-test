default: simv-fifo

simv-fifo: BisynchronousNormalQueue.t.v BisynchronousNormalQueue.v
	vcs -full64 -sverilog -debug_pp BisynchronousNormalQueue.t.v -v BisynchronousNormalQueue.v -v ../clock/ClockDivider.v -v ../test/Source.v -v ../test/Sink.v -o $@

clean:
	rm -rf simv csrc *.daidir ucli.key simv-* DVEfiles *.vpd

