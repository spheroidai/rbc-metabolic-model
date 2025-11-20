# 🧪 Test Data for Sensitivity Analysis

## 📁 File: `Test_Custom_Data.csv`

### Purpose
This test dataset is designed to validate the sensitivity analysis functionality by providing data that is **structurally identical** to Brodbar et al. data but with **significantly different values**.

### Structure
- **Metabolites**: 20 key RBC metabolites
- **Timepoints**: 14 measurements (0, 0.5, 1, 2, 3, 4, 6, 8, 12, 16, 24, 30, 36, 42 days)
- **Format**: CSV (Time in columns, Metabolites in rows)

### Modifications from Brodbar Data
Values have been modified by:
- Random factors between 0.5x and 2.0x (50% to 200%)
- Additional noise (~10%)
- Expected changes: **20-50% difference** on average

### How to Use

#### Step 1: Upload Data
1. Go to **📤 Data Upload** page
2. Click "Browse files"
3. Select `Test_Custom_Data.csv`
4. Wait for upload and validation

#### Step 2: Activate Data
1. Review the data preview
2. Select mode: **"Replace experimental data"** (for maximum impact)
3. Click **"Apply Data to Simulations"**

#### Step 3: Run Sensitivity Analysis
1. Go to **📊 Sensitivity Analysis** page
2. Click **"▶️ Run Comparative Analysis"**
3. Wait for both simulations to complete (~1-2 minutes)

#### Step 4: Review Results
You should see:
- ✅ **Flux changes**: 10-30% for many reactions
- ✅ **Metabolite changes**: 20-50% for modified metabolites
- ✅ **Heatmap**: Color-coded differences over time
- ✅ **Tornado plot**: Clear ranking of sensitive metabolites

### Expected Output

**Top Sensitive Metabolites:**
- ATP: ~-25% change
- LAC (Lactate): ~+50% change
- BPG23: ~-15% change
- NAD/NADH ratio: ~+30% change

**Top Sensitive Fluxes:**
- Glycolysis reactions: 15-25% change
- Lactate production: 40-60% change
- ATP synthesis: 20-30% change

### Troubleshooting

**If you see 0% changes:**
1. Check that data is uploaded and active
2. Verify `curve_fit_strength` is set to 2.0 or higher
3. Confirm data format matches (Time in columns)
4. Check debug info shows correct data shape

**If simulation fails:**
1. Check that all metabolite names are recognized
2. Verify no negative values in data
3. Ensure time column is named "Metabolite" or similar

### Notes
- This is **synthetic test data** - not real experimental results
- Use only for testing the sensitivity analysis feature
- For real analysis, use your actual experimental data

---

**Created**: 2025-11-18
**Purpose**: Sensitivity Analysis Testing
