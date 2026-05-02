import json
data = json.load(open('jumper_heuristic_events.json'))
long = [e for e in data if e['cc_decision'] and (e['t_end']-e['t_start']) > 3]
print(f'Long captions (>3s): {len(long)}')
for e in long:
    duration = e['t_end'] - e['t_start']
    print(f"{e['t_start']:.1f}-{e['t_end']:.1f} ({duration:.1f}s): {e['cc_label']}")
