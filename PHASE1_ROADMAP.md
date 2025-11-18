# Phase 1 Implementation Roadmap
## RBC Metabolic Model - Advanced Features

**Timeline**: 1-2 weeks  
**Status**: In Progress 🚧

---

## 1️⃣ Data Upload Page ✅ COMPLETED
**Goal**: Allow users to upload custom experimental data

### Features Implemented
- ✅ CSV/Excel file upload
- ✅ Data validation and preview
- ✅ Interactive plotting of uploaded data
- ✅ Descriptive statistics display
- ✅ Column mapping to RBC metabolites (with auto-detection)
- ✅ Integration options (replace, supplement, validation only)
- ✅ Example data template
- ✅ **Auto-detection of transposed format** (NEW!)
- ✅ **Automatic data transposition** (NEW!)
- ✅ **Visual comparison of formats** (NEW!)

### Files Created
- `streamlit_app/pages/3_Data_Upload.py`
- `streamlit_app/core/data_preprocessor.py` - Format detection and transposition

### Key Features - Data Preprocessing
- **Format detection**: Auto-detects standard vs transposed format
- **Smart transposition**: Converts metabolites-in-rows → metabolites-in-columns
- **Visual feedback**: Shows before/after transformation
- **Confidence scoring**: Reports detection confidence
- **Validation**: Checks for missing values, non-numeric data, negative values

### Next Steps
- [ ] Integrate with simulation engine
- [ ] Add data preprocessing options (interpolation, smoothing)
- [ ] Support multiple file uploads

---

## 2️⃣ Auto-metabolite Mapping ✅ COMPLETED
**Goal**: Intelligent recognition of metabolite names

### Features Implemented
- ✅ Comprehensive synonym database (50+ metabolites, 200+ synonyms)
- ✅ Fuzzy string matching using SequenceMatcher
- ✅ Context-aware suggestions with confidence scores
- ✅ Auto-detection of time columns
- ✅ Pattern recognition (external/internal metabolites)
- ✅ Mapping quality indicators (exact, synonym, fuzzy)
- ✅ Export mapping template functionality

### Files Created
- ✅ `streamlit_app/core/metabolite_mapper.py` - Main mapping logic with MetaboliteMapper class
- ✅ `streamlit_app/data/metabolite_synonyms.json` - Comprehensive synonym database
- ✅ Integration in `streamlit_app/pages/3_Data_Upload.py`

### Key Features
- **Confidence scoring**: Exact (100%), Synonym (95%), Fuzzy (variable)
- **Smart suggestions**: Top 5 alternatives with scores
- **Batch mapping**: Process entire dataframes
- **Search functionality**: Find metabolites by name
- **Info retrieval**: Get metabolite descriptions and synonyms

---

## 3️⃣ Sensitivity Analysis ⏳ PLANNED
**Goal**: Understand parameter influence on model behavior

### Planned Features
- [ ] Parameter selection interface
- [ ] Range definition (min, max, steps)
- [ ] One-at-a-time (OAT) sensitivity
- [ ] Global sensitivity analysis (Sobol indices)
- [ ] Tornado plots visualization
- [ ] Heatmap of parameter interactions
- [ ] Export sensitivity results

### Files to Create
- `streamlit_app/pages/4_Sensitivity_Analysis.py` - Main page
- `streamlit_app/core/sensitivity.py` - Analysis engine

### Implementation Steps
1. Create parameter selection UI
2. Implement OAT sensitivity
3. Add visualization (tornado plots)
4. Implement Sobol sensitivity (advanced)
5. Add result export

---

## Integration Tasks

### Simulation Engine Updates
- [ ] Add support for custom uploaded data in `simulation_engine.py`
- [ ] Create data validation functions
- [ ] Handle missing metabolites gracefully
- [ ] Add data interpolation if time points don't match

### UI/UX Improvements
- [ ] Add progress indicators for long operations
- [ ] Improve error messages and user guidance
- [ ] Add tooltips and help text
- [ ] Create tutorial/walkthrough mode

---

## Testing & Validation

### Test Cases
- [ ] Upload various CSV formats
- [ ] Test with incomplete data
- [ ] Verify column mapping accuracy
- [ ] Test metabolite name recognition
- [ ] Validate sensitivity analysis results

### Performance
- [ ] Benchmark file upload sizes
- [ ] Optimize data processing
- [ ] Add caching where appropriate

---

## Documentation

- [ ] User guide for Data Upload
- [ ] Tutorial videos
- [ ] API documentation
- [ ] Example datasets repository

---

## Timeline

**Week 1**:
- ✅ Day 1-2: Data Upload Page (DONE)
- 🚧 Day 3-4: Auto-metabolite Mapping (IN PROGRESS)
- Day 5: Integration with simulation

**Week 2**:
- Day 1-3: Sensitivity Analysis implementation
- Day 4: Testing and refinement
- Day 5: Documentation and polish

---

## Success Metrics

- [ ] Users can upload and use custom data successfully
- [ ] >90% metabolite name recognition accuracy
- [ ] Sensitivity analysis runs in <30 seconds for typical parameters
- [ ] Zero critical bugs in production
- [ ] Positive user feedback

---

**Last Updated**: 2025-11-17  
**Next Review**: Check progress in 3 days
