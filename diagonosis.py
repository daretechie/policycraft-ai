import sys
import os
import traceback
from typing import TypedDict, Any, Tuple
from datetime import datetime, timedelta

from dash import callback, html, dcc, Output, Input
import dash_design_kit as ddk
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from data import get_data
from components.filter_component import filter_data, FILTER_CALLBACK_INPUTS
from logger import logger

class TestInput(TypedDict):
    options: list[Any]
    default: Any

class ComponentResponse(TypedDict):
    layout: ddk.Card
    test_inputs: dict[str, TestInput]

component_id = "add_an_ai_narrative_text_box"

country_control_id = f"{component_id}_country"

def component() -> ComponentResponse:
    graph_id = f"{component_id}_graph"
    error_id = f"{component_id}_error"
    loading_id = f"{component_id}_loading"
    narrative_id = f"{component_id}_narrative"

    df = get_data()
    country_options = [{"label": country, "value": country} for country in sorted(df['country'].unique())]
    country_default = "Finland"

    title = "💡 Country Wellbeing Diagnostic"
    description = "Interactive analysis showing country performance gaps and AI-generated policy insights"

    layout = ddk.Card(
        id=component_id,
        children=[
            ddk.CardHeader(title=title),
            html.Div(
                style={"display": "flex", "flexDirection": "row", "flexWrap": "wrap", "rowGap": "10px", "alignItems": "center", "marginBottom": "15px"},
                children=[
                    html.Div(
                        children=[
                            html.Label("Select Country:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=country_control_id,
                                options=country_options,
                                value=country_default,
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px"}
                    ),
                ],
            ),
            dcc.Loading(
                id=loading_id,
                type="circle",
                children=[
                    ddk.Graph(id=graph_id),
                ]
            ),
            html.Div(
                id=narrative_id,
                style={
                    "backgroundColor": "#f8f9fa",
                    "border": "1px solid #dee2e6",
                    "borderRadius": "8px",
                    "padding": "20px",
                    "margin": "20px 0",
                    "fontFamily": "Arial, sans-serif"
                }
            ),
            html.Pre(id=error_id, style={"color": "red", "margin": "10px 0"}),
            ddk.CardFooter(title=description)
        ],
        width=100
    )

    test_inputs: dict[str, TestInput] = {
        country_control_id: {
            "options": [option["value"] for option in country_options],
            "default": country_default
        }
    }

    return {
        "layout": layout,
        "test_inputs": test_inputs
    }

def _update_logic(**kwargs) -> Tuple[go.Figure, str]:
    """Core chart update logic without error handling."""
    df = filter_data(get_data(), **kwargs)
    if len(df) == 0:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{
                "text": "No data available",
                "showarrow": False,
                "font": {"size": 20}
            }]
        )
        return empty_fig, "No data available for analysis."

    selected_country = kwargs.get(country_control_id, "Finland")
    if selected_country is None:
        selected_country = "Finland"

    country_data = df[df['country'] == selected_country]
    if len(country_data) == 0:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{
                "text": f"No data available for {selected_country}",
                "showarrow": False,
                "font": {"size": 20}
            }]
        )
        return empty_fig, f"No data available for {selected_country}."

    logger.debug("Starting chart creation for country: %s", selected_country)

    gap_columns = [
        'life_satisfaction_gap', 'health_gap', 'income_gap', 'education_gap',
        'jobs_gap', 'work_life_balance_gap', 'safety_gap', 'environment_gap',
        'social_connections_gap', 'housing_gap'
    ]

    dimension_names = {
        'life_satisfaction_gap': 'Life Satisfaction',
        'health_gap': 'Health',
        'income_gap': 'Income',
        'education_gap': 'Education',
        'jobs_gap': 'Jobs',
        'work_life_balance_gap': 'Work-Life Balance',
        'safety_gap': 'Safety',
        'environment_gap': 'Environment',
        'social_connections_gap': 'Social Connections',
        'housing_gap': 'Housing'
    }

    gap_values = []
    dimension_labels = []
    colors = []

    for gap_col in gap_columns:
        if gap_col in country_data.columns:
            gap_value = country_data[gap_col].iloc[0]
            gap_values.append(gap_value)
            dimension_labels.append(dimension_names[gap_col])
            colors.append('#2E8B57' if gap_value >= 0 else '#DC143C')

    fig = go.Figure(data=[
        go.Bar(
            x=gap_values,
            y=dimension_labels,
            orientation='h',
            marker_color=colors,
            text=[f"{val:+.1f}" for val in gap_values],
            textposition='outside'
        )
    ])

    fig.update_layout(
        xaxis_title="Performance Gap (points above/below OECD average)",
        yaxis_title="Wellbeing Dimensions",
        height=500,
        margin={"l": 150, "r": 50, "t": 50, "b": 50}
    )

    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.7)

    # Generate AI narrative
    narrative = _generate_narrative(selected_country, gap_values, dimension_labels, df)

    return fig, narrative

def _generate_narrative(country, gap_values, dimension_labels, df):
    """Generate AI-powered diagnostic narrative."""
    
    # Create dimension-gap pairs and sort
    dimension_gaps = list(zip(dimension_labels, gap_values))
    dimension_gaps.sort(key=lambda x: x[1], reverse=True)
    
    # Get top 2 strengths (highest positive gaps) and top 2 weaknesses (lowest negative gaps)
    strengths = [d for d in dimension_gaps if d[1] > 0][:2]
    weaknesses = [d for d in dimension_gaps if d[1] < 0][-2:]
    
    # Find top performer for policy insight
    composite_scores = df.groupby('country')['composite_index'].first().sort_values(ascending=False)
    top_performer = composite_scores.index[0]
    
    # Determine worst performing dimension for policy recommendation
    worst_dimension = dimension_gaps[-1][0] if dimension_gaps else "overall wellbeing"
    
    narrative_parts = []
    
    # Header
    narrative_parts.append(f"## 🏛️ OECD Wellbeing Diagnostic: {country}")
    narrative_parts.append("---")
    
    # Strengths section
    if strengths:
        narrative_parts.append("### 💪 **Key Strengths**")
        for dim, gap in strengths:
            narrative_parts.append(f"• **{dim}**: {gap:+.1f} points above OECD average")
        narrative_parts.append("")
        
        strength_text = f"{country} demonstrates notable excellence in {strengths[0][0].lower()}"
        if len(strengths) > 1:
            strength_text += f" and {strengths[1][0].lower()}"
        strength_text += f". These positive performance gaps indicate that {country}'s citizens experience significantly better outcomes in these dimensions compared to the typical OECD country."
        narrative_parts.append(strength_text)
    else:
        narrative_parts.append("### 💪 **Key Strengths**")
        narrative_parts.append(f"• {country} is performing at or below OECD average across most dimensions")
        narrative_parts.append("")
        narrative_parts.append(f"While {country} faces challenges across multiple wellbeing dimensions, this presents clear opportunities for targeted policy interventions to improve citizen outcomes.")
    
    narrative_parts.append("")
    
    # Weaknesses section
    if weaknesses:
        narrative_parts.append("### ⚠️ **Critical Areas for Improvement**")
        for dim, gap in weaknesses:
            narrative_parts.append(f"• **{dim}**: {gap:+.1f} points below OECD average")
        narrative_parts.append("")
        
        weakness_text = f"The data reveals significant challenges in {weaknesses[-1][0].lower()}"
        if len(weaknesses) > 1:
            weakness_text += f" and {weaknesses[-2][0].lower()}"
        weakness_text += f". These negative gaps suggest that {country}'s performance in these areas falls notably short of what citizens in other OECD countries typically experience."
        narrative_parts.append(weakness_text)
    else:
        narrative_parts.append("### ⚠️ **Areas for Attention**")
        narrative_parts.append(f"• {country} shows relatively balanced performance across dimensions")
        narrative_parts.append("")
        narrative_parts.append(f"{country} maintains consistent performance across wellbeing dimensions, though there may still be opportunities for enhancement in specific areas.")
    
    narrative_parts.append("")
    
    # Policy insight
    narrative_parts.append("### 🎯 **Policy Insight**")
    if weaknesses:
        policy_text = f"**Recommendation**: Prioritizing improvements in {worst_dimension.lower()} could significantly enhance {country}'s overall wellbeing performance and bring outcomes closer to leading countries like {top_performer}."
    else:
        policy_text = f"**Recommendation**: {country} should focus on maintaining its current performance levels while identifying emerging opportunities to further enhance citizen wellbeing outcomes."
    
    narrative_parts.append(policy_text)
    
    return "\n".join(narrative_parts)

@callback(
    output=[
        Output(f"{component_id}_graph", "figure"),
        Output(f"{component_id}_narrative", "children"),
        Output(f"{component_id}_error", "children")
    ],
    inputs={
        country_control_id: Input(country_control_id, "value"),
        **FILTER_CALLBACK_INPUTS
    }
)
def update(**kwargs) -> Tuple[go.Figure, str, str]:
    empty_fig = go.Figure()
    empty_fig.update_layout(
        annotations=[{"text": "An error occurred while updating this chart", "showarrow": False, "font": {"size": 20}}]
    )

    try:
        figure, narrative = _update_logic(**kwargs)
        
        # Convert narrative to Dash components
        narrative_component = dcc.Markdown(
            narrative,
            style={
                "lineHeight": "1.6",
                "fontSize": "14px"
            }
        )
        
        return figure, narrative_component, ""

    except Exception as e:
        error_msg = f"Error updating chart: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return empty_fig, "Error generating narrative.", error_msg