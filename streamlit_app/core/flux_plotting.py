"""
Flux Visualization Module for Streamlit
========================================

Interactive Plotly visualizations for metabolic flux analysis.

Features:
- Interactive heatmap (click to view flux details)
- Flux distribution by pathway (initial, midpoint, final)
- Top 20 individual reactions
- Detailed flux analysis with substrates/products

Author: Jorgelindo da Veiga
Date: 2025-11-17
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from typing import Dict, List, Tuple
from reaction_info_complete import REACTION_INFO_COMPLETE
import streamlit as st


# Pathway groupings (same as CLI)
PATHWAY_GROUPS = {
    'Glycolysis': ['VHK', 'VPGI', 'VPFK', 'VFDPA', 'VTPI', 'VGAPDH', 
                   'VPGK', 'VPGM', 'VENOPGM', 'VPK', 'VLDH'],
    'Pentose_Phosphate': ['VG6PDH', 'VPGLS', 'V6PGD', 'VR5PI', 'VR5PE', 
                          'VTKL1', 'VTKL2', 'VTAL'],
    'Transport': ['VELAC', 'VEADE', 'VEINO', 'VEHYPX', 'VEMAL', 'VEGLC', 
                  'VEADO', 'VEPYR', 'VEGLN', 'VEGLU', 'VECYS', 'VEURT',
                  'VEXAN', 'VECIT', 'VEUREA', 'VEFUM', 'VEALA', 'VEMET',
                  'VEASP', 'VENH4', 'VECYT'],
    'Nucleotide': ['VAK', 'VAK2', 'VAPRT', 'VADA', 'VAMPD1', 'VHGPRT1', 
                   'VHGPRT2', 'VGMPS', 'VADSS', 'VIMPH', 'VPNPase1', 'VPRPPASE',
                   'VADSL', 'VRKa', 'VRKb', 'VXAO', 'VXAO2', 'VOPRIBT', 'Vnucleo2'],
    'Amino_Acid': ['VGLNS', 'VGDH', 'VASPTA', 'VALATA', 'VME', 'VPC', 'VACLY',
                   'VASTA', 'VCYSGLY', 'VGGCT', 'VMESE'],
    'Redox': ['VGSR', 'VGPX', 'VGLUCYS', 'VGSS', 'VGGT'],
    'BPG_Shunt': ['V23DPGP', 'VDPGM'],
    'Other': ['VFUM', 'VMLD', 'VH2O2']
}

# Use complete reaction info dictionary
REACTION_INFO = REACTION_INFO_COMPLETE


def create_flux_heatmap(flux_data: Dict, metabolite_results: Dict) -> go.Figure:
    """
    Create interactive heatmap of all fluxes over time.
    Grouped by pathway, clickable for detail view.
    
    Parameters:
    -----------
    flux_data : dict
        Dictionary with 'times', 'fluxes' (dict of reaction: [values])
    metabolite_results : dict
        Full simulation results (for detail view)
        
    Returns:
    --------
    go.Figure
        Plotly figure with interactive heatmap
    """
    times = np.array(flux_data['times'])
    fluxes = flux_data['fluxes']
    
    # Subsample time points to reduce data size (max 50 points)
    n_times = len(times)
    if n_times > 50:
        step = n_times // 50
        time_indices = np.arange(0, n_times, step)
        times_subsampled = times[time_indices]
    else:
        time_indices = np.arange(n_times)
        times_subsampled = times
    
    # Build flux matrix with all reactions
    all_reactions = list(fluxes.keys())
    flux_matrix_full = []
    for rxn in all_reactions:
        flux_values = np.array(fluxes[rxn])
        flux_matrix_full.append(flux_values[time_indices])
    
    flux_matrix_full = np.array(flux_matrix_full)
    
    # Select top reactions by variance (max 60 reactions)
    variances = np.var(flux_matrix_full, axis=1)
    top_indices = np.argsort(variances)[::-1][:60]
    
    # Organize selected reactions by pathway
    ordered_reactions = []
    pathway_boundaries = []
    current_idx = 0
    
    selected_reactions = [all_reactions[i] for i in top_indices]
    
    for pathway, reactions in PATHWAY_GROUPS.items():
        pathway_reactions = [r for r in reactions if r in selected_reactions]
        if pathway_reactions:
            ordered_reactions.extend(pathway_reactions)
            pathway_boundaries.append((current_idx, len(pathway_reactions), pathway))
            current_idx += len(pathway_reactions)
    
    # Build final flux matrix with ordered reactions
    flux_matrix = []
    for rxn in ordered_reactions:
        flux_values = np.array(fluxes[rxn])
        flux_matrix.append(flux_values[time_indices])
    
    flux_matrix = np.array(flux_matrix)
    
    # Normalize for visualization (z-scores)
    flux_normalized = np.zeros_like(flux_matrix)
    for i in range(flux_matrix.shape[0]):
        mean = np.mean(flux_matrix[i])
        std = np.std(flux_matrix[i])
        if std > 1e-10:
            flux_normalized[i] = (flux_matrix[i] - mean) / std
        else:
            flux_normalized[i] = flux_matrix[i]
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=flux_normalized,
        x=times_subsampled,
        y=ordered_reactions,
        colorscale='RdBu_r',
        zmid=0,
        zmin=-3,
        zmax=3,
        colorbar=dict(
            title=dict(
                text="Normalized<br>Flux (σ)",
                side="right"
            )
        ),
        hovertemplate='<b>%{y}</b><br>Time: %{x:.1f}h<br>Flux: %{z:.2f}σ<extra></extra>'
    ))
    
    # Add pathway separators and labels
    shapes = []
    annotations = []
    for start_idx, length, pathway in pathway_boundaries:
        # Add horizontal line separator
        if start_idx > 0:
            shapes.append(dict(
                type='line',
                x0=-0.5, x1=len(times_subsampled)-0.5,
                y0=start_idx - 0.5, y1=start_idx - 0.5,
                line=dict(color='black', width=2)
            ))
        
        # Add pathway label
        annotations.append(dict(
            x=-1,
            y=start_idx + length/2 - 0.5,
            text=f"<b>{pathway.replace('_', ' ')}</b>",
            showarrow=False,
            xref='x',
            yref='y',
            xanchor='right',
            font=dict(size=10, color='darkblue')
        ))
    
    fig.update_layout(
        title=dict(
            text=f'<b>Metabolic Flux Heatmap</b><br><sub>Top {len(ordered_reactions)} reactions by variance</sub>',
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(title='Time (hours)', side='bottom'),
        yaxis=dict(title='', tickfont=dict(size=9)),
        height=max(600, len(ordered_reactions) * 15),
        margin=dict(l=150, r=100, t=80, b=60),
        shapes=shapes,
        annotations=annotations,
        hovermode='closest'
    )
    
    return fig


def create_flux_distribution_combined(flux_data: Dict, timepoint: str) -> go.Figure:
    """
    Create combined figure with pathway flux distribution + top 20 individual reactions.
    Matches CLI visualization style.
    
    Parameters:
    -----------
    flux_data : dict
        Dictionary with 'times', 'fluxes'
    timepoint : str
        'initial', 'midpoint', or 'final'
        
    Returns:
    --------
    go.Figure
        Combined Plotly figure
    """
    times = np.array(flux_data['times'])
    fluxes = flux_data['fluxes']
    
    # Determine time index
    if timepoint == 'initial':
        t_idx = 0
        time_val = times[0]
    elif timepoint == 'midpoint':
        t_idx = len(times) // 2
        time_val = times[t_idx]
    else:  # final
        t_idx = -1
        time_val = times[-1]
    
    # Calculate pathway fluxes
    pathway_fluxes = {}
    for pathway, reactions in PATHWAY_GROUPS.items():
        total = 0.0
        for rxn in reactions:
            if rxn in fluxes and len(fluxes[rxn]) > abs(t_idx):
                total += abs(fluxes[rxn][t_idx])
        if total > 0:
            pathway_fluxes[pathway] = total
    
    # Get top 20 individual reactions
    individual_fluxes = {}
    for rxn, values in fluxes.items():
        if len(values) > abs(t_idx):
            individual_fluxes[rxn] = abs(values[t_idx])
    
    top_20 = sorted(individual_fluxes.items(), key=lambda x: x[1], reverse=True)[:20]
    
    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            f'<b>Pathway Flux Distribution</b><br><sub>t = {time_val:.1f}h</sub>',
            f'<b>Top 20 Individual Reactions</b><br><sub>t = {time_val:.1f}h</sub>'
        ),
        horizontal_spacing=0.15
    )
    
    # Left plot: Pathway distribution
    pathways = list(pathway_fluxes.keys())
    pathway_values = [pathway_fluxes[p] for p in pathways]
    colors_pathway = px.colors.qualitative.Set2[:len(pathways)]
    
    fig.add_trace(
        go.Bar(
            y=pathways,
            x=pathway_values,
            orientation='h',
            marker=dict(color=colors_pathway),
            text=[f'{v:.3f}' for v in pathway_values],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Total Flux: %{x:.4f} mM/h<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Right plot: Top 20 reactions
    rxn_names = [rxn for rxn, _ in top_20]
    rxn_values = [val for _, val in top_20]
    colors_rxn = ['#FF6B6B' if val > np.median(rxn_values) else '#4ECDC4' for val in rxn_values]
    
    fig.add_trace(
        go.Bar(
            y=rxn_names,
            x=rxn_values,
            orientation='h',
            marker=dict(color=colors_rxn),
            text=[f'{v:.3f}' for v in rxn_values],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Flux: %{x:.4f} mM/h<extra></extra>'
        ),
        row=1, col=2
    )
    
    # Update layout
    fig.update_xaxes(title_text="Total Flux (mM/h)", row=1, col=1)
    fig.update_xaxes(title_text="Flux (mM/h)", row=1, col=2)
    fig.update_yaxes(title_text="Pathway", tickfont=dict(size=10), row=1, col=1)
    fig.update_yaxes(title_text="Reaction", tickfont=dict(size=9), row=1, col=2)
    
    fig.update_layout(
        title=dict(
            text=f'<b>Flux Distribution Analysis</b> - {timepoint.capitalize()} Timepoint',
            x=0.5,
            xanchor='center'
        ),
        height=600,
        showlegend=False,
        margin=dict(l=150, r=100, t=100, b=60)
    )
    
    return fig


def create_flux_detail_view(reaction_name: str, flux_data: Dict, 
                            metabolite_results: Dict) -> go.Figure:
    """
    Create detailed analysis view for a specific flux.
    Shows flux + substrate/product concentrations + kinetic parameters.
    
    Parameters:
    -----------
    reaction_name : str
        Name of reaction (e.g., 'VHK')
    flux_data : dict
        Dictionary with 'times', 'fluxes'
    metabolite_results : dict
        Full simulation results with metabolite concentrations and simulation times
        
    Returns:
    --------
    go.Figure
        Detailed analysis figure
    """
    flux_times = np.array(flux_data['times'])
    flux_values = np.array(flux_data['fluxes'][reaction_name])
    
    # Use full simulation times for metabolite concentrations
    # Flux tracking may have fewer points than full simulation
    sim_times = metabolite_results.get('sim_times', flux_times)  # Fallback to flux times if not available
    
    # Get reaction info
    rxn_info = REACTION_INFO.get(reaction_name, {
        'name': reaction_name,
        'reaction': 'Unknown',
        'substrates': [],
        'products': []
    })
    
    # Create 2x2 grid layout
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Substrate Concentrations',
            'Product Concentrations',
            f'<b>{rxn_info["name"]}</b> Flux',
            'Flux Statistics'
        ),
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "table"}]],
        vertical_spacing=0.12,
        horizontal_spacing=0.12
    )
    
    # Plot 1: Substrates (if available in metabolite_results)
    if 'metabolite_names' in metabolite_results and 'concentrations' in metabolite_results:
        met_names = metabolite_results['metabolite_names']
        concentrations = metabolite_results['concentrations']
        
        for substrate in rxn_info.get('substrates', []):
            if substrate in met_names:
                idx = met_names.index(substrate)
                fig.add_trace(
                    go.Scatter(
                        x=sim_times,  # Use simulation times, not flux times
                        y=concentrations[:, idx],
                        mode='lines',
                        name=substrate,
                        line=dict(width=2),
                        hovertemplate=f'<b>{substrate}</b><br>Time: %{{x:.1f}}h<br>[C]: %{{y:.4f}} mM<extra></extra>'
                    ),
                    row=1, col=1
                )
        
        # Plot 2: Products (top-right)
        for product in rxn_info.get('products', []):
            if product in met_names:
                idx = met_names.index(product)
                fig.add_trace(
                    go.Scatter(
                        x=sim_times,  # Use simulation times, not flux times
                        y=concentrations[:, idx],
                        mode='lines',
                        name=product,
                        line=dict(width=2, dash='dot'),
                        hovertemplate=f'<b>{product}</b><br>Time: %{{x:.1f}}h<br>[C]: %{{y:.4f}} mM<extra></extra>'
                    ),
                    row=1, col=2
                )
    
    # Plot 3: Flux over time (bottom-left)
    fig.add_trace(
        go.Scatter(
            x=flux_times,  # Use flux tracking times
            y=flux_values,
            mode='lines',
            line=dict(color='#FF6B6B', width=3),
            name='Flux',
            fill='tozeroy',
            fillcolor='rgba(255, 107, 107, 0.2)',
            hovertemplate='Time: %{x:.1f}h<br>Flux: %{y:.4f} mM/h<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add mean line
    mean_flux = np.mean(flux_values)
    fig.add_hline(
        y=mean_flux,
        line=dict(color='red', dash='dash', width=2),
        annotation_text=f'Mean: {mean_flux:.4f}',
        row=2, col=1
    )
    
    # Plot 4: Statistics table (bottom-right)
    stats = [
        ['Mean Flux', f'{np.mean(flux_values):.6f} mM/h'],
        ['Std Dev', f'{np.std(flux_values):.6f} mM/h'],
        ['Max Flux', f'{np.max(flux_values):.6f} mM/h'],
        ['Min Flux', f'{np.min(flux_values):.6f} mM/h'],
        ['Max Time', f'{flux_times[np.argmax(flux_values)]:.2f} h'],
        ['Min Time', f'{flux_times[np.argmin(flux_values)]:.2f} h'],
    ]
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=['<b>Metric</b>', '<b>Value</b>'],
                fill_color='lightblue',
                align='left',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=[[s[0] for s in stats], [s[1] for s in stats]],
                fill_color='lavender',
                align='left',
                font=dict(size=11)
            )
        ),
        row=2, col=2
    )
    
    # Update axes
    fig.update_xaxes(title_text="Time (hours)", row=1, col=1)
    fig.update_yaxes(title_text="Concentration (mM)", row=1, col=1)
    fig.update_xaxes(title_text="Time (hours)", row=1, col=2)
    fig.update_yaxes(title_text="Concentration (mM)", row=1, col=2)
    fig.update_xaxes(title_text="Time (hours)", row=2, col=1)
    fig.update_yaxes(title_text="Flux (mM/h)", row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=f'<b>{reaction_name} - {rxn_info["name"]}</b><br><sub>{rxn_info["reaction"]}</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        height=800,
        showlegend=True,
        legend=dict(x=1.02, y=0.5),
        margin=dict(l=80, r=150, t=120, b=60)
    )
    
    return fig


def export_flux_data_csv(flux_data: Dict) -> str:
    """
    Convert flux data to CSV format for download.
    
    Parameters:
    -----------
    flux_data : dict
        Dictionary with 'times', 'fluxes'
        
    Returns:
    --------
    str
        CSV string
    """
    df_data = {'Time_hours': flux_data['times']}
    df_data.update(flux_data['fluxes'])
    df = pd.DataFrame(df_data)
    return df.to_csv(index=False)
