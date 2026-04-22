#!/usr/bin/env python3
"""
Rebuild index.html from pipeline outputs (stage_level_summary.csv,
correlation_matrix.csv, stage_au_aum_correlations.csv, descriptive_statistics.csv,
analysis_dataset_enriched.csv).

Run after survey_phase3_analysis.py:
  python3 generate_survey_dashboard.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DIR = Path(__file__).resolve().parent


def load_bundle() -> dict:
    stage = pd.read_csv(DIR / "stage_level_summary.csv")
    corr = pd.read_csv(DIR / "correlation_matrix.csv", index_col=0)
    stage_r = pd.read_csv(DIR / "stage_au_aum_correlations.csv")
    desc = pd.read_csv(DIR / "descriptive_statistics.csv")
    enriched = pd.read_csv(DIR / "analysis_dataset_enriched.csv")

    stages_key = stage["Stage"].tolist()
    au_m = [round(float(stage.loc[stage["Stage"] == s, "AU_mean"].iloc[0]), 3) for s in stages_key]
    au_sd = [round(float(stage.loc[stage["Stage"] == s, "AU_sd"].iloc[0]), 3) for s in stages_key]
    aum_m = [round(float(stage.loc[stage["Stage"] == s, "AUM_mean"].iloc[0]), 3) for s in stages_key]
    aum_sd = [round(float(stage.loc[stage["Stage"] == s, "AUM_sd"].iloc[0]), 3) for s in stages_key]

    scorr = [
        round(float(stage_r.loc[stage_r["Stage"] == s, "corr"].iloc[0]), 3) for s in stages_key
    ]

    labels = list(corr.index)
    corr_mat = [[round(float(corr.loc[li, lj]), 3) for lj in labels] for li in labels]

    x = enriched["AU_overall"].values.astype(float)
    y = enriched["AUM_overall"].values.astype(float)
    coef = np.polyfit(x, y, 1)
    xline = np.array([float(np.min(x)), float(np.max(x))], dtype=float)
    yline = coef[0] * xline + coef[1]
    points = [{"x": float(a), "y": float(b)} for a, b in zip(x, y)]
    line_pts = [{"x": float(xline[0]), "y": float(yline[0])}, {"x": float(xline[1]), "y": float(yline[1])}]

    def dmean(name: str) -> float:
        return float(desc.loc[desc["Variable"] == name, "Mean"].iloc[0])

    au_o, aum_o, lit, fc = map(dmean, ["AU_overall", "AUM_overall", "AI_Literacy", "Facilitating_Conditions"])

    cap = {
        "plan": "Plan",
        "design": "Design",
        "implementation": "Implementation",
        "testing": "Testing",
        "deployment": "Deployment",
        "maintenance": "Maintenance",
    }
    table_rows = ""
    for _, r in stage.iterrows():
        table_rows += (
            f"<tr><td>{cap[r['Stage']]}</td>"
            f"<td>{r['AU_mean']:.3f}</td><td>{r['AU_sd']:.3f}</td>"
            f"<td>{r['AUM_mean']:.3f}</td><td>{r['AUM_sd']:.3f}</td></tr>\n"
        )

    overall_r = round(float(corr.loc["AU_overall", "AUM_overall"]), 3)
    weak_stage = str(stage_r.sort_values("corr").iloc[0]["Stage"])
    strong_stage = str(stage_r.sort_values("corr").iloc[-1]["Stage"])

    return {
        "stages_display": ["Plan", "Design", "Implementation", "Testing", "Deployment", "Maintenance"],
        "auMeans": au_m,
        "auSD": au_sd,
        "aumMeans": aum_m,
        "aumSD": aum_sd,
        "stageCorr": scorr,
        "relationshipPoints": points,
        "relationshipLine": line_pts,
        "corrLabels": labels,
        "corrData": corr_mat,
        "distMeans": [round(au_o, 3), round(aum_o, 3), round(lit, 3), round(fc, 3)],
        "overall_r": overall_r,
        "table_rows": table_rows,
        "n": len(enriched),
        "au_overall_mean": round(au_o, 3),
        "aum_overall_mean": round(aum_o, 3),
        "weak_stage": weak_stage,
        "strong_stage": strong_stage,
        "corr_peou_pu": round(float(corr.loc["PEOU_plan", "PU_plan"]), 3),
        "corr_pu_bi": round(float(corr.loc["PU_plan", "BI_plan"]), 3),
        "corr_pu_au": round(float(corr.loc["PU_plan", "AU_plan"]), 3),
        "corr_bi_au": round(float(corr.loc["BI_plan", "AU_plan"]), 3),
        "corr_lit_au": round(float(corr.loc["AI_Literacy", "AU_overall"]), 3),
        "corr_lit_aum": round(float(corr.loc["AI_Literacy", "AUM_overall"]), 3),
    }


def main() -> int:
    b = load_bundle()
    data_json = json.dumps(
        {
            "stages": b["stages_display"],
            "auMeans": b["auMeans"],
            "auSD": b["auSD"],
            "aumMeans": b["aumMeans"],
            "aumSD": b["aumSD"],
            "stageCorr": b["stageCorr"],
            "relationshipPoints": b["relationshipPoints"],
            "relationshipLine": b["relationshipLine"],
            "corrLabels": b["corrLabels"],
            "corrData": b["corrData"],
            "distMeans": b["distMeans"],
            "overall_r": b["overall_r"],
        }
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Survey Analysis Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {{
      --bg: #f8fafc;
      --card: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --border: #e2e8f0;
      --accent: #2563eb;
      --accent-soft: #dbeafe;
      --accent-2: #7c3aed;
      --accent-3: #0f766e;
      --accent-4: #dc2626;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.55;
    }}
    .container {{
      max-width: 1200px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .hero {{
      background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.06);
    }}
    h1, h2, h3 {{ margin: 0 0 12px; }}
    h1 {{ font-size: 2.2rem; }}
    h2 {{ font-size: 1.4rem; margin-bottom: 16px; }}
    p {{ margin: 0 0 14px; color: var(--muted); }}
    .grid {{
      display: grid;
      gap: 20px;
      margin-top: 24px;
    }}
    .grid-2 {{ grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }}
    .grid-3 {{ grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
    }}
    .metric {{
      font-size: 2rem;
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 4px;
    }}
    .metric-label {{
      color: var(--muted);
      font-size: 0.95rem;
    }}
    .section {{ margin-top: 28px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }}
    th, td {{
      text-align: left;
      padding: 12px 10px;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    th {{
      background: #f8fafc;
      color: #0f172a;
      font-weight: 700;
    }}
    .table-wrap {{ overflow-x: auto; }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 0.85rem;
      font-weight: 600;
      margin-bottom: 10px;
    }}
    figure {{ margin: 0; }}
    figcaption {{
      margin-top: 10px;
      font-size: 0.92rem;
      color: var(--muted);
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      color: var(--muted);
    }}
    .small {{ font-size: 0.92rem; color: var(--muted); }}
    .chart-wrap {{
      position: relative;
      min-height: 320px;
    }}
    .chart-wrap.tall {{
      min-height: 420px;
    }}
    canvas {{
      width: 100% !important;
      height: 100% !important;
    }}
    .matrix {{
      display: grid;
      grid-template-columns: 180px repeat(8, minmax(68px, 1fr));
      gap: 6px;
      align-items: stretch;
      font-size: 0.82rem;
      overflow-x: auto;
    }}
    .matrix .cell,
    .matrix .head {{
      border-radius: 10px;
      padding: 10px 8px;
      text-align: center;
      border: 1px solid var(--border);
      background: white;
    }}
    .matrix .head {{
      font-weight: 700;
      color: var(--text);
      position: sticky;
      left: 0;
      z-index: 1;
    }}
    .matrix .rowhead {{
      text-align: left;
      font-weight: 700;
      position: sticky;
      left: 0;
      background: white;
      z-index: 1;
    }}
    .static-fig img {{ max-width: 100%; height: auto; border-radius: 12px; border: 1px solid var(--border); }}
  </style>
</head>
<body>
  <div class="container">
    <section class="hero">
      <span class="badge">Stage-Aware TAM + AUM Dashboard</span>
      <h1>Generative AI Usage in Software Engineering Education</h1>
      <p>This dashboard summarizes results from the UCSC survey on generative AI usage across the software development lifecycle (SDLC). Values are synced from <code>analysis_dataset_enriched.csv</code>, Phase 3 CSVs in this folder, and static figures in <code>assets/</code>.</p>
      <div class="grid grid-3">
        <div class="card">
          <div class="metric">{b["n"]}</div>
          <div class="metric-label">Valid responses</div>
        </div>
        <div class="card">
          <div class="metric">{b["au_overall_mean"]}</div>
          <div class="metric-label">Overall AI Usage (AU mean)</div>
        </div>
        <div class="card">
          <div class="metric">{b["aum_overall_mean"]}</div>
          <div class="metric-label">Overall AI Usage Maturity (AUM mean)</div>
        </div>
      </div>
    </section>

    <section class="section grid grid-2">
      <div class="card">
        <h2>Key Findings</h2>
        <ul>
          <li>Mean AU is highest in <strong>design</strong>; <strong>implementation</strong> is very close.</li>
          <li>Mean AUM peaks in <strong>implementation</strong>.</li>
          <li>Overall AU and AUM correlate at <strong>r = {b["overall_r"]}</strong>.</li>
          <li><strong>Deployment</strong> and <strong>maintenance</strong> show the lowest mean AU and AUM.</li>
          <li>Within-stage AU–AUM correlation is weakest in <strong>{b["weak_stage"]}</strong> and among the strongest in <strong>{b["strong_stage"]}</strong>.</li>
        </ul>
      </div>
      <div class="card">
        <h2>Interpretive Summary</h2>
        <p>Students do not use AI uniformly across the SDLC. Usage and maturity track each other overall, but stage-level correlations show that <em>how much</em> students use AI at a stage and <em>how mature</em> that use is can diverge—especially where within-stage AU–AUM correlation is lower.</p>
        <p>Open the generated PNGs in <code>assets/</code> for publication-ready static figures (same pipeline as the charts below).</p>
      </div>
    </section>

    <section class="section card">
      <h2>Table 1. Stage-Level Summary</h2>
      <p class="small">Source: <code>stage_level_summary.csv</code></p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Stage</th>
              <th>AU Mean</th>
              <th>AU SD</th>
              <th>AUM Mean</th>
              <th>AUM SD</th>
            </tr>
          </thead>
          <tbody>
{b["table_rows"]}          </tbody>
        </table>
      </div>
    </section>

    <section class="section grid grid-2">
      <div class="card">
        <figure>
          <div class="chart-wrap"><canvas id="usageChart"></canvas></div>
          <figcaption><strong>Figure 1.</strong> Mean AI Usage (AU) across SDLC stages.</figcaption>
        </figure>
      </div>
      <div class="card">
        <figure>
          <div class="chart-wrap"><canvas id="aumChart"></canvas></div>
          <figcaption><strong>Figure 2.</strong> Mean AI Usage Maturity (AUM) across SDLC stages.</figcaption>
        </figure>
      </div>
    </section>

    <section class="section card">
      <figure>
        <div class="chart-wrap"><canvas id="lineChart"></canvas></div>
        <figcaption><strong>Figure 3.</strong> AU and AUM mean trajectories across stages.</figcaption>
      </figure>
    </section>

    <section class="section grid grid-2">
      <div class="card">
        <figure>
          <div class="chart-wrap"><canvas id="overallRelationshipChart"></canvas></div>
          <figcaption><strong>Figure 4.</strong> Respondent-level AU_overall vs AUM_overall (N = {b["n"]}). Red line: OLS fit.</figcaption>
        </figure>
      </div>
      <div class="card">
        <figure>
          <div class="chart-wrap"><canvas id="stageCorrChart"></canvas></div>
          <figcaption><strong>Figure 5.</strong> Pearson correlation between AU and AUM within each stage. Source: <code>stage_au_aum_correlations.csv</code>.</figcaption>
        </figure>
      </div>
    </section>

    <section class="section grid grid-2">
      <div class="card static-fig">
        <h2>Pipeline figure (match paper)</h2>
        <p class="small">Same regression as Figure 4, exported from Python (<code>assets/au_vs_aum.png</code>).</p>
        <img src="assets/au_vs_aum.png" alt="AU overall vs AUM overall with regression line" />
      </div>
      <div class="card static-fig">
        <h2>Correlation heatmap (pipeline)</h2>
        <p class="small"><code>assets/correlation_heatmap.png</code></p>
        <img src="assets/correlation_heatmap.png" alt="Correlation heatmap" />
      </div>
    </section>

    <section class="section card">
      <h2>Table 2. Selected correlations</h2>
      <p class="small">Source: <code>correlation_matrix.csv</code> (planning-stage TAM and globals).</p>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Relationship</th>
              <th>r</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>PEOU_plan ↔ PU_plan</td><td>{b["corr_peou_pu"]}</td><td>Ease of use vs perceived usefulness.</td></tr>
            <tr><td>PU_plan ↔ BI_plan</td><td>{b["corr_pu_bi"]}</td><td>Usefulness vs behavioral intention.</td></tr>
            <tr><td>PU_plan ↔ AU_plan</td><td>{b["corr_pu_au"]}</td><td>Usefulness vs actual use (planning).</td></tr>
            <tr><td>BI_plan ↔ AU_plan</td><td>{b["corr_bi_au"]}</td><td>Intention vs actual use (planning).</td></tr>
            <tr><td>AU_overall ↔ AUM_overall</td><td>{b["overall_r"]}</td><td>Overall usage vs maturity.</td></tr>
            <tr><td>AI_Literacy ↔ AU_overall</td><td>{b["corr_lit_au"]}</td><td>Literacy vs usage frequency.</td></tr>
            <tr><td>AI_Literacy ↔ AUM_overall</td><td>{b["corr_lit_aum"]}</td><td>Literacy vs maturity.</td></tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="section card">
      <h2>Figure 6. Correlation matrix (interactive)</h2>
      <p class="small">Same numeric values as <code>correlation_matrix.csv</code>.</p>
      <div id="corrMatrix" class="matrix"></div>
    </section>

    <section class="section grid grid-2">
      <div class="card">
        <h2>Global construct means</h2>
        <div class="chart-wrap"><canvas id="distributionSummaryChart"></canvas></div>
        <p class="small">AU_overall, AUM_overall, AI_Literacy, Facilitating_Conditions (from descriptive statistics).</p>
      </div>
      <div class="card">
        <h2>Stage variability (AU mean ±1 SD)</h2>
        <div class="chart-wrap tall"><canvas id="variabilityChart"></canvas></div>
        <p class="small">Bars: mean AU; whiskers drawn at ±1 SD per stage.</p>
      </div>
    </section>

    <section class="section card">
      <h2>Regenerate</h2>
      <p class="small">After updating CSVs, run: <code>python3 generate_survey_dashboard.py</code></p>
    </section>
  </div>

  <script id="dash-data" type="application/json">{data_json}</script>
  <script>
    const DASH = JSON.parse(document.getElementById('dash-data').textContent);
    const stages = DASH.stages;
    const auMeans = DASH.auMeans;
    const auSD = DASH.auSD;
    const aumMeans = DASH.aumMeans;
    const aumSD = DASH.aumSD;
    const stageCorr = DASH.stageCorr;
    const relationshipPoints = DASH.relationshipPoints;
    const relationshipLine = DASH.relationshipLine;
    const corrLabels = DASH.corrLabels;
    const corrData = DASH.corrData;
    const distMeans = DASH.distMeans;
    const overallR = DASH.overall_r;

    function cssVar(name) {{
      return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }}

    const commonOptions = {{
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {{
        legend: {{ labels: {{ color: cssVar('--text') }} }},
        tooltip: {{ enabled: true }}
      }},
      scales: {{
        x: {{ ticks: {{ color: cssVar('--muted') }}, grid: {{ display: false }} }},
        y: {{ ticks: {{ color: cssVar('--muted') }}, grid: {{ color: '#e2e8f0' }} }}
      }}
    }};

    const yminAu = Math.min(...auMeans) - 0.3;
    const ymaxAu = Math.max(...auMeans) + 0.3;
    const yminAum = Math.min(...aumMeans) - 0.3;
    const ymaxAum = Math.max(...aumMeans) + 0.3;

    new Chart(document.getElementById('usageChart'), {{
      type: 'bar',
      data: {{
        labels: stages,
        datasets: [{{
          label: 'Mean AU',
          data: auMeans,
          backgroundColor: 'rgba(37, 99, 235, 0.75)',
          borderRadius: 10
        }}]
      }},
      options: {{
        ...commonOptions,
        plugins: {{ ...commonOptions.plugins, legend: {{ display: false }} }},
        scales: {{ ...commonOptions.scales, y: {{ ...commonOptions.scales.y, min: yminAu, max: ymaxAu }} }}
      }}
    }});

    new Chart(document.getElementById('aumChart'), {{
      type: 'bar',
      data: {{
        labels: stages,
        datasets: [{{
          label: 'Mean AUM',
          data: aumMeans,
          backgroundColor: 'rgba(124, 58, 237, 0.75)',
          borderRadius: 10
        }}]
      }},
      options: {{
        ...commonOptions,
        plugins: {{ ...commonOptions.plugins, legend: {{ display: false }} }},
        scales: {{ ...commonOptions.scales, y: {{ ...commonOptions.scales.y, min: yminAum, max: ymaxAum }} }}
      }}
    }});

    new Chart(document.getElementById('lineChart'), {{
      type: 'line',
      data: {{
        labels: stages,
        datasets: [
          {{
            label: 'AU',
            data: auMeans,
            borderColor: 'rgba(37, 99, 235, 1)',
            backgroundColor: 'rgba(37, 99, 235, 0.12)',
            tension: 0.3,
            fill: false,
            pointRadius: 4
          }},
          {{
            label: 'AUM',
            data: aumMeans,
            borderColor: 'rgba(124, 58, 237, 1)',
            backgroundColor: 'rgba(124, 58, 237, 0.12)',
            tension: 0.3,
            fill: false,
            pointRadius: 4
          }}
        ]
      }},
      options: {{
        ...commonOptions,
        scales: {{
          ...commonOptions.scales,
          y: {{ ...commonOptions.scales.y, min: Math.min(yminAu, yminAum), max: Math.max(ymaxAu, ymaxAum) }}
        }}
      }}
    }});

    const xs = relationshipPoints.map(p => p.x);
    const ys = relationshipPoints.map(p => p.y);
    new Chart(document.getElementById('overallRelationshipChart'), {{
      type: 'scatter',
      data: {{
        datasets: [
          {{
            label: 'Respondents',
            data: relationshipPoints,
            pointBackgroundColor: 'rgba(15, 118, 110, 0.65)',
            pointRadius: 4
          }},
          {{
            label: 'OLS fit',
            data: relationshipLine,
            showLine: true,
            borderColor: 'rgba(220, 38, 38, 0.9)',
            borderWidth: 2,
            pointRadius: 0
          }}
        ]
      }},
      options: {{
        ...commonOptions,
        scales: {{
          x: {{
            min: Math.min(...xs) - 0.2,
            max: Math.max(...xs) + 0.2,
            ticks: {{ color: cssVar('--muted') }},
            grid: {{ color: '#e2e8f0' }},
            title: {{ display: true, text: 'AU_overall', color: cssVar('--muted') }}
          }},
          y: {{
            min: Math.min(...ys) - 0.2,
            max: Math.max(...ys) + 0.2,
            ticks: {{ color: cssVar('--muted') }},
            grid: {{ color: '#e2e8f0' }},
            title: {{ display: true, text: 'AUM_overall', color: cssVar('--muted') }}
          }}
        }}
      }}
    }});

    new Chart(document.getElementById('stageCorrChart'), {{
      type: 'bar',
      data: {{
        labels: stages,
        datasets: [{{
          label: 'AU–AUM correlation',
          data: stageCorr,
          backgroundColor: 'rgba(15, 118, 110, 0.75)',
          borderRadius: 10
        }}]
      }},
      options: {{
        ...commonOptions,
        plugins: {{ ...commonOptions.plugins, legend: {{ display: false }} }},
        scales: {{ ...commonOptions.scales, y: {{ ...commonOptions.scales.y, min: 0, max: 1 }} }}
      }}
    }});

    new Chart(document.getElementById('distributionSummaryChart'), {{
      type: 'bar',
      data: {{
        labels: ['AU_overall', 'AUM_overall', 'AI_Literacy', 'Facilitating_Conditions'],
        datasets: [{{
          label: 'Mean',
          data: distMeans,
          backgroundColor: [
            'rgba(37, 99, 235, 0.75)',
            'rgba(124, 58, 237, 0.75)',
            'rgba(15, 118, 110, 0.75)',
            'rgba(245, 158, 11, 0.75)'
          ],
          borderRadius: 10
        }}]
      }},
      options: {{
        ...commonOptions,
        plugins: {{ ...commonOptions.plugins, legend: {{ display: false }} }},
        scales: {{ ...commonOptions.scales, y: {{ ...commonOptions.scales.y, min: 0, max: 5 }} }}
      }}
    }});

    const variabilityPlugin = {{
      id: 'variabilityPlugin',
      afterDatasetsDraw(chart) {{
        const {{ ctx, scales: {{ x, y }} }} = chart;
        const meta = chart.getDatasetMeta(0);
        ctx.save();
        ctx.strokeStyle = 'rgba(71, 85, 105, 0.8)';
        ctx.lineWidth = 2;
        meta.data.forEach((bar, index) => {{
          const xPos = bar.x;
          const mean = auMeans[index];
          const sd = auSD[index];
          const top = y.getPixelForValue(mean + sd);
          const bottom = y.getPixelForValue(mean - sd);
          ctx.beginPath();
          ctx.moveTo(xPos, top);
          ctx.lineTo(xPos, bottom);
          ctx.stroke();
          ctx.beginPath();
          ctx.moveTo(xPos - 8, top);
          ctx.lineTo(xPos + 8, top);
          ctx.moveTo(xPos - 8, bottom);
          ctx.lineTo(xPos + 8, bottom);
          ctx.stroke();
        }});
        ctx.restore();
      }}
    }};

    new Chart(document.getElementById('variabilityChart'), {{
      type: 'bar',
      data: {{
        labels: stages,
        datasets: [{{
          label: 'AU mean',
          data: auMeans,
          backgroundColor: 'rgba(37, 99, 235, 0.7)',
          borderRadius: 10
        }}]
      }},
      options: {{
        ...commonOptions,
        plugins: {{ ...commonOptions.plugins, legend: {{ display: false }} }},
        scales: {{ ...commonOptions.scales, y: {{ ...commonOptions.scales.y, min: 0, max: 5 }} }}
      }},
      plugins: [variabilityPlugin]
    }});

    function corrColor(v) {{
      const alpha = Math.abs(v);
      if (v >= 0) return `rgba(37, 99, 235, ${{0.08 + alpha * 0.7}})`;
      return `rgba(220, 38, 38, ${{0.08 + alpha * 0.7}})`;
    }}

    const corrMatrixEl = document.getElementById('corrMatrix');
    corrMatrixEl.innerHTML = '';
    corrMatrixEl.appendChild(Object.assign(document.createElement('div'), {{ className: 'head', textContent: '' }}));
    corrLabels.forEach(label => {{
      corrMatrixEl.appendChild(Object.assign(document.createElement('div'), {{ className: 'head', textContent: label }}));
    }});
    corrData.forEach((row, i) => {{
      corrMatrixEl.appendChild(Object.assign(document.createElement('div'), {{ className: 'cell rowhead', textContent: corrLabels[i] }}));
      row.forEach(value => {{
        const div = document.createElement('div');
        div.className = 'cell';
        div.textContent = value.toFixed(2);
        div.style.background = corrColor(value);
        div.style.color = Math.abs(value) > 0.55 ? 'white' : cssVar('--text');
        corrMatrixEl.appendChild(div);
      }});
    }});
  </script>
</body>
</html>
"""
    out = DIR / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
