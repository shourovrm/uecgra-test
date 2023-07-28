RISC-V Processor Experiments
============================

Run a benchmark
---------------
First of all make sure you clone pymtl-v3 repo and pymtl-v3-designs repo
in the same parent directory:

```text
work/
  pymtl-v3/
  pymtl-v3-designs/
```

For convenience, I have built the mtbmark-matmul binaries with four
different sizes of datasets:

```text
- mtbmark-matmul-small:  single core runs for        80,000 cycles
- mtbmark-matmul-medium: single core runs for    10,000,000 cycles
- mtbmark-matmul-big:    single core runs for   500,000,000 cycles
- mtbmark-matmul-huge:   single core runs for 2,300,000,000 cycles
```

I have also parameterized the benchmark to seamlessly switch between
different number of cores. As a result, "mcore-sim-elf" can run single
core benchmark as well.

Note that the work region is embarrassingly
parallel so with e.g. four cores, the total amount of cycle executed will
be roughly 1/4 of the number above.

```text
 $ cd pymtl-v3-designs/proc_dac
 $ ./mcore-sim-elf mtbmark-matmul-medium --ncores N (--stats --trace)

 N \in {1,2,4,8,16}
```

To force using Python Bits in PyPy environment:

```text
 $ PYMTL_BITS=1 ./mcore-sim-elf ...
```

Hack Mamba
----------
Right now all the simulation related passes are those who generate the
tick, and do the schedule.

This is how I schedule update blocks using a priority queue:
https://github.com/cornell-brg/pymtl-v3/blob/master/pymtl/passes/ScheduleUpblkPass.py#L44-L59

This is where the tick is generated. By default it is 'unroll':
https://github.com/cornell-brg/pymtl-v3/blob/master/pymtl/passes/GenerateTickPass.py#L41-L52
