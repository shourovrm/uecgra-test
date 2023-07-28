# !/bin/sh

for pro_clk in "nominal" "fast" "slow"
do
  for body_clk in "nominal" "fast" "slow"
  do
    for epi_clk in "nominal" "fast" "slow"
    do
      python $RGALS_TOP/benchmark-synthetic/series-parallel/series-parallel-gen.py \
        --prologue 3 --body 5 --epilogue 3 \
        --prologue_clk $pro_clk --body_clk $body_clk --epilogue_clk $epi_clk
    done
  done
done
