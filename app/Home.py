"""Experiment explorer: effects, profit under editable assumptions, and the sample-ratio check."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import ab  # noqa: E402

st.set_page_config(page_title="Email experiment explorer", layout="wide")


@st.cache_data
def get_data():
    return ab.load()


@st.cache_data
def spend_effect(arm, n_boot=4000):
    df = get_data()
    t, c = df[df.segment == arm].spend, df[df.segment == ab.CONTROL].spend
    r = ab.diff_in_means(t, c, n_boot=n_boot, seed=1)
    return r["diff"], r["boots"]


df = get_data()
st.title("Which email should we send?")
st.caption("Hillstrom E-Mail Analytics Challenge: 64,000 customers randomized to Men's email, Women's email or no email. "
           "Outcomes over 2 weeks.")

st.sidebar.header("Your business assumptions")
margin = st.sidebar.slider("Contribution margin on spend", 0.05, 0.80, 0.40, 0.05)
cost = st.sidebar.slider("Cost per email sent ($)", 0.00, 0.30, 0.05, 0.01)
conf = st.sidebar.select_slider("Confidence for the decision interval", [0.80, 0.90, 0.95, 0.99], 0.95)
customers = st.sidebar.number_input("Customers on the list", 1_000, 10_000_000, 100_000, 10_000)

st.subheader("Decision at your assumptions")
st.write("Rule: send only if the **lower bound** of incremental profit per customer is above zero. "
         "Two emails are compared with the same control, so the interval is widened (Bonferroni).")
cols = st.columns(2)
alpha = (1 - conf) / 2  # two emails -> split alpha
for col, arm in zip(cols, ab.ARMS):
    diff, boots = spend_effect(arm)
    lo, hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    p_mid = ab.incremental_profit(diff, margin, cost)
    p_lo = ab.incremental_profit(lo, margin, cost)
    p_hi = ab.incremental_profit(hi, margin, cost)
    with col:
        st.markdown(f"### {arm}")
        st.metric("Profit per customer", f"${p_mid:.3f}", f"range ${p_lo:.3f} to ${p_hi:.3f}", delta_color="off")
        st.metric(f"Expected profit on {customers:,} customers", f"${p_mid * customers:,.0f}")
        if p_lo > 0:
            st.success("Send: the whole interval is above zero.")
        elif p_hi < 0:
            st.error("Don't send: the whole interval is below zero.")
        else:
            st.warning("Unclear at these assumptions: the interval includes zero.")

st.subheader("Raw results by arm")
summary = df.groupby("segment").agg(customers=("spend", "size"), visit_rate=("visit", "mean"),
                                    conversion_rate=("conversion", "mean"), spend_per_customer=("spend", "mean"))
st.dataframe(summary.style.format({"visit_rate": "{:.2%}", "conversion_rate": "{:.2%}",
                                   "spend_per_customer": "${:.3f}", "customers": "{:,}"}))

st.subheader("Sample-ratio check")
counts, chi2, p = ab.sample_ratio_check(df)
st.write(f"Arm sizes {counts.to_dict()} against an equal split: chi-square p = {p:.2f}. "
         + ("No sign of broken randomization." if p > 0.01 else "Randomization looks broken; investigate before trusting results."))

st.info("Limits: 2-week window, revenue not margin (you supply margin and cost), a single 2008 campaign.")
