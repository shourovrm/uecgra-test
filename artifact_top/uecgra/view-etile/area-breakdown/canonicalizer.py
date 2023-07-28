import json

def main():
  with open("area_breakdown.json", "r") as fd:
    _area = json.load(fd)

  with open("tile_area.json", "w") as fd:
    area = {}
    area['mul'] = _area['mul']['abs_total']
    area['alu'] = _area['alu']['abs_total']
    area['acc_reg'] = _area['acc_reg']['abs_total']
    area['q_n'] = _area['in_q_n']['abs_total']
    area['q_s'] = _area['in_q_s']['abs_total']
    area['q_w'] = _area['in_q_w']['abs_total']
    area['q_e'] = _area['in_q_e']['abs_total']
    area['suppress'] = 0.0
    area['unsafe_gen'] = 0.0
    area['clk_switcher'] = 0.0
    area['other'] = _area['other']['abs_total']
    json.dump(area, fd, indent=2)

main()
