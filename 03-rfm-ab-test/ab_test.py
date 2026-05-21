"""
DHL Supply Chain | RFM Segmentation & A/B Test — A/B Test Analysis
BA/DA Portfolio | Project 3 | Step 3
Author: Vinyl Kiran Anipe

Designs and analyses a hypothetical retention campaign targeting the
At Risk RFM segment. Simulates campaign outcome with 15% uplift on
test group. Runs two-proportion z-test, calculates significance,
confidence interval, effect size, and sample size adequacy.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import scipy.stats as stats
import os
import math

pd.set_option("display.float_format", "{:,.4f}".format)

DATA    = os.path.expanduser("~/Documents/dhl/shared/data/dhl-synthetic/")
PROJECT = os.path.expanduser("~/Documents/dhl/dhl-business-analyst/03-rfm-ab-test/")
FIGURES = os.path.join(PROJECT, "figures")
OUTPUTS = os.path.join(PROJECT, "outputs")
os.makedirs(FIGURES, exist_ok=True)
os.makedirs(OUTPUTS, exist_ok=True)

DHL_RED    = "#D40511"
DHL_YELLOW = "#FFCC00"
SEED = 42
np.random.seed(SEED)

# ── Load RFM output (from rfm_analysis.py) ────────────────────────────────────
rfm_path = os.path.join(OUTPUTS, "customer_rfm.csv")
if not os.path.exists(rfm_path):
    raise FileNotFoundError(f"customer_rfm.csv not found at {rfm_path}. Run rfm_analysis.py first.")

rfm = pd.read_csv(rfm_path)
at_risk = rfm[rfm["Segment"] == "At Risk"].copy().reset_index(drop=True)
print(f"At Risk segment: {len(at_risk)} customers")
print(f"  Revenue at risk: ${at_risk['monetary'].sum():,.0f}")
print(f"  Avg recency: {at_risk['recency'].mean():.0f} days")
print(f"  Avg order frequency: {at_risk['frequency'].mean():.1f} orders\n")

# ── STEP 1: Random assignment to test / control ────────────────────────────────
print("[1/5] Random assignment to test/control (seed=42)...")
at_risk = at_risk.sample(frac=1, random_state=SEED).reset_index(drop=True)
mid = len(at_risk) // 2
at_risk["Group"] = ["Test" if i < mid else "Control" for i in range(len(at_risk))]

test_group    = at_risk[at_risk["Group"] == "Test"]
control_group = at_risk[at_risk["Group"] == "Control"]
print(f"  Test group:    {len(test_group)} customers")
print(f"  Control group: {len(control_group)} customers")
print(f"  Test revenue at risk:    ${test_group['monetary'].sum():,.0f}")
print(f"  Control revenue at risk: ${control_group['monetary'].sum():,.0f}")

# Check groups are balanced on key metrics
print("\n  Balance check — group means:")
for col in ["recency","frequency","monetary","avg_order_value"]:
    print(f"    {col:<22}: Test={test_group[col].mean():.2f} | Control={control_group[col].mean():.2f}")

# ── STEP 2: Simulate campaign outcome ─────────────────────────────────────────
print("\n[2/5] Simulating campaign outcome...")
UPLIFT        = 0.15     # 15% uplift on order probability for test group
BASE_CONV_RATE = 0.38    # ~38% of At Risk customers place an order in 90 days (baseline)

# Base conversion probability from recency: inversely scaled
def base_prob(recency_days, base_rate=BASE_CONV_RATE):
    """Customers with lower recency (more recent) have higher conversion probability."""
    recency_factor = np.clip(1 - (recency_days - 30) / 400, 0.2, 1.0)
    return base_rate * recency_factor

# Control: base probability
control_group = control_group.copy()
control_group["conv_prob"] = control_group["recency"].apply(base_prob)
control_group["converted"] = (np.random.uniform(0, 1, len(control_group)) <
                               control_group["conv_prob"]).astype(int)

# Test: base probability × (1 + uplift)
test_group = test_group.copy()
test_group["conv_prob"] = test_group["recency"].apply(lambda r: min(base_prob(r) * (1 + UPLIFT), 0.99))
test_group["converted"] = (np.random.uniform(0, 1, len(test_group)) <
                            test_group["conv_prob"]).astype(int)

# Simulate order value for converters — test group gets same AOV (guardrail metric)
test_converters    = test_group[test_group["converted"] == 1]
control_converters = control_group[control_group["converted"] == 1]

# AOV: use actual historical AOV from RFM + small random noise
test_aov    = test_converters["avg_order_value"].values * np.random.normal(1.0, 0.05, len(test_converters))
control_aov = control_converters["avg_order_value"].values * np.random.normal(1.0, 0.05, len(control_converters))

# ── STEP 3: Compute primary and guardrail metrics ─────────────────────────────
print("[3/5] Computing test metrics...")

n_test          = len(test_group)
n_control       = len(control_group)
conv_test       = test_group["converted"].sum()
conv_control    = control_group["converted"].sum()
conv_rate_test    = conv_test / n_test
conv_rate_control = conv_control / n_control
lift_abs        = conv_rate_test - conv_rate_control
lift_rel        = lift_abs / conv_rate_control * 100

aov_test_mean    = np.mean(test_aov)
aov_control_mean = np.mean(control_aov)
aov_diff         = aov_test_mean - aov_control_mean
aov_diff_pct     = aov_diff / aov_control_mean * 100

print(f"\n  PRIMARY METRIC — Conversion Rate (90-day order placed):")
print(f"    Test group:    {conv_test}/{n_test} = {conv_rate_test:.1%}")
print(f"    Control group: {conv_control}/{n_control} = {conv_rate_control:.1%}")
print(f"    Absolute lift: {lift_abs:+.4f} ({lift_rel:+.1f}% relative)")
print(f"\n  GUARDRAIL METRIC — Average Order Value:")
print(f"    Test AOV:    ${aov_test_mean:,.2f}")
print(f"    Control AOV: ${aov_control_mean:,.2f}")
print(f"    Difference:  ${aov_diff:+,.2f} ({aov_diff_pct:+.2f}%)")

# ── STEP 4: Statistical tests ─────────────────────────────────────────────────
print("\n[4/5] Running statistical tests...")

# --- Two-proportion z-test for conversion rate ---------------------------------
# Pooled proportion
p_pool  = (conv_test + conv_control) / (n_test + n_control)
se_pool = math.sqrt(p_pool * (1 - p_pool) * (1/n_test + 1/n_control))
z_stat  = lift_abs / se_pool
p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))  # two-tailed

# 95% confidence interval on the difference
se_diff = math.sqrt(conv_rate_test*(1-conv_rate_test)/n_test +
                    conv_rate_control*(1-conv_rate_control)/n_control)
ci_lower = lift_abs - 1.96 * se_diff
ci_upper = lift_abs + 1.96 * se_diff

# Effect size (Cohen's h for proportions)
phi_test    = 2 * math.asin(math.sqrt(conv_rate_test))
phi_control = 2 * math.asin(math.sqrt(conv_rate_control))
cohens_h    = abs(phi_test - phi_control)

# Statistical power (post-hoc)
n_min = max(n_test, n_control)
power_ncp = cohens_h * math.sqrt(n_min / 2)
power     = stats.norm.cdf(power_ncp - 1.96)

print(f"\n  TWO-PROPORTION Z-TEST (two-tailed, α=0.05):")
print(f"    z-statistic:  {z_stat:.4f}")
print(f"    p-value:      {p_value:.4f}")
print(f"    Significant:  {'YES ✓' if p_value < 0.05 else 'NO ✗'}")
print(f"\n  95% CONFIDENCE INTERVAL on lift:")
print(f"    [{ci_lower:+.4f}, {ci_upper:+.4f}]  "
      f"([{ci_lower:.1%}, {ci_upper:.1%}])")
print(f"\n  EFFECT SIZE (Cohen's h): {cohens_h:.4f}")
print(f"    Interpretation: {'Small' if cohens_h < 0.2 else 'Medium' if cohens_h < 0.5 else 'Large'}")
print(f"\n  POST-HOC POWER: {power:.3f}")

# --- Minimum Detectable Effect (MDE) for 80% power at α=0.05 -----------------
z_alpha = 1.96   # two-tailed α=0.05
z_beta  = 0.842  # 80% power
mde     = (z_alpha + z_beta) * math.sqrt(2 * p_pool * (1-p_pool) / n_min)
print(f"\n  SAMPLE SIZE ANALYSIS:")
print(f"    Group size: {n_min} customers per arm")
print(f"    Minimum Detectable Effect (80% power, α=0.05): {mde:.4f} ({mde:.1%})")
print(f"    Observed lift ({lift_abs:.4f}) {'≥' if lift_abs >= mde else '<'} MDE ({mde:.4f})")
print(f"    Sample adequate: {'YES ✓' if lift_abs >= mde else 'NO ✗ — increase sample or extend duration'}")

# --- AOV guardrail t-test -------------------------------------------------------
t_stat_aov, p_val_aov = stats.ttest_ind(test_aov, control_aov, equal_var=False)
print(f"\n  GUARDRAIL — AOV WELCH'S T-TEST:")
print(f"    t-statistic: {t_stat_aov:.4f}")
print(f"    p-value:     {p_val_aov:.4f}")
print(f"    AOV NOT significantly degraded: {'YES ✓' if p_val_aov > 0.05 else 'WARNING — AOV degraded'}")

# ── STEP 5: Write readout and figures ─────────────────────────────────────────
print("\n[5/5] Writing readout and figures...")

RECOMMENDATION = (
    "LAUNCH CAMPAIGN" if (p_value < 0.05 and lift_abs > 0 and p_val_aov > 0.05)
    else "DO NOT LAUNCH — insufficient evidence"
)

readout = f"""
DHL SUPPLY CHAIN — A/B TEST READOUT
======================================
Project:  RFM Segmentation & Retention Campaign — At Risk Segment
Author:   Vinyl Kiran Anipe (BA/DA)
Date:     2024-06-XX (simulated post-campaign analysis)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. HYPOTHESIS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  H₀ (null):        The retention offer has no effect on 90-day
                    re-order rate for At Risk customers.
  H₁ (alternative): The retention offer increases the 90-day
                    re-order rate compared to the control group.
  Direction:        Two-tailed (z-test), α = 0.05

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. TEST DESIGN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Target population:   At Risk RFM segment ({len(at_risk)} customers)
  Randomisation:       50/50 random split, seed=42
  Test group:          {n_test} customers — received retention offer
  Control group:       {n_control} customers — no offer (business as usual)
  Simulated uplift:    15% increase in order probability for test group
  Observation window:  90 days post-campaign launch
  Primary metric:      Conversion rate (placed ≥1 order in 90 days)
  Guardrail metric:    Average order value (must not decrease)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. RESULTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PRIMARY METRIC — Conversion Rate:
    Test group:      {conv_test}/{n_test} = {conv_rate_test:.1%}
    Control group:   {conv_control}/{n_control} = {conv_rate_control:.1%}
    Absolute lift:   {lift_abs:+.4f} ({lift_rel:+.1f}% relative lift)
    95% CI:          [{ci_lower:+.4f}, {ci_upper:+.4f}]
                     [{ci_lower:.1%}, {ci_upper:.1%}]

  GUARDRAIL METRIC — Average Order Value:
    Test group AOV:    ${aov_test_mean:,.2f}
    Control group AOV: ${aov_control_mean:,.2f}
    Difference:        ${aov_diff:+,.2f} ({aov_diff_pct:+.2f}%)
    Guardrail status:  {'PASSING — AOV not significantly degraded' if p_val_aov > 0.05 else 'FAILING — AOV significantly reduced'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. STATISTICAL SIGNIFICANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Test:         Two-proportion z-test (two-tailed)
  z-statistic:  {z_stat:.4f}
  p-value:      {p_value:.4f}
  α threshold:  0.05
  Result:       {'STATISTICALLY SIGNIFICANT — reject H₀' if p_value < 0.05 else 'NOT statistically significant — fail to reject H₀'}

  Effect size (Cohen's h):  {cohens_h:.4f}
  Interpretation:           {'Small' if cohens_h < 0.2 else 'Medium' if cohens_h < 0.5 else 'Large'} effect

  Post-hoc power:           {power:.3f} ({power*100:.1f}%)
  Minimum Detectable Effect: {mde:.4f} ({mde:.1%})
  Observed lift ≥ MDE:      {'YES — sample size is adequate' if lift_abs >= mde else 'NO — increase sample or extend duration'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. RECOMMENDATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Decision: {RECOMMENDATION}

  Rationale:
  {'  ✓ Conversion rate lift is statistically significant (p < 0.05).' if p_value < 0.05 else '  ✗ Conversion rate lift is NOT statistically significant.'}
  {'  ✓ Average order value is not significantly degraded.' if p_val_aov > 0.05 else '  ✗ Average order value is significantly degraded — guardrail failed.'}
  {'  ✓ Observed effect size exceeds the minimum detectable effect.' if lift_abs >= mde else '  ✗ Sample size is insufficient to detect the observed effect reliably.'}

  If launched at scale to all At Risk customers ({len(at_risk)} total):
    Expected additional conversions: {round(lift_abs * len(at_risk))} customers
    Revenue recovered (est.):        ${lift_abs * len(at_risk) * rfm[rfm['Segment']=='At Risk']['avg_order_value'].mean():,.0f}

  Next steps:
  1. Present results to Commercial Manager for campaign sign-off.
  2. Segment At Risk by Customer_Type for targeted offer customisation.
  3. Track actual 90-day conversion rate post-launch against this baseline.
  4. Run a follow-up analysis at 90 days to validate simulated results.
  5. Consider expanding to "About to Sleep" segment in the next sprint.
"""

readout_path = os.path.join(OUTPUTS, "ab_test_readout.txt")
with open(readout_path, "w") as f:
    f.write(readout)
print(f"  → Saved ab_test_readout.txt")
print(readout)

# ── FIGURES ────────────────────────────────────────────────────────────────────

# Figure 12: Conversion rate comparison with CI
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("A/B Test Results — Retention Campaign for At Risk Segment",
             fontsize=13, fontweight="bold")

# Left: conversion bars
bars = axes[0].bar(["Control", "Test"],
                   [conv_rate_control * 100, conv_rate_test * 100],
                   color=["#607D8B", DHL_RED], edgecolor="white", width=0.5)
for bar, val in zip(bars, [conv_rate_control, conv_rate_test]):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                 f"{val:.1%}", ha="center", va="bottom", fontsize=14, fontweight="bold")
sig_text = f"p={p_value:.4f} {'★ Significant' if p_value < 0.05 else '✗ Not significant'}"
axes[0].set_title(f"Conversion Rate: {conv_rate_control:.1%} → {conv_rate_test:.1%}\n{sig_text}",
                  fontsize=10, fontweight="bold")
axes[0].set_ylabel("Conversion Rate (%)", fontsize=10)
axes[0].set_ylim(0, max(conv_rate_test, conv_rate_control) * 100 * 1.2)
axes[0].grid(axis="y", linestyle="--", alpha=0.4)

# Right: confidence interval plot
ci_x = [ci_lower * 100, ci_upper * 100]
axes[1].barh([0], [ci_upper * 100 - ci_lower * 100], left=[ci_lower * 100],
             height=0.4, color=DHL_RED if p_value < 0.05 else "#607D8B", alpha=0.6)
axes[1].axvline(0, color="#333", linewidth=1.5, linestyle="--", label="No effect (0%)")
axes[1].axvline(lift_abs * 100, color=DHL_RED, linewidth=2, label=f"Observed lift {lift_abs:.1%}")
axes[1].scatter([lift_abs * 100], [0], color=DHL_RED, s=120, zorder=5)
axes[1].set_yticks([])
axes[1].set_xlabel("Lift in Conversion Rate (percentage points)", fontsize=10)
axes[1].set_title(f"95% Confidence Interval: [{ci_lower:.1%}, {ci_upper:.1%}]\n"
                  f"Effect size (Cohen's h) = {cohens_h:.3f}",
                  fontsize=10, fontweight="bold")
axes[1].legend(fontsize=9)
axes[1].grid(axis="x", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "12_ab_test_results.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 12_ab_test_results.png")

# Figure 13: Power curve
uplift_range = np.linspace(0.01, 0.20, 200)
powers = []
for u in uplift_range:
    p2_h = min(conv_rate_control * (1 + u), 0.99)
    h_val = 2*math.asin(math.sqrt(p2_h)) - 2*math.asin(math.sqrt(conv_rate_control))
    ncp = abs(h_val) * math.sqrt(n_min / 2)
    powers.append(stats.norm.cdf(ncp - 1.96))

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot([u*100 for u in uplift_range], [p*100 for p in powers],
        color=DHL_RED, linewidth=2.5)
ax.axhline(80, color="#333", linewidth=1.5, linestyle="--", label="80% power threshold")
ax.axvline(UPLIFT * 100, color=DHL_YELLOW, linewidth=2, linestyle="-.",
           label=f"Simulated uplift ({UPLIFT:.0%})")
ax.axvline(mde * 100, color="#4CAF50", linewidth=2, linestyle=":",
           label=f"MDE ({mde:.1%})")
ax.fill_between([u*100 for u in uplift_range], [p*100 for p in powers],
                alpha=0.1, color=DHL_RED)
ax.set_xlabel("Uplift in Conversion Rate (%)", fontsize=10)
ax.set_ylabel("Statistical Power (%)", fontsize=10)
ax.set_title(f"Power Curve — At Risk A/B Test (n={n_min} per arm, α=0.05)\n"
             f"Power at simulated uplift ({UPLIFT:.0%}): {power*100:.1f}%",
             fontsize=12, fontweight="bold")
ax.legend(fontsize=9)
ax.grid(linestyle="--", alpha=0.4)
ax.set_ylim(0, 105)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES, "13_ab_test_power_curve.png"), dpi=150, bbox_inches="tight")
plt.close()
print("  → Saved 13_ab_test_power_curve.png")

print(f"\n{'='*70}")
print("  A/B TEST ANALYSIS COMPLETE")
print(f"  Decision: {RECOMMENDATION}")
print(f"  p-value:  {p_value:.4f}")
print(f"  Figures:  12–13")
print(f"  Output:   ab_test_readout.txt")
print(f"{'='*70}\n")
