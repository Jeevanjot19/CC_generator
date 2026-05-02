import json
old = json.load(open('jumper_yamnet_events.json'))
new = json.load(open('jumper_yamnet_fixed2_events.json'))
print('BEFORE: Top 5 events by fusion score:')
for e in sorted(old, key=lambda x: x['fusion_score'], reverse=True)[:5]:
    print(f"  {e['t_start']:.1f}s: audio={e['audio_confidence']:.2f}, visual={e['reaction_score']:.2f}, fusion={e['fusion_score']:.2f}, decision={e['cc_decision']}")
print()
print('AFTER: Top 5 events by fusion score:')
for e in sorted(new, key=lambda x: x['fusion_score'], reverse=True)[:5]:
    print(f"  {e['t_start']:.1f}s: audio={e['audio_confidence']:.2f}, visual={e['reaction_score']:.2f}, fusion={e['fusion_score']:.2f}, decision={e['cc_decision']}")

print()
print("Issue: Reaction scores changed due to sigmoid fix. Let me show reaction_type too:")
print()
print('BEFORE accepted events:')
for e in old:
    if e['cc_decision']:
        print(f"  {e['t_start']:.1f}s: reaction_type={e.get('reaction_type')}, visual={e['reaction_score']:.2f}")

print()
print('AFTER accepted events:')
for e in new:
    if e['cc_decision']:
        print(f"  {e['t_start']:.1f}s: reaction_type={e.get('reaction_type')}, visual={e['reaction_score']:.2f}")
