# 📊 Calibration Data Format

## Required Format

Experimental data for parameter calibration must be in **CSV or Excel** format with:

### Columns:
1. **`time`**: Time points (hours or days)
2. **Metabolite columns**: One column per metabolite (concentration in mM)

### Example:

```csv
time,ATP,ADP,AMP,G6P,F6P,FBP
0,2.50,0.50,0.10,0.15,0.08,0.05
6,2.45,0.55,0.12,0.18,0.09,0.06
12,2.40,0.60,0.14,0.20,0.10,0.07
24,2.30,0.70,0.18,0.25,0.12,0.09
36,2.20,0.80,0.22,0.30,0.14,0.11
48,2.10,0.90,0.26,0.35,0.16,0.13
72,2.00,1.00,0.30,0.40,0.18,0.15
```

## Requirements

✅ **Do:**
- Include `time` column (required)
- Use consistent units (hours or days)
- Include at least 5 time points
- Use metabolite abbreviations (ATP, G6P, etc.)
- Concentrations in mM (millimolar)

❌ **Don't:**
- Mix time units
- Include missing values (NaN)
- Use inconsistent metabolite names
- Include non-numeric data

## Time Units

The calibration module automatically detects time units:
- **If max(time) < 100**: Assumed to be days → converted to hours
- **If max(time) ≥ 100**: Assumed to be hours

## Example Files

### 1. Simple Format (CSV)
See: `example_calibration_data.csv`

### 2. Bordbar et al. (2015) Format
Built-in data: `Data_Brodbar_et_al_exp.xlsx`
- Transposed format (metabolites as rows, time as columns)
- Automatically converted by the app

## Creating Your Data

### From Excel:

1. Create spreadsheet with structure:
   ```
   | time | ATP  | ADP  | G6P  | ... |
   |------|------|------|------|-----|
   | 0    | 2.5  | 0.5  | 0.1  | ... |
   | 24   | 2.3  | 0.7  | 0.15 | ... |
   ```

2. Save as `.xlsx` or export as `.csv`

3. Upload in calibration page

### From Python:

```python
import pandas as pd

# Create data
data = {
    'time': [0, 6, 12, 24, 36, 48, 72],
    'ATP': [2.5, 2.45, 2.4, 2.3, 2.2, 2.1, 2.0],
    'ADP': [0.5, 0.55, 0.6, 0.7, 0.8, 0.9, 1.0],
    'G6P': [0.15, 0.18, 0.20, 0.25, 0.30, 0.35, 0.40]
}

df = pd.DataFrame(data)
df.to_csv('my_experimental_data.csv', index=False)
```

## Metabolite Names

Common metabolite abbreviations (case-sensitive):

### Adenylates:
- ATP, ADP, AMP

### Glycolysis:
- G6P, F6P, FBP, DHAP, GAP, BPG13, BPG23, PG3, PG2, PEP, PYR, LAC

### Pentose Phosphate:
- R5P, RU5P, X5P, S7P, E4P

### Nucleotides:
- GTP, GDP, GMP, IMP, INO, HYP, XAN

### Amino Acids:
- GLY, SER, ALA, VAL, LEU, etc.

## Validation

The app will validate your data:
- ✅ Check for `time` column
- ✅ Check for numeric values
- ✅ Check for reasonable concentrations (0-100 mM)
- ⚠️ Warn about missing metabolites
- ⚠️ Warn about sparse time points

## Tips

1. **More time points = better calibration**
   - Minimum: 5 points
   - Recommended: 10-20 points
   - Optimal: 30+ points

2. **Cover full dynamic range**
   - Include initial conditions (t=0)
   - Include steady state (if reached)
   - Cover transition period

3. **Measurement quality**
   - Use technical replicates if available
   - Report measurement uncertainty
   - Flag outliers

4. **Metabolite selection**
   - Include metabolites sensitive to parameters
   - Balance coverage (glycolysis, PPP, etc.)
   - Avoid highly correlated metabolites

## Troubleshooting

### "KeyError: 'time'"
→ Make sure first column is named `time`

### "Could not load experimental data"
→ Check file format (CSV or Excel)
→ Verify no special characters in metabolite names

### "No metabolites found"
→ Check column names match model metabolites
→ Use standard abbreviations (ATP not Atp)

### "Time points mismatch"
→ Ensure time column is numeric
→ Remove any text or formatting

## References

- Bordbar, A., et al. (2015). Cell Systems, 1(4), 283-292.
- Model documentation: `USER_GUIDE.md`
- Calibration guide: `CALIBRATION_GUIDE.md`
