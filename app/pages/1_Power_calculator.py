"""Power calculator and peeking simulator for planning the next experiment."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import ab  # noqa: E402

st.set_page_config(page_title="Power calculator", layout="wide")
st.title("Plan the next experiment")

st.header("How many customers per arm?")
kind = st.radio("Metric type", ["Rate (visit, conversion)", "Average (spend per customer)"], horizontal=True)
c1, c2, c3 = st.columns(3)
alpha = c1.selectbox("Significance level", [0.05, 0.01, 0.10], 0)
power = c2.selectbox("Power", [0.8, 0.9, 0.95], 0)

if kind.startswith("Rate"):
    base = c3.number_input("Baseline rate", 0.001, 0.99, 0.106, 0.005, format="%.3f")
    st.caption("Default 10.6% is the no-email visit rate in the Hillstrom data.")
    mdes = [0.005, 0.01, 0.02, 0.03, 0.045, 0.077]
    table = pd.DataFrame({"Detectable lift (points)": [m * 100 for m in mdes],
                          "Customers per arm": [ab.n_per_arm(base, m, alpha, power) for m in mdes]})
    custom = st.number_input("Your minimum detectable lift (absolute, e.g. 0.02 = 2 points)", 0.001, 0.5, 0.02, 0.005, format="%.3f")
    n = ab.n_per_arm(base, custom, alpha, power)
else:
    sd = c3.number_input("Std dev of spend", 0.1, 100.0, 13.0, 0.5)
    st.caption("Spend is mostly zeros with a long tail: std ~ $12 to $18 in the Hillstrom data against a mean near $1. "
               "That is why spend needs far more customers than visits.")
    mdes = [0.05, 0.10, 0.25, 0.50, 0.77]
    table = pd.DataFrame({"Detectable lift ($ per customer)": mdes,
                          "Customers per arm": [ab.n_per_arm_mean(sd, m, alpha, power) for m in mdes]})
    custom = st.number_input("Your minimum detectable lift ($ per customer)", 0.01, 10.0, 0.25, 0.05)
    n = ab.n_per_arm_mean(sd, custom, alpha, power)

st.metric("Customers needed per arm", f"{n:,}", f"{2 * n:,} for a two-arm test", delta_color="off")
st.dataframe(table.style.format({"Customers per arm": "{:,}"}), hide_index=True)

st.header("What if you peek?")
st.write("Simulates an experiment with **no real effect**, checked daily, stopping at the first significant result.")
d1, d2, d3 = st.columns(3)
days = d1.slider("Days", 3, 30, 14)
per_day = d2.number_input("Customers per arm per day", 100, 20000, 1000, 100)
rate = d3.number_input("Base rate", 0.01, 0.5, 0.10, 0.01)
if st.button("Run simulation"):
    peek, once = ab.peeking_simulation(per_day, days, rate, n_sims=3000)
    a, b = st.columns(2)
    a.metric("False wins if you test once at the end", f"{once:.1%}")
    b.metric("False wins if you stop at first significant look", f"{peek:.1%}")
