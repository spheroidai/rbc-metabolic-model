# 📖 RBC Metabolic Model - User Guide

Quick reference guide for using the Streamlit web application.

## 🚀 Getting Started

### Starting the Application

```bash
streamlit run streamlit_app/app.py
```

The app will open at `http://localhost:8501`

---

## 📱 Navigation

### Main Pages

- **🏠 Home** - Overview and quick start
- **🚀 Simulation** - Run metabolic simulations
- **🔬 Flux Analysis** - Explore metabolic fluxes
- **📊 Sensitivity Analysis** - Compare datasets
- **📤 Data Upload** - Import custom data

---

## 🎯 Common Workflows

### Workflow 1: Basic Simulation

1. Go to **🚀 Simulation** page
2. Configure parameters (or use defaults):
   - Simulation duration: 42 hours
   - Curve fitting: 50%
   - Initial conditions: JA Final
3. Click **▶️ Start Simulation**
4. View results:
   - Metabolite concentrations over time
   - Validation against Brodbar data
5. **Export** results as CSV

### Workflow 2: pH Perturbation Analysis

1. Go to **🚀 Simulation** page
2. Select **pH Perturbation** type:
   - **Acidosis**: Simulates blood acidification
   - **Alkalosis**: Simulates blood alkalinization
   - **Step**: Instant pH change
   - **Ramp**: Gradual pH transition
3. Set **severity** (Mild/Moderate/Severe)
4. Click **▶️ Start Simulation**
5. View **Bohr Effect Analysis**:
   - P50 changes (oxygen binding affinity)
   - O2 saturation curves
   - 2,3-BPG levels

### Workflow 3: Custom Data Analysis

#### Step 1: Upload Data

1. Go to **📤 Data Upload** page
2. Prepare your data file:
   - **CSV** or **Excel** format
   - Time points in columns OR rows
   - Metabolite concentrations in mM
3. **Upload** your file
4. Review the **Data Preview**

#### Step 2: Map Metabolites

1. Use **Intelligent Column Mapping**:
   - Auto-detection with fuzzy matching
   - Manual corrections if needed
2. Click **💾 Save Mapping**
3. Choose integration mode:
   - **Replace experimental data**: Use your data as baseline
   - **Validation only**: Compare with Brodbar data

#### Step 3: Run Analysis

1. Go to **📊 Sensitivity Analysis** page
2. Click **▶️ Run Comparative Analysis**
3. Review results:
   - **Top sensitive metabolites** (biggest differences)
   - **Side-by-side comparisons** (your data vs Brodbar)
   - **Validation metrics** (R², RMSE, MAE)

### Workflow 4: Flux Analysis

1. **Run a simulation first** (Simulation page)
2. Go to **🔬 Flux Analysis** page
3. Explore:
   - **Flux distributions** at key timepoints
   - **Flux heatmap** for all reactions
   - **Detailed flux analysis** for specific reactions
4. **Export** flux data as CSV

---

## 📊 Understanding Results

### Metabolite Plots

- **Solid lines**: Simulation predictions
- **Dots/Diamonds**: Experimental measurements
- **Colors**: Different metabolites or datasets

### Validation Metrics

- **R² (R-squared)**:
  - > 0.9 = Excellent fit ✅
  - 0.7-0.9 = Good fit
  - < 0.5 = Poor fit ❌
  
- **RMSE/MAE**: Lower is better (units: mM)

### Flux Analysis

- **Positive flux**: Reaction proceeding forward
- **Negative flux**: Reaction proceeding backward
- **Heatmap colors**:
  - 🔴 Red = High flux
  - 🔵 Blue = Low flux

---

## 💡 Tips & Best Practices

### Data Upload

✅ **DO:**
- Use clear column names (ATP, Glucose, etc.)
- Include time column (hours)
- Use consistent units (mM)
- Check for missing values

❌ **DON'T:**
- Mix different units
- Use special characters in column names
- Skip time information

### Simulation

✅ **Recommended Settings:**
- Curve fit strength: 40-60% (default: 50%)
- Solver: LSODA (adaptive, robust)
- Tolerances: Default values work well

⚠️ **Troubleshooting:**
- If simulation fails: Try different solver (BDF for stiff systems)
- If results look wrong: Check initial conditions
- If too slow: Reduce simulation duration

### Sensitivity Analysis

✅ **Best for:**
- Comparing different experimental conditions
- Validating model against new data
- Identifying most variable metabolites

📝 **Note:** Fluxes are NOT compared because they're determined by kinetic laws, not experimental data.

---

## 📥 Exporting Data

### Available Exports

1. **Simulation Results** (CSV)
   - Time points
   - All metabolite concentrations
   - Experimental vs simulation

2. **Flux Data** (CSV)
   - All reactions
   - Flux values over time
   - Grouped by pathway

3. **Bohr Effect** (CSV)
   - P50 values
   - O2 saturation
   - pH levels

---

## 🐛 Troubleshooting

### Common Issues

**"No simulation results found"**
- Go to Simulation page first
- Run a simulation before accessing other analyses

**"Invalid data format"**
- Check your CSV/Excel structure
- Ensure Time column exists
- Remove empty rows/columns

**"Metabolite not found"**
- Check metabolite names match RBC model
- Use the intelligent mapper in Data Upload

**Simulation taking too long**
- Reduce simulation duration
- Try LSODA solver
- Check for numerical instabilities

---

## 📚 Additional Resources

- **Documentation Folder**: Detailed project documentation
- **TEST_DATA_README.md**: Guide for validation testing
- **README.md**: Technical overview

---

## 🆘 Need Help?

1. Check this guide
2. Review the in-app **💡 How to Use** sections
3. Check the Documentation folder
4. Try the test data (`Test_Custom_Data.csv`)

---

**Version:** 2.0  
**Last Updated:** November 2025  
**Author:** Jorgelindo da Veiga
