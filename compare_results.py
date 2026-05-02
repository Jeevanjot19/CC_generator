import json
data = json.load(open('test_yamnet_events.json'))
print("=== YAMNET RESULTS ===")
for e in data:
    print(f"  Time: {e['t_start']:.2f}s-{e['t_end']:.2f}s")
    print(f"  Class: {e['audio_class']}")
    print(f"  Confidence: {e['audio_confidence']:.2f}")
    print(f"  Label: {e['cc_label']}")
    print()

print("=== HEURISTIC RESULTS (for comparison) ===")
data = json.load(open('test_heuristic_events.json'))
for e in data:
    print(f"  Time: {e['t_start']:.2f}s-{e['t_end']:.2f}s")
    print(f"  Class: {e['audio_class']}")
    print(f"  Confidence: {e['audio_confidence']:.2f}")
    print()
