# 🎯 Parameter Calibration Guide

## Overview

The Parameter Calibration module automatically optimizes enzyme kinetic parameters to match experimental data using advanced optimization algorithms.

## Features

- ✅ **Multiple Optimization Algorithms**
  - Differential Evolution (global optimizer)
  - L-BFGS-B (local optimizer)
  - Nonlinear Least Squares

- ✅ **Statistical Analysis**
  - Confidence intervals for parameters
  - Parameter sensitivity analysis
  - R² goodness-of-fit metric
  - Residual analysis

- ✅ **Validation**
  - Cross-validation support
  - Bootstrap resampling
  - Out-of-sample testing

---

## Quick Start

### 1. Prepare Your Data

Experimental data should be in CSV or Excel format with:
- **time** column (hours or days)
- One column per metabolite concentration (mM)

Example:
```csv
time,ATP,ADP,G6P,F6P
0,2.5,0.5,0.1,0.05
24,2.3,0.7,0.15,0.08
48,2.1,0.9,0.20,0.12
72,2.0,1.0,0.25,0.15
```

### 2. Launch Calibration Page

1. Navigate to **🎯 Parameter Calibration** in the sidebar
2. Upload your experimental data or use built-in data
3. Select target metabolites
4. Choose parameters to optimize

### 3. Configure Calibration

**Choose Parameters:**
- Start with 3-5 parameters
- Use preset groups (Glycolysis, PPP, etc.)
- Set reasonable bounds (typically 0.1x - 10x initial value)

**Select Algorithm:**
- **Differential Evolution**: Best for initial calibration (robust, global)
- **L-BFGS-B**: Fast refinement (requires good initial guess)
- **Least Squares**: Specialized for linear-like problems

**Set Options:**
- **Max Iterations**: 1000 (increase for complex problems)
- **Confidence Level**: 95% (standard)

### 4. Run and Analyze

Click **🚀 Run Calibration** and wait for completion (1-5 minutes typically).

Review results:
- **R² Score**: > 0.9 is excellent, > 0.7 is good
- **Parameter Changes**: Check if reasonable
- **Confidence Intervals**: Narrow = high confidence
- **Sensitivity**: High = important parameter

---

## Usage Example

### Python Script

```python
from parameter_calibration import ParameterCalibrator
from simulation_engine import SimulationEngine
import pandas as pd
import numpy as np

# Load experimental data
exp_data = pd.read_csv("experimental_data.csv")

# Setup simulation function
engine = SimulationEngine()

def simulation_function(params):
    result = engine.run_simulation(
        duration=72.0,
        custom_params=params
    )
    return result

# Create calibrator
calibrator = ParameterCalibrator(
    simulation_function=simulation_function,
    experimental_data=exp_data,
    target_metabolites=['ATP', 'ADP', 'G6P'],
    time_points=exp_data['time'].values
)

# Define parameters to optimize
params_to_optimize = {
    'vmax_HK': (1.0, 0.1, 10.0),   # (initial, lower, upper)
    'vmax_PFK': (1.0, 0.1, 10.0),
    'vmax_PK': (1.0, 0.1, 10.0)
}

# Run calibration
result = calibrator.calibrate(
    params_to_optimize=params_to_optimize,
    base_params={},  # Other fixed parameters
    method='differential_evolution',
    max_iterations=1000,
    confidence_level=0.95
)

# Check results
print(f"Success: {result.success}")
print(f"R²: {result.r_squared:.4f}")
print(f"Optimized parameters: {result.optimized_params}")
print(f"Confidence intervals: {result.confidence_intervals}")
print(f"Sensitivity: {result.sensitivity}")
```

---

## Optimization Methods

### Differential Evolution (Recommended)

**When to use:**
- Initial calibration
- Complex landscapes
- Poor initial guesses
- Multiple local minima

**Pros:**
- Global optimizer (finds true optimum)
- Robust and reliable
- No gradient needed

**Cons:**
- Slower (10-100x vs local methods)
- More function evaluations

**Settings:**
```python
method='differential_evolution'
max_iterations=1000  # Increase for complex problems
```

### L-BFGS-B (Local Minimization)

**When to use:**
- Refinement of existing solution
- Quick iterations
- Good initial guess available
- Smooth objective function

**Pros:**
- Very fast
- Efficient for well-behaved problems

**Cons:**
- Can get stuck in local minima
- Requires good starting point

**Settings:**
```python
method='minimize'
max_iterations=100  # Usually converges quickly
```

### Least Squares

**When to use:**
- Sum-of-squares objective
- Nearly linear problems
- High-quality data

**Pros:**
- Specialized algorithm
- Fast convergence
- Good for overdetermined systems

**Cons:**
- Only for least-squares problems
- May fail on ill-conditioned problems

**Settings:**
```python
method='least_squares'
max_iterations=100
```

---

## Interpreting Results

### R² (Coefficient of Determination)

Measures goodness of fit:
- **R² > 0.95**: Excellent fit
- **R² = 0.80-0.95**: Good fit
- **R² = 0.70-0.80**: Acceptable fit
- **R² < 0.70**: Poor fit (model or data issues)

**Action if R² is low:**
1. Add more parameters to optimize
2. Check data quality
3. Consider model structure limitations
4. Increase max_iterations

### Confidence Intervals

Range where true parameter value likely lies:

```
Example: vmax_HK = 1.23 [1.15, 1.31]
```

**Narrow intervals** (±10%):
- High confidence
- Good data quality
- Parameter well-determined

**Wide intervals** (±50%+):
- High uncertainty
- Need more data
- Parameter may not be identifiable

### Sensitivity

Normalized measure of parameter importance:

**High sensitivity** (> 0.5):
- Parameter strongly affects fit
- Important to calibrate
- Small changes have big impact

**Low sensitivity** (< 0.1):
- Parameter barely affects fit
- May not need calibration
- Consider fixing to literature value

### Parameter Changes

Check if optimized values are biologically plausible:

```
vmax_HK: 1.0 → 1.5 (+50%)  ✅ Reasonable
km_ATP: 2.0 → 0.1 (-95%)   ⚠️ Suspicious
```

**Actions for suspicious changes:**
1. Check experimental data
2. Verify parameter bounds
3. Consult literature values
4. Consider parameter correlations

---

## Best Practices

### 1. Data Preparation

✅ **Do:**
- Use high-quality experimental data
- Include multiple time points (≥5)
- Cover full dynamic range
- Report measurement uncertainty

❌ **Don't:**
- Use single time point
- Mix different experimental conditions
- Include outliers without flagging

### 2. Parameter Selection

✅ **Do:**
- Start with 3-5 most sensitive parameters
- Use literature values as initial guesses
- Set bounds at 0.1x - 10x initial value
- Consider parameter correlations

❌ **Don't:**
- Optimize >10 parameters at once
- Use arbitrary initial guesses
- Set unrealistic bounds
- Ignore prior knowledge

### 3. Validation

✅ **Do:**
- Validate on independent data
- Perform cross-validation
- Check biological plausibility
- Compare with literature

❌ **Don't:**
- Only test on calibration data
- Accept results blindly
- Ignore large confidence intervals
- Extrapolate beyond data range

### 4. Troubleshooting

**Problem: Calibration fails**
- Check data format and quality
- Widen parameter bounds
- Try different optimization method
- Reduce number of parameters

**Problem: Poor R² score**
- Add more target metabolites
- Optimize more parameters
- Check for model limitations
- Verify experimental data quality

**Problem: Unrealistic parameters**
- Tighten bounds around literature values
- Add regularization (future feature)
- Check for parameter identifiability
- Consider fixing some parameters

---

## Advanced Features

### Cross-Validation

Assess generalization performance:

```python
cv_results = calibrator.cross_validate(
    params_to_optimize=params_to_optimize,
    base_params=base_params,
    k_folds=5
)

print(f"Mean CV Score: {cv_results['mean_score']:.4f}")
print(f"Std Dev: {cv_results['std_score']:.4f}")
```

### Bootstrapping

Estimate parameter uncertainty:

```python
# Coming soon!
bootstrap_results = calibrator.bootstrap(
    params_to_optimize=params_to_optimize,
    n_iterations=100
)
```

### Multi-Objective Optimization

Balance multiple objectives:

```python
# Coming soon!
result = calibrator.multi_objective_calibrate(
    objectives=['fit_quality', 'parameter_simplicity'],
    weights=[0.7, 0.3]
)
```

---

## API Reference

### ParameterCalibrator

```python
ParameterCalibrator(
    simulation_function: Callable,
    experimental_data: pd.DataFrame,
    target_metabolites: List[str],
    time_points: np.ndarray
)
```

**Parameters:**
- `simulation_function`: Function that runs simulation with given parameters
- `experimental_data`: DataFrame with experimental measurements
- `target_metabolites`: List of metabolite names to match
- `time_points`: Time points for comparison (hours or days)

### CalibrationResult

```python
@dataclass
class CalibrationResult:
    optimized_params: Dict[str, float]
    initial_params: Dict[str, float]
    objective_value: float
    success: bool
    message: str
    iterations: int
    confidence_intervals: Dict[str, Tuple[float, float]]
    sensitivity: Dict[str, float]
    residuals: np.ndarray
    r_squared: float
```

---

## Examples

### Example 1: Glycolysis Calibration

```python
params_to_optimize = {
    'vmax_HK': (1.2, 0.5, 3.0),
    'km_HK_ATP': (0.5, 0.1, 2.0),
    'vmax_PFK': (2.0, 0.5, 5.0),
    'km_PFK_F6P': (0.3, 0.1, 1.0)
}

result = calibrator.calibrate(
    params_to_optimize=params_to_optimize,
    base_params=default_params,
    method='differential_evolution',
    max_iterations=2000
)
```

### Example 2: Quick Refinement

```python
# After initial calibration, refine locally
result_refined = calibrator.calibrate(
    params_to_optimize=params_to_optimize,
    base_params={**default_params, **result.optimized_params},
    method='minimize',
    max_iterations=100
)
```

### Example 3: Sensitivity-Based Selection

```python
# First pass: calibrate many parameters
result1 = calibrator.calibrate(params_all, base_params, ...)

# Identify sensitive parameters
sensitive = {k: v for k, v in result1.sensitivity.items() if v > 0.5}

# Second pass: refine only sensitive parameters
result2 = calibrator.calibrate(sensitive, base_params, ...)
```

---

## Citation

If you use this calibration module in your research, please cite:

```
Bordbar, A., et al. (2015). Personalized Whole-Cell Kinetic Models of 
Metabolism for Discovery in Genomics and Pharmacodynamics. 
Cell Systems, 1(4), 283-292.
```

---

## Support

For issues or questions:
- 📧 Email: support@example.com
- 💬 GitHub Issues: [github.com/your-repo/issues](https://github.com)
- 📚 Documentation: See `AUTHENTICATION_SETUP_GUIDE.md`

---

**Happy Calibrating! 🎯**
