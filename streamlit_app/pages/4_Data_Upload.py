"""
Data Upload Page
================

Upload custom experimental data for RBC metabolic simulations.

Features:
- CSV/Excel file upload
- Data validation and preview
- Column mapping to metabolites
- Integration with simulation engine

Author: Jorgelindo da Veiga
Date: 2025-11-17
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Dict, List, Optional
import io
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from core.metabolite_mapper import MetaboliteMapper
from core.data_preprocessor import DataPreprocessor
from core.auth import init_session_state, check_page_auth
from core.styles import apply_global_styles

# Page configuration
st.set_page_config(
    page_title="Data Upload - RBC Model",
    page_icon="📤",
    layout="wide"
)

# Apply global styles
apply_global_styles()

# Initialize and check authentication
init_session_state()
if not check_page_auth():
    st.stop()

# Title
st.title("📤 Data Upload & Management")
st.markdown("*Upload your experimental data to use in simulations*")

# Instructions
with st.expander("💡 How to Use This Page", expanded=False):
    st.markdown("""
    ### Upload Process
    1. **Prepare Your Data**: CSV or Excel file with time series data
    2. **Upload File**: Use the upload button below
    3. **Preview & Validate**: Check that data is correctly loaded
    4. **Map Columns**: Associate columns with metabolites
    5. **Save**: Data will be available in simulations
    
    ### Data Format Requirements
    - **Time column**: Required (in days)
    - **Metabolite columns**: At least one metabolite concentration
    - **Units**: mM (millimolar) for concentrations
    - **Format**: Numeric values only (no text in data cells)
    
    ### Example Format
    ```
    Time_days, GLC, LAC, ATP, ADP, B23PG
    0.0, 5.0, 2.0, 2.5, 0.8, 4.5
    0.5, 4.8, 2.2, 2.4, 0.9, 4.6
    1.0, 4.5, 2.5, 2.3, 1.0, 4.7
    ```
    """)

st.markdown("---")

# Main upload section
st.header("📁 Upload Experimental Data")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload a file containing time series metabolite data"
    )

with col2:
    if uploaded_file is not None:
        file_details = {
            "Filename": uploaded_file.name,
            "File size": f"{uploaded_file.size / 1024:.2f} KB",
            "File type": uploaded_file.type
        }
        st.json(file_details)

# Process uploaded file
if uploaded_file is not None:
    try:
        # Read file based on type
        if uploaded_file.name.endswith('.csv'):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)
        
        st.success(f"✅ File loaded successfully! Found {len(df_raw)} rows and {len(df_raw.columns)} columns")
        
        # Auto-detect and preprocess data format
        preprocessor = DataPreprocessor()
        format_info = preprocessor.detect_format(df_raw)
        
        # Show format detection
        if format_info['needs_transpose']:
            st.info(f"🔄 **Auto-detected transposed format** (confidence: {format_info['confidence']:.0%})")
            st.caption("Data will be transposed: metabolites in rows → metabolites in columns")
            
            # Process data
            df, metadata = preprocessor.auto_process(df_raw)
            
            # Show transformation
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original format (first 5 rows, 5 cols):**")
                st.code(df_raw.iloc[:5, :5].to_string(), language="text")
            with col2:
                st.markdown("**Transformed format (first 5 rows):**")
                st.code(df.head(5).to_string(), language="text")
        else:
            st.success(f"✅ **Standard format detected** (confidence: {format_info['confidence']:.0%})")
            df = df_raw.copy()
        
        # Store both in session state
        st.session_state['uploaded_data_raw'] = df_raw
        st.session_state['uploaded_data'] = df
        st.session_state['uploaded_filename'] = uploaded_file.name
        
        # Data preview section
        st.markdown("---")
        st.header("👀 Data Preview")
        
        tab1, tab2, tab3 = st.tabs(["📊 Data Table", "📈 Quick Plots", "🔍 Statistics"])
        
        with tab1:
            st.markdown("### First 10 rows")
            st.dataframe(df.head(10), width="stretch")
            
            st.markdown("### Last 10 rows")
            st.dataframe(df.tail(10), width="stretch")
            
            # Download processed data
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            st.download_button(
                label="📥 Download Preview as CSV",
                data=csv_buffer.getvalue(),
                file_name=f"preview_{uploaded_file.name}",
                mime="text/csv"
            )
        
        with tab2:
            st.markdown("### Select columns to plot")
            
            # Identify potential time column
            time_columns = [col for col in df.columns if 'time' in col.lower() or 'hour' in col.lower() or 'day' in col.lower()]
            
            if time_columns:
                time_col = st.selectbox("Time column:", time_columns, index=0)
            else:
                time_col = st.selectbox("Time column:", df.columns)
            
            # Select metabolite columns to plot
            other_cols = [col for col in df.columns if col != time_col]
            selected_cols = st.multiselect(
                "Select metabolites to plot:",
                other_cols,
                default=other_cols[:5] if len(other_cols) >= 5 else other_cols
            )
            
            if selected_cols:
                fig = go.Figure()
                for col in selected_cols:
                    fig.add_trace(go.Scatter(
                        x=df[time_col],
                        y=df[col],
                        mode='lines+markers',
                        name=col
                    ))
                
                fig.update_layout(
                    title="Metabolite Concentrations Over Time",
                    xaxis_title=time_col,
                    yaxis_title="Concentration (mM)",
                    hovermode='x unified',
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.markdown("### Descriptive Statistics")
            st.dataframe(df.describe(), width="stretch")
            
            st.markdown("### Data Types")
            dtype_df = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.astype(str),
                'Non-Null Count': df.count(),
                'Null Count': df.isnull().sum()
            })
            st.dataframe(dtype_df, width="stretch")
        
        # Column mapping section with intelligent mapper
        st.markdown("---")
        st.header("🗺️ Intelligent Column Mapping")
        st.caption("🤖 AI-powered mapping using synonym database and fuzzy matching")
        
        # Initialize mapper
        mapper = MetaboliteMapper()
        rbc_metabolites = mapper.get_all_metabolites()
        
        # Auto-map columns
        with st.spinner("🔍 Analyzing columns with AI mapper..."):
            auto_mappings = mapper.map_dataframe_columns(df.columns.tolist(), threshold=0.7)
        
        # Show mapping confidence summary
        confidence_col1, confidence_col2, confidence_col3, confidence_col4 = st.columns(4)
        
        exact_matches = sum(1 for m in auto_mappings.values() if m['method'] == 'exact')
        synonym_matches = sum(1 for m in auto_mappings.values() if m['method'] == 'synonym')
        fuzzy_matches = sum(1 for m in auto_mappings.values() if m['method'] == 'fuzzy')
        no_matches = sum(1 for m in auto_mappings.values() if not m['matched'] and m['method'] != 'time_column')
        
        with confidence_col1:
            st.metric("✅ Exact Matches", exact_matches)
        with confidence_col2:
            st.metric("🎯 Synonym Matches", synonym_matches)
        with confidence_col3:
            st.metric("🔍 Fuzzy Matches", fuzzy_matches)
        with confidence_col4:
            st.metric("❓ Unmapped", no_matches)
        
        # Identify time column
        st.subheader("1️⃣ Time Column")
        time_candidates = [col for col, m in auto_mappings.items() if m['method'] == 'time_column']
        
        if time_candidates:
            default_time = time_candidates[0]
        elif time_columns:
            default_time = time_columns[0]
        else:
            default_time = df.columns[0]
        
        time_col_mapped = st.selectbox(
            "Select the column containing time values:",
            df.columns,
            index=df.columns.tolist().index(default_time) if default_time in df.columns else 0,
            key='time_mapping'
        )
        
        # Map metabolite columns with AI suggestions
        st.subheader("2️⃣ Metabolite Columns (AI-Assisted)")
        st.markdown("*Review and adjust AI-suggested mappings below*")
        
        # Add mapping confidence filter
        show_filter = st.checkbox("🔧 Show advanced filters", value=False)
        if show_filter:
            min_confidence = st.slider(
                "Minimum confidence threshold:",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.05,
                help="Only show auto-mappings above this confidence level"
            )
        else:
            min_confidence = 0.7
        
        # Create mapping interface
        metabolite_mappings = {}
        
        # Separate columns by mapping quality for better UX
        mapped_cols = []
        uncertain_cols = []
        
        for col in df.columns:
            if col == time_col_mapped:
                continue
            
            mapping = auto_mappings.get(col, {})
            if mapping.get('matched') and mapping.get('confidence', 0) >= min_confidence:
                mapped_cols.append((col, mapping))
            else:
                uncertain_cols.append((col, mapping))
        
        # Show successfully mapped columns
        if mapped_cols:
            with st.expander(f"✅ Auto-Mapped Columns ({len(mapped_cols)})", expanded=True):
                map_col1, map_col2 = st.columns(2)
                
                for idx, (col, mapping) in enumerate(mapped_cols):
                    with map_col1 if idx % 2 == 0 else map_col2:
                        # Show confidence badge
                        method_emoji = {
                            'exact': '🎯',
                            'synonym': '📚',
                            'fuzzy': '🔍'
                        }.get(mapping['method'], '❓')
                        
                        st.markdown(f"**{col}** {method_emoji}")
                        
                        # Get metabolite info for tooltip
                        met_info = mapper.get_metabolite_info(mapping['metabolite'])
                        full_name = met_info.get('full_name', mapping['metabolite']) if met_info else mapping['metabolite']
                        
                        selected_met = st.selectbox(
                            f"→ {full_name}",
                            ['(skip)'] + rbc_metabolites,
                            index=rbc_metabolites.index(mapping['metabolite']) + 1,
                            key=f'map_{col}',
                            help=f"Confidence: {mapping['confidence']:.1%} | Method: {mapping['method']}"
                        )
                        
                        if selected_met != '(skip)':
                            metabolite_mappings[selected_met] = col
        
        # Show uncertain/unmapped columns with suggestions
        if uncertain_cols:
            with st.expander(f"❓ Uncertain Mappings ({len(uncertain_cols)})", expanded=False):
                st.markdown("*These columns need manual review or had low confidence matches*")
                
                map_col1, map_col2 = st.columns(2)
                
                for idx, (col, mapping) in enumerate(uncertain_cols):
                    with map_col1 if idx % 2 == 0 else map_col2:
                        st.markdown(f"**{col}**")
                        
                        # Get suggestions
                        suggestions = mapper.suggest_corrections(col, max_suggestions=3)
                        
                        if suggestions:
                            suggestion_text = " | ".join([f"{m} ({c:.0%})" for m, c, _ in suggestions[:3]])
                            st.caption(f"💡 Suggestions: {suggestion_text}")
                        
                        # Default selection
                        if mapping.get('matched'):
                            default_idx = rbc_metabolites.index(mapping['metabolite']) + 1
                        else:
                            default_idx = 0
                        
                        selected_met = st.selectbox(
                            "Select metabolite:",
                            ['(skip)'] + rbc_metabolites,
                            index=default_idx,
                            key=f'map_uncertain_{col}'
                        )
                        
                        if selected_met != '(skip)':
                            metabolite_mappings[selected_met] = col
        
        # Save mapping
        if st.button("💾 Save Column Mapping", type="primary"):
            if metabolite_mappings:
                st.session_state['column_mapping'] = {
                    'time_column': time_col_mapped,
                    'metabolites': metabolite_mappings
                }
                st.success(f"✅ Mapping saved! {len(metabolite_mappings)} metabolites mapped.")
                
                # Show mapping summary
                st.markdown("### Mapping Summary")
                mapping_df = pd.DataFrame([
                    {'Model Metabolite': met, 'Data Column': col}
                    for met, col in metabolite_mappings.items()
                ])
                st.dataframe(mapping_df, width="stretch")
            else:
                st.warning("⚠️ No metabolites mapped. Please map at least one metabolite column.")
        
        # Integration options
        st.markdown("---")
        st.header("⚙️ Integration Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_mode = st.radio(
                "How should this data be used?",
                [
                    "Replace experimental data",
                    "Supplement existing data",
                    "Use for validation only"
                ]
            )
        
        with col2:
            if use_mode == "Replace experimental data":
                st.info("📝 All existing experimental data will be replaced with uploaded data")
            elif use_mode == "Supplement existing data":
                st.info("📝 Uploaded data will be merged with existing experimental data")
            else:
                st.info("📝 Uploaded data will only be used for comparison/validation")
        
        if st.button("✅ Apply Data to Simulations", type="primary"):
            # Transform data to match expected format
            if 'column_mapping' in st.session_state:
                mapping = st.session_state['column_mapping']
                time_col = mapping.get('time_column')
                met_mapping = mapping.get('metabolites', {})
                
                # Create transformed dataframe
                transformed_df = pd.DataFrame()
                
                # Add time column
                if time_col and time_col in df.columns:
                    transformed_df['Time'] = df[time_col]
                else:
                    transformed_df['Time'] = df.iloc[:, 0]  # Use first column as time
                
                # Add metabolite columns with model names
                for model_met, data_col in met_mapping.items():
                    if data_col in df.columns:
                        transformed_df[model_met] = df[data_col]
                
                # Store transformed data
                st.session_state['uploaded_data'] = transformed_df
                st.session_state['uploaded_data_active'] = True
                st.session_state['uploaded_data_mode'] = use_mode
                
                st.success(f"""
                ✅ **Data configuration saved!** 
                - {len(transformed_df)} timepoints
                - {len(met_mapping)} metabolites mapped
                - Mode: {use_mode}
                """)
                st.info("👉 Go to the **Simulation** page to run a simulation with your custom data.")
                
                # Show preview of transformed data
                with st.expander("🔍 Preview Transformed Data"):
                    st.dataframe(transformed_df.head(), width="stretch")
            else:
                st.error("❌ Please save column mapping first!")

    
    except Exception as e:
        st.error(f"❌ Error loading file: {str(e)}")
        st.info("Please check that your file format matches the requirements above.")

else:
    st.info("👆 Upload a file to get started")
    
    # Show example data format
    st.markdown("---")
    st.header("📋 Example Data Format")
    
    example_data = pd.DataFrame({
        'Time_days': [0.0, 0.5, 1.0, 2.0, 4.0, 8.0],
        'GLC': [5.0, 4.8, 4.5, 4.0, 3.2, 2.5],
        'LAC': [2.0, 2.2, 2.5, 3.0, 4.5, 6.0],
        'ATP': [2.5, 2.4, 2.3, 2.2, 2.0, 1.8],
        'ADP': [0.8, 0.9, 1.0, 1.1, 1.3, 1.5],
        'B23PG': [4.5, 4.6, 4.7, 4.8, 5.0, 5.2]
    })
    
    # Display as markdown table (workaround for pyarrow issues)
    st.markdown("**Example Data Format:**")
    st.code(example_data.to_string(index=False), language="text")
    
    # Download example
    csv_buffer = io.StringIO()
    example_data.to_csv(csv_buffer, index=False)
    st.download_button(
        label="📥 Download Example CSV",
        data=csv_buffer.getvalue(),
        file_name="example_rbc_data.csv",
        mime="text/csv"
    )

# Footer with current data status
st.markdown("---")
st.markdown("### 📊 Current Data Status")

if 'uploaded_data' in st.session_state and st.session_state.get('uploaded_data_active', False):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📁 Active File", st.session_state.get('uploaded_filename', 'N/A'))
    with col2:
        st.metric("🔢 Data Points", len(st.session_state['uploaded_data']))
    with col3:
        mode = st.session_state.get('uploaded_data_mode', 'N/A')
        st.metric("⚙️ Mode", mode)
else:
    st.info("No custom data currently active. Using default experimental data.")
