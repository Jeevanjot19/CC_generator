import json

print("=" * 70)
print("HEURISTIC BACKEND RESULTS")
print("=" * 70)
with open('jumper_heuristic_events.json') as f:
    heur_events = json.load(f)

accepted = [e for e in heur_events if e['cc_decision']]
print(f"\n✓ ACCEPTED ({len(accepted)} events):")
for e in accepted:
    print(f"  {e['t_start']:.1f}s - {e['t_end']:.1f}s: {e['cc_label']} (confidence: {e['audio_confidence']:.2f})")

print(f"\n✗ REJECTED (samples, {len(heur_events) - len(accepted)} total):")
for e in heur_events[:3]:
    if not e['cc_decision']:
        print(f"  {e['t_start']:.1f}s - {e['t_end']:.1f}s: {e['audio_class']} (audio: {e['audio_confidence']:.2f}, visual: {e['reaction_score']:.2f}, fusion: {e['fusion_score']:.2f})")

print("\n" + "=" * 70)
print("YAMNET BACKEND RESULTS (Rich Audio Classification)")
print("=" * 70)
with open('jumper_yamnet_events.json') as f:
    yamnet_events = json.load(f)

accepted = [e for e in yamnet_events if e['cc_decision']]
print(f"\n✓ ACCEPTED ({len(accepted)} events):")
for e in accepted:
    print(f"  {e['t_start']:.1f}s - {e['t_end']:.1f}s: {e['cc_label']} (class: {e['audio_class']}, confidence: {e['audio_confidence']:.2f})")

print(f"\n✗ REJECTED (samples, {len(yamnet_events) - len(accepted)} total):")
count = 0
for e in yamnet_events:
    if not e['cc_decision'] and count < 5:
        print(f"  {e['t_start']:.1f}s - {e['t_end']:.1f}s: {e['audio_class']} (confidence: {e['audio_confidence']:.2f})")
        count += 1

print("\n" + "=" * 70)
print("KEY DIFFERENCES")
print("=" * 70)
print(f"Heuristic: 27 candidates → 4 accepted | YAMNet: 20 candidates → 2 accepted")
print(f"Both use same visual scoring (OpenCV motion detection)")
print(f"YAMNet uses 500+ audio classes vs Heuristic's 3 generic labels")
print(f"YAMNet timestamps fixed with manual calculation (no result.timestamp_ms)")
