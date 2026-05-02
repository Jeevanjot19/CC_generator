import json

print("=" * 80)
print("COMPARISON: YAMNet BEFORE vs AFTER FIXES")
print("=" * 80)

# Load old results
with open('jumper_yamnet_events.json') as f:
    old = json.load(f)

# Load new results  
with open('jumper_yamnet_fixed_events.json') as f:
    new = json.load(f)

print(f"\nBEFORE FIXES:")
print(f"  Total candidates: {len(old)}")
print(f"  Time range: {min(e['t_start'] for e in old):.1f}s - {max(e['t_end'] for e in old):.1f}s")
print(f"  Accepted: {sum(1 for e in old if e['cc_decision'])}")

print(f"\nAFTER FIXES:")
print(f"  Total candidates: {len(new)}")
print(f"  Time range: {min(e['t_start'] for e in new):.1f}s - {max(e['t_end'] for e in new):.1f}s")
print(f"  Accepted: {sum(1 for e in new if e['cc_decision'])}")

print("\n" + "=" * 80)
print("FIX #1: YAMNet Timestamps")
print("=" * 80)
old_max = max(e['t_end'] for e in old)
new_max = max(e['t_end'] for e in new)
print(f"Old max timestamp: {old_max:.1f}s (was capped at ~22s)")
print(f"New max timestamp: {new_max:.1f}s (now spans full video)")
print(f"✅ Fixed!" if new_max > 100 else "❌ Still capped")

print("\n" + "=" * 80)
print("FIX #2: Reaction Score Saturation")
print("=" * 80)
old_scores = [e['reaction_score'] for e in old if e['cc_decision']]
new_scores = [e['reaction_score'] for e in new if e['cc_decision']]
print(f"Old reaction_scores (accepted): {old_scores}")
print(f"New reaction_scores (accepted): {new_scores}")
print(f"✅ No more ceiling at 1.0" if all(s < 1.0 for s in new_scores) else "❌ Still has 1.0 scores")

print("\n" + "=" * 80)
print("FIX #3: Long Caption Splitting")
print("=" * 80)
old_durations = [e['t_end'] - e['t_start'] for e in old if e['cc_decision']]
new_durations = [e['t_end'] - e['t_start'] for e in new if e['cc_decision']]
print(f"Old caption durations: {[f'{d:.1f}s' for d in old_durations]}")
print(f"New caption durations: {[f'{d:.1f}s' for d in new_durations]}")
print(f"✅ All captions ≤3s" if all(d <= 3.0 for d in new_durations) else "❌ Still has long captions")

print("\n" + "=" * 80)
print("FIX #4: YAMNet Label Taxonomy")
print("=" * 80)
new_labels = [e['cc_label'] for e in new if e['cc_decision']]
print(f"New labels: {new_labels}")
print(f"✅ Has specific labels" if any('[' in l and l != '[Sound effect]' for l in new_labels) else "Still generic [Sound effect]")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Candidates increased: {len(old)} → {len(new)} (+{len(new)-len(old)})")
print(f"Time coverage: {old_max:.1f}s → {new_max:.1f}s")
