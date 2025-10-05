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

component_id = "policy_simulation_scatter"

dimension_control_id = f"{component_id}_dimension"
environment_slider_id = f"{component_id}_environment_slider"
education_slider_id = f"{component_id}_education_slider"
jobs_slider_id = f"{component_id}_jobs_slider"

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

def component() -> ComponentResponse:
    graph_id = f"{component_id}_graph"
    error_id = f"{component_id}_error"
    loading_id = f"{component_id}_loading"

    title = "📈 Policy Simulation Impact"
    description = "Interactive scatter plot showing how improving the weakest dimensions affects life satisfaction. Includes sliders for simulation."

    layout = ddk.Card(
        id=component_id,
        children=[
            ddk.CardHeader(title=title),
            html.Div(
                style={"display": "flex", "flexDirection": "row", "flexWrap": "wrap", "rowGap": "10px", "alignItems": "center", "marginBottom": "15px"},
                children=[
                    html.Div(
                        children=[
                            html.Label("Dimension to Compare:", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
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
                            html.Label("Environment Policy (+%):", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            html.Div(
                                children=dcc.Slider(
                                    id=environment_slider_id,
                                    min=0,
                                    max=50,
                                    step=5,
                                    value=0,
                                    marks={
                                        int(0): "0%",
                                        int(10): "10%",
                                        int(25): "25%",
                                        int(40): "40%",
                                        int(50): "50%"
                                    },
                                    tooltip={"placement": "bottom"}
                                ),
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px", "width": "250px"}
                    ),
                    html.Div(
                        children=[
                            html.Label("Education Policy (+%):", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            html.Div(
                                children=dcc.Slider(
                                    id=education_slider_id,
                                    min=0,
                                    max=50,
                                    step=5,
                                    value=0,
                                    marks={
                                        int(0): "0%",
                                        int(10): "10%",
                                        int(25): "25%",
                                        int(40): "40%",
                                        int(50): "50%"
                                    },
                                    tooltip={"placement": "bottom"}
                                ),
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px", "width": "250px"}
                    ),
                    html.Div(
                        children=[
                            html.Label("Jobs Policy (+%):", style={"marginBottom": "5px", "fontWeight": "bold", "display": "block"}),
                            html.Div(
                                children=dcc.Slider(
                                    id=jobs_slider_id,
                                    min=0,
                                    max=50,
                                    step=5,
                                    value=0,
                                    marks={
                                        int(0): "0%",
                                        int(10): "10%",
                                        int(25): "25%",
                                        int(40): "40%",
                                        int(50): "50%"
                                    },
                                    tooltip={"placement": "bottom"}
                                ),
                                style={"minWidth": "200px"}
                            )
                        ],
                        style={"display": "flex", "flexDirection": "column", "marginRight": "15px", "width": "250px"}
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
            html.Pre(id=error_id, style={"color": "red", "margin": "10px 0"}),
            ddk.CardFooter(title=description)
        ],
        width=100
    )

    test_inputs: dict[str, TestInput] = {
        dimension_control_id: {
            "options": [option["value"] for option in dimension_options],
            "default": dimension_default
        },
        environment_slider_id: {
            "options": [0, 10, 25, 40, 50],
            "default": 0
        },
        education_slider_id: {
            "options": [0, 10, 25, 40, 50],
            "default": 0
        },
        jobs_slider_id: {
            "options": [0, 10, 25, 40, 50],
            "default": 0
        }
    }

    return {
        "layout": layout,
        "test_inputs": test_inputs
    }

def _update_logic(**kwargs) -> go.Figure:
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
        return empty_fig

    dimension = kwargs.get(dimension_control_id, dimension_default)
    if dimension is None:
        dimension = dimension_default

    environment_boost = kwargs.get(environment_slider_id, 0)
    education_boost = kwargs.get(education_slider_id, 0)
    jobs_boost = kwargs.get(jobs_slider_id, 0)

    if environment_boost is None:
        environment_boost = 0
    if education_boost is None:
        education_boost = 0
    if jobs_boost is None:
        jobs_boost = 0

    logger.debug("Starting chart creation. df:\n%s", df.head())

    df_sim = df.copy()
    
    # Apply policy boosts (convert percentage to multiplier)
    df_sim['environment_sim'] = df_sim['environment'] * (1 + environment_boost / 100)
    df_sim['education_sim'] = df_sim['education'] * (1 + education_boost / 100)
    df_sim['jobs_sim'] = df_sim['jobs'] * (1 + jobs_boost / 100)
    
    # Cap values at 100
    df_sim['environment_sim'] = np.minimum(df_sim['environment_sim'], 100)
    df_sim['education_sim'] = np.minimum(df_sim['education_sim'], 100)
    df_sim['jobs_sim'] = np.minimum(df_sim['jobs_sim'], 100)
    
    # Calculate simulated life satisfaction (simplified model: weighted average of key dimensions)
    weights = {
        'environment': 0.15,
        'education': 0.15,
        'jobs': 0.20,
        'safety': 0.10,
        'income': 0.10,
        'housing': 0.10,
        'health': 0.10,
        'work_life_balance': 0.05,
        'social_connections': 0.05
    }
    
    df_sim['life_satisfaction_sim'] = (
        df_sim['environment_sim'] * weights['environment'] +
        df_sim['education_sim'] * weights['education'] +
        df_sim['jobs_sim'] * weights['jobs'] +
        df_sim['safety'] * weights['safety'] +
        df_sim['income'] * weights['income'] +
        df_sim['housing'] * weights['housing'] +
        df_sim['health'] * weights['health'] +
        df_sim['work_life_balance'] * weights['work_life_balance'] +
        df_sim['social_connections'] * weights['social_connections']
    )
    
    # Get the simulated dimension value
    if dimension == 'environment':
        df_sim['dimension_sim'] = df_sim['environment_sim']
    elif dimension == 'education':
        df_sim['dimension_sim'] = df_sim['education_sim']
    elif dimension == 'jobs':
        df_sim['dimension_sim'] = df_sim['jobs_sim']
    else:
        df_sim['dimension_sim'] = df_sim[dimension]

    fig = go.Figure()

    # Add current positions
    fig.add_trace(go.Scatter(
        x=df[dimension],
        y=df['life_satisfaction'],
        mode='markers',
        name='Current Position',
        text=df['country'],
        hovertemplate="<b>%{text}</b><br>" +
                     f"{dimension.replace('_', ' ').title()}: %{{x:.1f}}<br>" +
                     "Life Satisfaction: %{y:.1f}<extra></extra>",
        marker=dict(
            size=8,
            opacity=0.7
        )
    ))

    # Add simulated positions if any policy changes
    if environment_boost > 0 or education_boost > 0 or jobs_boost > 0:
        fig.add_trace(go.Scatter(
            x=df_sim['dimension_sim'],
            y=df_sim['life_satisfaction_sim'],
            mode='markers',
            name='Simulated Position',
            text=df_sim['country'],
            hovertemplate="<b>%{text}</b><br>" +
                         f"{dimension.replace('_', ' ').title()}: %{{x:.1f}}<br>" +
                         "Life Satisfaction: %{y:.1f}<br>" +
                         "<i>After Policy Changes</i><extra></extra>",
            marker=dict(
                size=8,
                opacity=0.7,
                symbol='diamond'
            )
        ))

        # Add arrows showing movement
        for i in range(len(df)):
            if abs(df_sim.iloc[i]['dimension_sim'] - df.iloc[i][dimension]) > 0.1 or \
               abs(df_sim.iloc[i]['life_satisfaction_sim'] - df.iloc[i]['life_satisfaction']) > 0.1:
                fig.add_annotation(
                    x=df_sim.iloc[i]['dimension_sim'],
                    y=df_sim.iloc[i]['life_satisfaction_sim'],
                    ax=df.iloc[i][dimension],
                    ay=df.iloc[i]['life_satisfaction'],
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1,
                    arrowcolor="gray",
                    opacity=0.6
                )

    fig.update_layout(
        xaxis_title=dimension.replace('_', ' ').title(),
        yaxis_title="Life Satisfaction",
        showlegend=True,
        hovermode='closest'
    )

    return fig

@callback(
    output=[
        Output(f"{component_id}_graph", "figure"),
        Output(f"{component_id}_error", "children")
    ],
    inputs={
        dimension_control_id: Input(dimension_control_id, "value"),
        environment_slider_id: Input(environment_slider_id, "value"),
        education_slider_id: Input(education_slider_id, "value"),
        jobs_slider_id: Input(jobs_slider_id, "value"),
        **FILTER_CALLBACK_INPUTS
    }
)
def update(**kwargs) -> Tuple[go.Figure, str]:
    empty_fig = go.Figure()
    empty_fig.update_layout(
        annotations=[{"text": "An error occurred while updating this chart", "showarrow": False, "font": {"size": 20}}]
    )

    try:
        figure = _update_logic(**kwargs)
        return figure, ""

    except Exception as e:
        error_msg = f"Error updating chart: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return empty_fig, error_msg