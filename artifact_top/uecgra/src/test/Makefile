default: simv-source simv-sink simv-test

simv-source: Source.t.v Source.v
	vcs -full64 -sverilog -debug_pp Source.t.v -v Source.v -o $@

simv-sink: Sink.t.v Sink.v
	vcs -full64 -sverilog -debug_pp Sink.t.v -v Sink.v -o $@

simv-test: Test.t.v Source.v Sink.v
	vcs -full64 -sverilog -debug_pp Test.t.v -v Source.v -v Sink.v -o $@

clean:
	rm -rf simv csrc *.daidir ucli.key simv-* DVEfiles *.vpd

