# Research plan (written before outcomes were analyzed)

## Decision and reader
**Decision:** Which email, if any, should the retailer send to its customer base, and is it worth the cost?
**Reader:** Head of e-commerce marketing. They need a send / don't-send recommendation per email, with the size of the gain in dollars and how sure we are.

## Data and access check
- Source: Kevin Hillstrom's MineThatData E-Mail Analytics Challenge (2008), 64,000 customers, randomized three ways: Men's e-mail, Women's e-mail, No e-mail. Outcomes are measured over the following two weeks.
- Downloaded from the author's site (`minethatdata.com`). The page states the data is free to use for the challenge but gives no formal license, so the repo links to the source instead of redistributing the file.
- Checked before analysis: 64,000 rows, 12 columns, no missing values, three arms of near-equal size. The file has **no customer ID**, so 6,562 exact-duplicate rows are expected collisions between customers with identical attributes. They are **not** removed.
- Only assignment and pre-treatment covariates were inspected before this plan was written.

## Hypotheses
Control = No e-mail. Three arms, so two treatment-vs-control comparisons (the family for multiple-comparison control).
- H1: Men's e-mail raises the 2-week outcome vs. control.
- H2: Women's e-mail raises the 2-week outcome vs. control.
- Exploratory (not part of the decision): Men's vs. Women's.

## Metrics
| Role | Metric | Definition |
|---|---|---|
| **Primary** | Spend per customer | `spend` over 2 weeks, zeros included (intent-to-treat) |
| Secondary | Visit rate | `visit` |
| Secondary | Conversion rate | `conversion` |
| Guardrail | Sample-ratio mismatch | arm sizes vs. an equal 1/3 split |

Spend is mostly zeros with a long right tail, so the interval for the mean difference is a bootstrap percentile interval, with a Welch t-test as a cross-check.

## Decision rule (fixed in advance)
Send an email only if the **lower bound of the Holm-adjusted 95% interval for incremental profit per customer is above zero**:

`incremental profit = margin x (spend_treatment - spend_control) - cost per email`

Assumptions (editable in the app): contribution margin **40%** of spend, cost **$0.05 per email**. These are stated assumptions, not facts from the data. The data records revenue, not margin or send cost.
A result can be statistically significant and still fail this rule. That distinction is the point of the project.

## Analysis steps
1. Sample-ratio check (chi-square on arm sizes) and covariate balance (standardized mean differences).
2. Difference in visit, conversion, spend with confidence intervals; Holm correction over the two treatment comparisons.
3. Variance reduction with past spend (`history`) as a covariate (CUPED / regression adjustment), reported next to the unadjusted estimate.
4. Heterogeneity: effects in subgroups fixed now, not chosen after looking: **newbie vs. existing**, **channel** (Phone / Web / Multichannel), **history_segment**. Report an interaction test, not just per-subgroup p-values, and correct across subgroups.
5. Peeking simulation: how often does checking a no-effect experiment daily and stopping at the first p < 0.05 produce a false win?
6. Translate to dollars under the cost assumptions; show sensitivity to margin and cost.
7. Power calculator: sample size needed for a given minimum detectable effect.

## Predictions (logged before running the analysis)
Honesty note: I have read summaries of this well-known dataset before, so these are not blind predictions.
1. Arm sizes will pass the sample-ratio check; covariates will be balanced (all |SMD| < 0.02).
2. Both emails raise visit rate; the effect on visit is larger than the effect on conversion, in relative terms.
3. Men's e-mail raises spend; Women's e-mail's effect on spend is smaller and its interval is closer to zero.
4. Adjusting for `history` shrinks interval widths for spend noticeably.
5. At the stated assumptions, Men's e-mail clears the decision rule. Women's e-mail is the closer call.
6. No subgroup interaction survives correction for multiple subgroups.
7. Daily peeking with stop-at-first-significant gives a false-positive rate well above 5% (I expect 15–30% over 14 looks).

## Limits (stated up front)
- 2-week window: no long-run effects (fatigue, unsubscribes, cannibalized later purchases).
- Revenue, not margin; cost and margin are assumed.
- One retailer, one campaign from 2008; external validity is limited.
- Intent-to-treat: we know who was sent the email, not who opened it.
