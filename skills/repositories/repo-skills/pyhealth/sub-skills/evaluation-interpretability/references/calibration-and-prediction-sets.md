# Calibration and prediction sets

PyHealth includes calibration utilities and prediction-set modules under
`pyhealth.calib`, plus conformal-oriented examples. Calibration data must not
be reused as test data. For a four-way protocol use the package's
`split_by_visit_conformal` only when the research design explicitly needs
train/validation/calibration/test; for longitudinal clinical data, preserve
patient grouping whenever the protocol permits.

Before computing ECE or a prediction set, record: probability definition;
number/binning policy; calibration split; coverage target; class imbalance;
missingness; and whether the result is marginal or subgroup-conditional.

A calibration smoke should use deterministic probabilities and labels and
assert finite output plus expected monotonic/coverage direction. It should not
fetch data. Read the installed API for exact class/function arguments because
calibration and prediction-set names are versioned independently of the main
metric functions.
