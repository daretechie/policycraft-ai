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

component_id = "produce_an_ai_narrative_text"

country_control_id = f"{component_id}_country"
dimension_control_id = f"{component_id}_dimension"
improvement_control_id = f"{component_id}_improvement"

def component() -> ComponentResponse:
    graph_id = f"{component_id}_graph"
    error_id = f"{component_id}_error"
    loading_id = f"{component_id}_loading"
    narrative_id = f"{component_id}_narrative"

    df = get_data()
    
    country_options = [{"label": country, "value": country} for country in sorted(df['country'].unique())]
    country_default = "United States"
    
    dimension_options = [
        {"label": "Environment", "value": "environment"},
        {"label": "Education", "value": "education"},
        {"label": "Jobs", "value": "jobs"},
        {"label": "Safety", "value": "safety"},
        {"label": "Income", "value": "income"},
        {"label": "Housing", "value": "housing"},
        {"label": "Health", "value": "health"},
        {"label": "Work-Life Balance", "value": "work_life_balance"},
        {"label": "Social Connections", "value": "social_connections"}
    ]
    dimension_default = "environment"
    
    improvement_marks = {
        int(5): "5",
        int(10): "10",
        int(15): "15",
        int(20): "20",
        int(25): "25"
    }
    improvement_default = 10

    title = "🤖 AI Simulation Insight"
    description = "AI-powered analysis of how targeted wellbeing improvements could enhance national life satisfaction through evidence-based policy recommendations."

    layout = ddk.Card(
        id=component_id,
        children=[
            ddk.CardHeader(title=title),
            html.Div(
                style={"display": "flex", "flexDirection": "row", "flexWrap": "wrap", "rowGap": "10px", "alignItems": "center", "marginBottom": "15px"},
                children=[
                    html.Div(
                        children=[
                            html.Label("Country:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=country_control_id,
                                options=country_options,
                                value=country_default,
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px"}
                    ),
                    html.Div(
                        children=[
                            html.Label("Dimension to Improve:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            dcc.Dropdown(
                                id=dimension_control_id,
                                options=dimension_options,
                                value=dimension_default,
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px"}
                    ),
                    html.Div(
                        children=[
                            html.Label("Improvement Points:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            html.Div(
                                children=dcc.Slider(
                                    id=improvement_control_id,
                                    min=5,
                                    max=25,
                                    step=5,
                                    value=improvement_default,
                                    marks=improvement_marks,
                                    tooltip={"placement": "bottom", "always_visible": True}
                                ),
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px", "width": "300px"}
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
                    "background": "#F8F9FA",
                    "borderLeft": "4px solid #3498DB",
                    "padding": "16px",
                    "margin": "20px 0",
                    "fontFamily": "Inter, Lato, sans-serif",
                    "borderRadius": "4px"
                }
            ),
            html.Pre(id=error_id, style={"color": "red", "margin": "10px 0"}),
            ddk.CardFooter(title=description)
        ],
        width=50
    )

    test_inputs: dict[str, TestInput] = {
        country_control_id: {
            "options": [option["value"] for option in country_options],
            "default": country_default
        },
        dimension_control_id: {
            "options": [option["value"] for option in dimension_options],
            "default": dimension_default
        },
        improvement_control_id: {
            "options": list(improvement_marks.keys()),
            "default": improvement_default
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

    country = kwargs.get(country_control_id, "United States")
    dimension = kwargs.get(dimension_control_id, "environment")
    improvement = kwargs.get(improvement_control_id, 10)
    
    if country is None:
        country = "United States"
    if dimension is None:
        dimension = "environment"
    if improvement is None:
        improvement = 10

    logger.debug("Starting chart creation. Country: %s, Dimension: %s, Improvement: %s", country, dimension, improvement)

    country_data = df[df['country'] == country]
    if len(country_data) == 0:
        empty_fig = go.Figure()
        empty_fig.update_layout(
            annotations=[{
                "text": f"No data available for {country}",
                "showarrow": False,
                "font": {"size": 20}
            }]
        )
        return empty_fig, f"No data available for {country}."

    current_life_sat = country_data['life_satisfaction'].iloc[0]
    current_dimension_val = country_data[dimension].iloc[0]
    
    # Simple correlation-based simulation
    correlation = df['life_satisfaction'].corr(df[dimension])
    estimated_life_sat_increase = improvement * correlation * 0.3  # Scale factor for realistic estimates
    
    new_life_sat = current_life_sat + estimated_life_sat_increase
    new_dimension_val = current_dimension_val + improvement

    # Create scatter plot showing current vs simulated position
    fig = go.Figure()

    # Add all countries as background
    fig.add_trace(go.Scatter(
        x=df[dimension],
        y=df['life_satisfaction'],
        mode='markers',
        name='Other Countries',
        marker=dict(color='lightgray', size=8, opacity=0.6),
        hovertemplate="<b>%{text}</b><br>" + 
                     f"{dimension.replace('_', ' ').title()}: %{{x:.1f}}<br>" +
                     "Life Satisfaction: %{y:.1f}<extra></extra>",
        text=df['country']
    ))

    # Add top performers (Finland, Denmark)
    top_countries = ['Finland', 'Denmark']
    top_data = df[df['country'].isin(top_countries)]
    if len(top_data) > 0:
        fig.add_trace(go.Scatter(
            x=top_data[dimension],
            y=top_data['life_satisfaction'],
            mode='markers',
            name='Top Performers',
            marker=dict(color='green', size=12, symbol='star'),
            hovertemplate="<b>%{text}</b><br>" + 
                         f"{dimension.replace('_', ' ').title()}: %{{x:.1f}}<br>" +
                         "Life Satisfaction: %{y:.1f}<extra></extra>",
            text=top_data['country']
        ))

    # Add current country position
    fig.add_trace(go.Scatter(
        x=[current_dimension_val],
        y=[current_life_sat],
        mode='markers',
        name=f'{country} (Current)',
        marker=dict(color='red', size=15),
        hovertemplate=f"<b>{country} (Current)</b><br>" + 
                     f"{dimension.replace('_', ' ').title()}: %{{x:.1f}}<br>" +
                     "Life Satisfaction: %{y:.1f}<extra></extra>"
    ))

    # Add simulated position
    fig.add_trace(go.Scatter(
        x=[new_dimension_val],
        y=[new_life_sat],
        mode='markers',
        name=f'{country} (Simulated)',
        marker=dict(color='blue', size=15, symbol='diamond'),
        hovertemplate=f"<b>{country} (Simulated)</b><br>" + 
                     f"{dimension.replace('_', ' ').title()}: %{{x:.1f}}<br>" +
                     "Life Satisfaction: %{y:.1f}<extra></extra>"
    ))

    # Add arrow showing improvement
    fig.add_annotation(
        x=new_dimension_val,
        y=new_life_sat,
        ax=current_dimension_val,
        ay=current_life_sat,
        xref="x",
        yref="y",
        axref="x",
        ayref="y",
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="blue"
    )

    fig.update_layout(
        xaxis_title=dimension.replace('_', ' ').title(),
        yaxis_title="Life Satisfaction",
        showlegend=True,
        height=500
    )

    # Generate AI narrative
    dimension_name = dimension.replace('_', ' ').title()
    
    # Get top performer data for comparison
    finland_data = df[df['country'] == 'Finland']
    denmark_data = df[df['country'] == 'Denmark']
    
    top_performer_text = ""
    if len(finland_data) > 0 and len(denmark_data) > 0:
        finland_val = finland_data[dimension].iloc[0]
        denmark_val = denmark_data[dimension].iloc[0]
        finland_life_sat = finland_data['life_satisfaction'].iloc[0]
        denmark_life_sat = denmark_data['life_satisfaction'].iloc[0]
        
        top_performer_text = f"Finland scores {finland_val:.1f} in {dimension_name} with {finland_life_sat:.1f} life satisfaction, while Denmark achieves {denmark_val:.1f} and {denmark_life_sat:.1f} respectively."
    
    narrative = html.Div([
        html.H4("🤖 AI Simulation Insight", style={"fontWeight": "bold", "marginBottom": "12px", "color": "#2C3E50"}),
        html.P([
            f"📈 Increasing {country}'s {dimension_name} score by {improvement} points (from {current_dimension_val:.1f} to {new_dimension_val:.1f}) ",
            f"could potentially raise life satisfaction by approximately {estimated_life_sat_increase:.1f} points ",
            f"(from {current_life_sat:.1f} to {new_life_sat:.1f}). This improvement would represent a meaningful enhancement ",
            f"in national wellbeing, demonstrating how targeted policy interventions in {dimension_name.lower()} can create ",
            "measurable gains in citizen satisfaction and quality of life."
        ], style={"marginBottom": "12px", "lineHeight": "1.6"}),
        html.P([
            f"🌍 Comparing {country}'s simulated position to top-performing nations reveals important lessons. ",
            top_performer_text if top_performer_text else f"Leading countries like Finland and Denmark consistently demonstrate that excellence in {dimension_name.lower()} correlates with higher life satisfaction scores. ",
            f"Their success shows that sustained investment in {dimension_name.lower()} infrastructure, policies, and programs ",
            "can yield substantial returns in citizen wellbeing. This shows how targeted progress in key wellbeing areas can meaningfully enhance national life satisfaction."
        ], style={"marginBottom": "0", "lineHeight": "1.6"})
    ])

    return fig, narrative

@callback(
    output=[
        Output(f"{component_id}_graph", "figure"),
        Output(f"{component_id}_narrative", "children"),
        Output(f"{component_id}_error", "children")
    ],
    inputs={
        country_control_id: Input(country_control_id, "value"),
        dimension_control_id: Input(dimension_control_id, "value"),
        improvement_control_id: Input(improvement_control_id, "value"),
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
        return figure, narrative, ""

    except Exception as e:
        error_msg = f"Error updating chart: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return empty_fig, html.Div("Error generating AI narrative."), error_msg