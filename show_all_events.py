import json
old = json.load(open('jumper_yamnet_events.json'))
new = json.load(open('jumper_yamnet_fixed2_events.json'))
print(f'BEFORE: {len(old)} total candidates, {sum(1 for e in old if e["cc_decision"])} accepted')
print(f'AFTER: {len(new)} total candidates, {sum(1 for e in new if e["cc_decision"])} accepted')
print()
print('All events in AFTER:')
for e in new:
    print(f"  {e['t_start']:.1f}-{e['t_end']:.1f}s: {e['audio_class']}, audio={e['audio_confidence']:.2f}, visual={e['reaction_score']:.2f}, fusion={e['fusion_score']:.2f}, accept={e['cc_decision']}")
