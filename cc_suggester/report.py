from __future__ import annotations

from html import escape
from pathlib import Path
from typing import NamedTuple, Optional

from .event import Event
from .output import format_srt_timestamp


class ReportMetrics(NamedTuple):
    """Optional metrics to display in HTML report."""
    total_time: float = 0.0
    audio_detection_time: float = 0.0
    visual_detection_time: float = 0.0
    fusion_time: float = 0.0
    num_audio_candidates: int = 0
    num_accepted: int = 0
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    overcaption_rate: Optional[float] = None


def _pct(value: float) -> str:
    return f"{value * 100:.0f}%"


def _decision_badge(event: Event) -> str:
    if event.cc_decision:
        return '<span class="badge accepted">Accepted</span>'
    return '<span class="badge rejected">Rejected</span>'


def render_html_report(
    events: list[Event], 
    input_path: Path, 
    output_path: Path,
    metrics: Optional[ReportMetrics] = None
) -> str:
    accepted = sum(1 for event in events if event.cc_decision)
    rejected = len(events) - accepted
    rows = []
    for event in events:
        notes = ", ".join(event.notes or [])
        rows.append(
            "<tr>"
            f"<td>{escape(format_srt_timestamp(event.t_start))}</td>"
            f"<td>{escape(format_srt_timestamp(event.t_end))}</td>"
            f"<td>{escape(event.cc_label or '[Sound effect]')}</td>"
            f"<td>{escape(_pct(event.audio_confidence))}</td>"
            f"<td>{escape(_pct(event.reaction_score))}</td>"
            f"<td>{escape(_pct(event.fusion_score))}</td>"
            f"<td>{_decision_badge(event)}</td>"
            f"<td>{escape(notes)}</td>"
            "</tr>"
        )

    table_body = "\n".join(rows) or (
        '<tr><td colspan="8" class="empty">No audio candidates were detected.</td></tr>'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Intelligent CC Suggestion Report</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #172026;
      --muted: #5e6b73;
      --line: #d8e0e5;
      --paper: #ffffff;
      --bg: #f5f7f8;
      --accent: #1b6b68;
      --accepted: #176b3a;
      --accepted-bg: #e8f5ed;
      --rejected: #8a3d18;
      --rejected-bg: #fff1e8;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--bg);
    }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      gap: 24px;
      align-items: flex-end;
      border-bottom: 1px solid var(--line);
      padding-bottom: 20px;
      margin-bottom: 24px;
    }}
    h1 {{
      font-size: 28px;
      line-height: 1.2;
      margin: 0 0 8px;
      letter-spacing: 0;
    }}
    p {{
      margin: 0;
      color: var(--muted);
      line-height: 1.5;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(3, minmax(120px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }}
    .stat {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .stat strong {{
      display: block;
      font-size: 26px;
      margin-bottom: 4px;
    }}
    .stat span {{
      color: var(--muted);
      font-size: 13px;
    }}
    .metrics-panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 20px;
      margin-bottom: 24px;
    }}
    .metrics-panel h2 {{
      margin: 0 0 16px 0;
      font-size: 16px;
      color: var(--ink);
    }}
    .metrics-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
      gap: 12px;
    }}
    .metric-item {{
      background: #f9fafb;
      border: 1px solid #e5e7eb;
      border-radius: 6px;
      padding: 12px;
      text-align: center;
    }}
    .metric-label {{
      display: block;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 6px;
      text-transform: uppercase;
    }}
    .metric-value {{
      display: block;
      font-size: 18px;
      font-weight: bold;
      color: var(--accent);
    }}
    .panel {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 12px 14px;
      vertical-align: top;
    }}
    th {{
      background: #edf3f3;
      color: #27363d;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    .badge {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 12px;
      font-weight: 700;
    }}
    .accepted {{
      color: var(--accepted);
      background: var(--accepted-bg);
    }}
    .rejected {{
      color: var(--rejected);
      background: var(--rejected-bg);
    }}
    .empty {{
      color: var(--muted);
      text-align: center;
      padding: 28px;
    }}
    code {{
      color: var(--accent);
      overflow-wrap: anywhere;
    }}
    @media (max-width: 760px) {{
      header {{ display: block; }}
      .stats {{ grid-template-columns: 1fr; }}
      .panel {{ overflow-x: auto; }}
      table {{ min-width: 760px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Intelligent CC Suggestion Report</h1>
        <p>Input: <code>{escape(str(input_path))}</code></p>
      </div>
      <p>Output: <code>{escape(str(output_path))}</code></p>
    </header>
    <section class="stats" aria-label="Summary">
      <div class="stat"><strong>{len(events)}</strong><span>Audio candidates</span></div>
      <div class="stat"><strong>{accepted}</strong><span>Accepted captions</span></div>
      <div class="stat"><strong>{rejected}</strong><span>Rejected events</span></div>
    </section>
    {f'''<section class="metrics-panel">
      <h2>Performance Metrics</h2>
      <div class="metrics-grid">
        <div class="metric-item">
          <span class="metric-label">Total Time</span>
          <span class="metric-value">{metrics.total_time:.3f}s</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Audio Detection</span>
          <span class="metric-value">{metrics.audio_detection_time:.3f}s</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Visual Scoring</span>
          <span class="metric-value">{metrics.visual_detection_time:.3f}s</span>
        </div>
        <div class="metric-item">
          <span class="metric-label">Fusion Logic</span>
          <span class="metric-value">{metrics.fusion_time:.3f}s</span>
        </div>
        {f'<div class="metric-item"><span class="metric-label">Precision</span><span class="metric-value">{_pct(metrics.precision)}</span></div>' if metrics.precision is not None else ''}
        {f'<div class="metric-item"><span class="metric-label">Recall</span><span class="metric-value">{_pct(metrics.recall)}</span></div>' if metrics.recall is not None else ''}
        {f'<div class="metric-item"><span class="metric-label">F1 Score</span><span class="metric-value">{metrics.f1_score:.3f}</span></div>' if metrics.f1_score is not None else ''}
        {f'<div class="metric-item"><span class="metric-label">False Positive Rate</span><span class="metric-value">{_pct(metrics.overcaption_rate)}</span></div>' if metrics.overcaption_rate is not None else ''}
      </div>
    </section>''' if metrics else ''}
    <section class="panel">
      <table>
        <thead>
          <tr>
            <th>Start</th>
            <th>End</th>
            <th>Label</th>
            <th>Audio</th>
            <th>Reaction</th>
            <th>Fusion</th>
            <th>Decision</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody>
          {table_body}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def write_html_report(
    events: list[Event], 
    input_path: Path, 
    output_path: Path, 
    report_path: Path,
    metrics: Optional[ReportMetrics] = None
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_html_report(events, input_path, output_path, metrics),
        encoding="utf-8",
    )
