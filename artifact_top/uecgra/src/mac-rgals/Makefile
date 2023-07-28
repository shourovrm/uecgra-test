default: simv-mac

simv-mac: mac-rgals.t.v mac-rgals.v
	vcs -full64 -sverilog -debug_pp mac-rgals.t.v -f flist.vcs -o $@;
	./$@

pymtl-import:
	python mac_rgals.py

clean:
	rm -rf simv csrc *.daidir ucli.key simv-* DVEfiles *.vpd
	rm -rf mac_rgals_w_params*.* obj_dir_mac_rgals_w_params libmac_rgals_w_params_v.so

waveform:
	dve -full64 -vpd vcdplus.vpd &
