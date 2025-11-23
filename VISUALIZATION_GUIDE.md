# 🗺️ Advanced Pathway Visualization Guide

## Overview

The **Pathway Visualization** module provides KEGG-style interactive metabolic maps for the RBC model, with advanced features for exploring metabolic dynamics.

## Features

### 1. 📍 KEGG-Style Static Map

**What it shows:**
- Metabolic network as an interactive graph
- Nodes = metabolites (size/color based on concentration)
- Edges = enzymatic reactions
- Color-coded by pathway:
  - 🔴 **Red**: Glycolysis
  - 🟣 **Purple**: Pentose Phosphate Pathway
  - 🟠 **Orange**: Rapoport-Luebering Shunt
  - ⚫ **Gray**: Energy/nucleotide metabolism

**How to use:**
1. Navigate to **🗺️ Pathway Visualization**
2. Select timepoint with slider
3. Hover over nodes for metabolite info
4. Hover over edges for enzyme/reaction info

**Interpretation:**
- **Large nodes** = high concentration
- **Red nodes** = very high concentration
- **Blue nodes** = low concentration
- **Arrows** = irreversible reactions
- **Plain lines** = reversible reactions

---

### 2. 🎬 Animated Pathway

**What it shows:**
- Temporal evolution of metabolite concentrations
- Dynamic changes in the metabolic network
- Real-time concentration updates

**How to use:**
1. Go to **🎬 Animated Pathway** tab
2. Set animation speed (frame skip)
3. Click **▶ Play** to start animation
4. Use slider to manually navigate timepoints
5. Click **⏸ Pause** to stop

**Tips:**
- Higher frame skip = faster animation
- Lower frame skip = smoother but slower
- Watch for metabolite "waves" propagating through pathways

**What to look for:**
- ATP/ADP oscillations
- Glycolytic flux changes
- PPP activation patterns
- Metabolite accumulation/depletion

---

### 3. 📊 3D Heatmap

**What it shows:**
- Multi-metabolite concentration surface
- **X-axis**: Time (hours)
- **Y-axis**: Selected metabolites
- **Z-axis / Color**: Concentration (mM)

**How to use:**
1. Go to **📊 3D Heatmap** tab
2. Select metabolite group in sidebar
3. Rotate/zoom/pan 3D plot
4. Download data as CSV

**Interpretation:**
- **Peaks** = concentration maxima
- **Valleys** = concentration minima
- **Smooth surfaces** = gradual changes
- **Sharp transitions** = rapid metabolism
- **Color gradients** = concentration ranges

**Use cases:**
- Compare multiple metabolites simultaneously
- Identify coordinated changes
- Detect phase shifts
- Spot outliers or unusual patterns

---

### 4. 🌳 Hierarchical Clustering

**What it shows:**
- Dendrogram of metabolite relationships
- Groups based on temporal correlation
- Metabolic module identification

**How to use:**
1. Go to **🌳 Clustering** tab
2. Select metabolite group
3. View dendrogram
4. Identify clustered groups

**Interpretation:**
- **Low branches** = highly similar metabolites
- **Tree height** = dissimilarity measure
- **Clusters** = co-regulated metabolites
- **Separated branches** = independent regulation

**Biological insights:**
- Metabolites in same pathway cluster together
- Energy charge components (ATP/ADP/AMP) cluster
- Glycolysis intermediates form groups
- PPP metabolites separate from glycolysis

---

## Metabolite Preset Groups

### Glycolysis
`GLC, G6P, F6P, FBP, GAP, BPG13, PG3, PEP, PYR, LAC`

**Focus:** Main glucose breakdown pathway

### Energy
`ATP, ADP, AMP, NAD, NADH, NADP, NADPH`

**Focus:** Energy carriers and redox couples

### Pentose Phosphate Pathway (PPP)
`G6P, GL6P, PGNT6, RU5P, R5P, X5P, S7P, E4P`

**Focus:** NADPH production, ribose synthesis

### Nucleotides
`IMP, INO, HYP, XAN, ADE, GUA`

**Focus:** Purine metabolism and salvage

### Amino Acids
`GLY, SER, ALA, VAL, LEU, ILE`

**Focus:** Amino acid levels in RBCs

---

## Pathway Layout

The KEGG-style layout organizes metabolites spatially:

```
        [Glycolysis]          [PPP]           [Energy]
        (vertical)          (branching)      (stacked)
            |                   |                |
          GLC                 GL6P             ATP
            ↓                   ↓              ADP
          G6P ←─────────────┐ PGNT6           AMP
            ↓                 ↓
          F6P               RU5P
            ↓              /  |  \
          FBP           R5P X5P ...
          / \
       DHAP GAP
            ↓
         BPG13 → BPG23 (Rapoport-Luebering)
            ↓       ↓
          PG3 ←────┘
            ↓
          PG2
            ↓
          PEP
            ↓
          PYR
            ↓
          LAC
```

---

## Advanced Usage

### Custom Simulations

Run tailored simulations for visualization:

```python
# In sidebar
✓ Run New Simulation
  Simulation Time: 7 days
  Initial Conditions: Bordbar
  🚀 Run Simulation
```

### Data Export

Export visualized data for further analysis:

1. Navigate to **📊 3D Heatmap** tab
2. Select metabolites of interest
3. Click **💾 Download CSV**
4. Use in Excel, Python, R, etc.

### Combining with Other Modules

**Calibration → Visualization:**
1. Calibrate parameters in **🎯 Parameter Calibration**
2. Export optimized parameters
3. Run simulation with new parameters
4. Visualize in **🗺️ Pathway Visualization**

**Sensitivity → Visualization:**
1. Identify sensitive parameters in **📊 Sensitivity Analysis**
2. Perturb those parameters
3. Visualize impact on pathway dynamics

---

## Technical Details

### Network Graph Construction

- **Layout algorithm**: Manual KEGG-inspired positioning
- **Node sizing**: `size = 15 + min(concentration * 10, 50)`
- **Node coloring**: Gradient from blue (low) to red (high)
- **Edge styling**: Pathway-specific colors, arrows for irreversible

### Animation Performance

- **Frames**: Every Nth timepoint (configurable)
- **Duration**: 100ms per frame
- **Format**: Plotly frames with redraw
- **Optimization**: Reduced frame count for large datasets

### 3D Heatmap

- **Surface type**: Plotly `go.Surface`
- **Interpolation**: Linear between timepoints
- **Colorscale**: Viridis (perceptually uniform)
- **Resolution**: Based on simulation timepoints

### Clustering Algorithm

- **Method**: Hierarchical clustering (Ward linkage)
- **Distance metric**: Euclidean on time series
- **Dendrogram**: SciPy implementation
- **Visualization**: Plotly scatter lines

---

## Troubleshooting

### "No simulation data available"
→ Click **✓ Run New Simulation** in sidebar
→ Or wait for default simulation to load

### Visualization is slow
→ Reduce animation frame skip
→ Select fewer metabolites
→ Use shorter simulation time

### Metabolite not found in map
→ Check metabolite abbreviation
→ Some metabolites may not be in default layout
→ Use preset groups for guaranteed coverage

### Graph layout looks crowded
→ This is expected - RBC has 107 metabolites!
→ Focus on specific pathways using presets
→ Use zoom/pan controls

### 3D plot not rotating
→ Click and drag with mouse
→ Scroll to zoom
→ Use Plotly toolbar for reset

---

## Best Practices

### For Publication Figures

1. **Static map**: High resolution, clear labels
2. **Save as PNG/SVG** from Plotly toolbar
3. **Annotate** important metabolites separately
4. **Color scheme**: Ensure accessibility

### For Presentations

1. **Animated pathway**: Engaging, shows dynamics
2. **Slow animation** (frame skip = 1-2)
3. **Highlight** key metabolites beforehand
4. **Narrate** the metabolic flow

### For Analysis

1. **3D heatmap**: Pattern detection
2. **Clustering**: Module identification
3. **Export data**: Statistical analysis
4. **Combine views**: Comprehensive understanding

---

## Examples

### Example 1: Glycolytic Flux Under Stress

```
1. Run simulation with acidosis (pH 7.0)
2. Select "Glycolysis" preset
3. View animated pathway
4. Observe LAC accumulation
5. Check ATP/ADP ratio changes
```

### Example 2: PPP Activation

```
1. Run normal simulation
2. Select "PPP" preset
3. View 3D heatmap
4. Look for NADPH production pattern
5. Check R5P for nucleotide synthesis
```

### Example 3: Energy Depletion

```
1. Simulate long storage (42 days)
2. Select "Energy" preset
3. View animated pathway
4. Watch ATP decline
5. Check AMP rise (energy charge drop)
```

---

## Future Enhancements

Planned features:

- [ ] Escher integration for professional maps
- [ ] Custom pathway layout editor
- [ ] Flux overlay on pathway (arrow thickness = flux)
- [ ] Multi-condition comparison (side-by-side)
- [ ] Export to SBML/BioPAX formats
- [ ] VR/AR pathway exploration
- [ ] Real-time simulation + visualization
- [ ] Metabolite search and highlighting

---

## References

1. **KEGG Pathway Database**
   - https://www.genome.jp/kegg/pathway.html
   - Reference for pathway layouts

2. **Escher**
   - https://escher.github.io/
   - Professional metabolic map builder

3. **Bordbar et al. (2015)**
   - RBC model source
   - Cell Systems, 1(4), 283-292

4. **Plotly Graphing Library**
   - https://plotly.com/python/
   - Interactive visualization toolkit

---

## Support

For questions or issues:
- Check this guide first
- Review example workflows above
- Open GitHub issue
- Contact: jorge.veiga@example.com

---

**Enjoy exploring your RBC metabolic network! 🗺️**
