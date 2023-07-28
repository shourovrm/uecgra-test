import json

def main():
  with open("area_breakdown.json", "r") as fd:
    _area = json.load(fd)

  with open("tile_area.json", "w") as fd:
    area = {}
    area['mul'] = _area['mul']['abs_total']
    area['alu'] = _area['alu']['abs_total']
    area['acc_reg'] = _area['acc_reg']['abs_total']
    area['q_n'] = _area['in_qs__0']['abs_total']
    area['q_s'] = _area['in_qs__1']['abs_total']
    area['q_w'] = _area['in_qs__2']['abs_total']
    area['q_e'] = _area['in_qs__3']['abs_total']
    area['suppress'] = _area['suppressors__0']['abs_total'] + \
                       _area['suppressors__1']['abs_total'] + \
                       _area['suppressors__2']['abs_total'] + \
                       _area['suppressors__3']['abs_total']
    area['unsafe_gen'] = _area['unsafe_gen']['abs_total']
    area['clk_switcher'] = _area['clk_switcher']['abs_total']
    area['other'] = _area['other']['abs_total']
    json.dump(area, fd, indent=2)

main()
