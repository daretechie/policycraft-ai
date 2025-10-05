import dash_design_kit as ddk
from dash import html

component_registry = {}  # Map of component names to their instances
failed_components = {}  # Map of component names to their error messages

### Component Imports
try:
    from components.filter_component import component as filter_component
except Exception:
    filter_component = None

try:
    from components.data_cards import component as data_card_component
except Exception:
    data_card_component = None

try:
    from components.data_table import component as data_table_component
except Exception:
    data_table_component = None

try:
    from components.global_wellbeing_choropleth import component as global_wellbeing_choropleth_component
    component_registry["global_wellbeing_choropleth"] = global_wellbeing_choropleth_component
except Exception as e:
    failed_components["global_wellbeing_choropleth"] = str(e)
    print(f"[COMPONENT FAILURE] Failed to import global_wellbeing_choropleth:", e)

try:
    from components.country_radar_chart import component as country_radar_chart_component
    component_registry["country_radar_chart"] = country_radar_chart_component
except Exception as e:
    failed_components["country_radar_chart"] = str(e)
    print(f"[COMPONENT FAILURE] Failed to import country_radar_chart:", e)

try:
    from components.gap_analysis_bar_chart import component as gap_analysis_bar_chart_component
    component_registry["gap_analysis_bar_chart"] = gap_analysis_bar_chart_component
except Exception as e:
    failed_components["gap_analysis_bar_chart"] = str(e)
    print(f"[COMPONENT FAILURE] Failed to import gap_analysis_bar_chart:", e)

try:
    from components.policy_simulation_scatter import component as policy_simulation_scatter_component
    component_registry["policy_simulation_scatter"] = policy_simulation_scatter_component
except Exception as e:
    failed_components["policy_simulation_scatter"] = str(e)
    print(f"[COMPONENT FAILURE] Failed to import policy_simulation_scatter:", e)

try:
    from components.wellbeing_dimensions_comparison import component as wellbeing_dimensions_comparison_component
    component_registry["wellbeing_dimensions_comparison"] = wellbeing_dimensions_comparison_component
except Exception as e:
    failed_components["wellbeing_dimensions_comparison"] = str(e)
    print(f"[COMPONENT FAILURE] Failed to import wellbeing_dimensions_comparison:", e)

try:
    from components.composite_index_ranking import component as composite_index_ranking_component
    component_registry["composite_index_ranking"] = composite_index_ranking_component
except Exception as e:
    failed_components["composite_index_ranking"] = str(e)
    print(f"[COMPONENT FAILURE] Failed to import composite_index_ranking:", e)

try:
    from components.add_an_ai_narrative_text_box import component as add_an_ai_narrative_text_box_component
    component_registry["add_an_ai_narrative_text_box"] = add_an_ai_narrative_text_box_component
except Exception as e:
    failed_components["add_an_ai_narrative_text_box"] = str(e)
    print(f"[COMPONENT FAILURE] Failed to import add_an_ai_narrative_text_box:", e)

try:
    from components.produce_an_ai_narrative_text import component as produce_an_ai_narrative_text_component
    component_registry["produce_an_ai_narrative_text"] = produce_an_ai_narrative_text_component
except Exception as e:
    failed_components["produce_an_ai_narrative_text"] = str(e)
    print(f"[COMPONENT FAILURE] Failed to import produce_an_ai_narrative_text:", e)


def _get_component_layout(component_name, width=100, preview=False):
    """
    Safely retrieves a component's layout, handles errors, and adds an edit button in preview mode.
    """
    if component_name not in component_registry:
        # Return a placeholder if the component failed to import
        error_message = failed_components.get(component_name, "Component not found in registry.")
        return ddk.Card(
            width=width,
            children=[
                ddk.CardHeader(title=f'Error loading "{component_name}"', style={"color": "red"}),
                html.Div(f"Details: {error_message}", style={"padding": "1rem"})
            ]
        )

    try:
        layout = component_registry[component_name]()["layout"]
    except Exception as e:
        # Return a placeholder if the component's layout function fails
        return ddk.Card(
            width=width,
            children=[
                ddk.CardHeader(title=f'Error in "{component_name}": {e}', style={"color": "red"}),
                ddk.Graph() # Empty graph as a visual placeholder
            ]
        )

    layout.width = width
    if preview and hasattr(layout, 'children') and layout.children:
        # Add the "Edit" button to the card header
        edit_button = html.Button(
            children=[ddk.Icon(icon_name="pencil"), "Edit"],
            style={"color": "var(--button_background_color)", "background-color": "transparent", "border-width": "1px", "gap": "5px", "display": "flex", "align-items": "center", "padding": "5px 10px"},
            id={"type": "edit-component-button", "index": component_name},
        )
        layout.children[0].children = [edit_button]
    return layout

def component(preview=False):
    layout_items = []

    # Add hero section
    app_title = "OECD Global Wellbeing Explorer"
    app_description = "Interactive data app exploring wellbeing across 41 OECD countries with global mapping, country diagnostics, and policy simulation capabilities to analyze national strengths, weaknesses, and potential improvements."
    app_logo = "https://dash.plotly.com/assets/images/plotly_logo_dark.png"
    app_tags = [
        ddk.Tag(text="**Data Updated:** 2025-10-04", icon="circle-check"),
        ddk.Tag(text="**Created by:** Plotly Studio", icon="user"),
        ddk.Tag(text="**Data Source**: OECD Global Wellbeing Explorer data", icon="database"),
    ]

    layout_items.append(
        ddk.Hero(title=app_title, description=app_description, logo=app_logo, tags=app_tags)
    )

    if filter_component:
        layout_items.append(filter_component()["layout"])

    # Data cards can remain at the top as high-level KPIs
    if data_card_component:
        layout_items.append(data_card_component()["layout"])

    # =====================================================================
    # SECTION 1: Global Overview
    # =====================================================================
    layout_items.append(ddk.Block(width=100, style={'margin-top': '20px', 'textAlign': 'center'}, children=[
        html.H2("🌍 SECTION 1 — Global Overview", style={'font-size': '1.5rem', 'margin-bottom': '0.5rem'}),
        html.P(
            "Explore wellbeing across 41 OECD countries through an interactive world map, rankings, and data explorer. Use this section to see how countries compare globally and identify interesting cases for deeper analysis.",
            style={
                'color': 'var(--secondary-text-color)',
                'margin-top': '0',
                'max-width': '80ch',  # Limit line length for readability
                'margin-left': 'auto', 'margin-right': 'auto'  # Center the paragraph block
            }
        )
    ]))
    layout_items.extend([
        _get_component_layout("global_wellbeing_choropleth", width=50, preview=preview),
        _get_component_layout("composite_index_ranking", width=50, preview=preview),
        _get_component_layout("wellbeing_dimensions_comparison", width=100, preview=preview)
    ])

    # =====================================================================
    # SECTION 2: Country Diagnostic
    # =====================================================================
    layout_items.append(ddk.Block(width=100, style={'margin-top': '20px', 'textAlign': 'center'}, children=[
        html.H2("🧭 SECTION 2 — Country Diagnostic", style={'font-size': '1.5rem', 'margin-bottom': '0.5rem'}),
        html.P(
            "Dive into detailed wellbeing insights for any selected country. See how it performs across dimensions like health, education, and income — and discover its top strengths and critical weaknesses through AI-powered analysis.",
            style={
                'color': 'var(--secondary-text-color)',
                'margin-top': '0',
                'max-width': '80ch',
                'margin-left': 'auto', 'margin-right': 'auto'
            }
        )
    ]))
    layout_items.extend([
        _get_component_layout("country_radar_chart", width=50, preview=preview),
        _get_component_layout("gap_analysis_bar_chart", width=50, preview=preview),
        _get_component_layout("add_an_ai_narrative_text_box", width=100, preview=preview) # This seems to be the "Country Wellbeing Diagnostic"
    ])

    # =====================================================================
    # SECTION 3: Policy Simulator
    # =====================================================================
    layout_items.append(ddk.Block(width=100, style={'margin-top': '20px', 'textAlign': 'center'}, children=[
        html.H2("⚙️ SECTION 3 — Policy Simulator", style={'font-size': '1.5rem', 'margin-bottom': '0.5rem'}),
        html.P(
            'Experiment with "what-if" scenarios. Adjust key wellbeing dimensions and instantly see how life satisfaction could improve. AI insights summarize how these improvements could bring the country closer to top performers like Finland and Denmark.',
            style={
                'color': 'var(--secondary-text-color)',
                'margin-top': '0',
                'max-width': '80ch',
                'margin-left': 'auto', 'margin-right': 'auto'
            }
        )
    ]))
    layout_items.extend([
        _get_component_layout("policy_simulation_scatter", width=50, preview=preview),
        _get_component_layout("produce_an_ai_narrative_text", width=50, preview=preview)
    ])

    # =====================================================================
    # Data Table (as a final reference)
    # =====================================================================
    if data_table_component:
        layout_items.append(data_table_component()["layout"])

    return layout_items