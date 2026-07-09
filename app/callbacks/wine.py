import json
import math

import dash
from dash import Patch, html, no_update
from dash.dependencies import ALL, Input, Output, State
from dash.exceptions import PreventUpdate
from flask import session

from app.utils.star_filters import update_button_active_state_helper
from app.utils.wine_figures import (
    RESTAURANT_STAR_ORDER,
    RESTAURANT_TRACE_BELOW,
    RESTAURANT_TRACE_INDICES,
    REGIONAL_OUTLINE_LAYER_INDEX,
    WINE_AOC_TRACE_INDEX,
    plot_wine_choropleth_plotly,
)
from app.utils.wine_prompts import generate_optimized_prompt
from app.utils.wine_search import (
    build_wine_search_index,
    map_view_for_feature,
    map_view_for_region,
    wine_records_for_region,
    wine_region_options,
    wine_search_lookup,
    wine_search_options,
)

WINE_VIEW_GEOGRAPHY_KEY = "geography"


def resolve_wine_feature(click_data, feature_lookup):
    """Resolve an AOC click by stable feature ID, or fail closed."""
    if not isinstance(click_data, dict):
        return None

    points = click_data.get("points")
    if not isinstance(points, list) or not points or not isinstance(points[0], dict):
        return None

    feature_id = points[0].get("location")
    if not isinstance(feature_id, str):
        return None

    return feature_lookup.get(feature_id)


def resolve_wine_hover(hover_data, feature_lookup):
    """Resolve a semantic AOC hover payload, or fail closed."""
    if not isinstance(hover_data, dict):
        return None

    points = hover_data.get("points")
    if not isinstance(points, list) or not points or not isinstance(points[0], dict):
        return None

    point = points[0]
    if point.get("curveNumber") != WINE_AOC_TRACE_INDEX:
        return None

    customdata = point.get("customdata")
    if not isinstance(customdata, (list, tuple)) or len(customdata) != 3:
        return None

    region, display_name, custom_feature_id = customdata
    location = point.get("location")
    if not all(
        isinstance(value, str) and value
        for value in (region, display_name, custom_feature_id, location)
    ):
        return None
    if location != custom_feature_id:
        return None

    feature = feature_lookup.get(location)
    if feature is None:
        return None
    if (
        feature.get("region") != region
        or feature.get("display_name") != display_name
    ):
        return None

    return point, feature


def wine_hover_overlay_response(hover_data, feature_lookup):
    """Return fixed-overlay content for a validated AOC hover payload."""
    resolved_hover = resolve_wine_hover(hover_data, feature_lookup)
    if resolved_hover is None:
        return "", "", True

    _, feature = resolved_hover
    return feature["display_name"], feature["region"], False


def wine_hover_highlight_patch(hover_data, feature_lookup, feature_indices):
    """Select only the hovered AOC so Plotly applies its lighter fill."""
    selectedpoints = []
    resolved_hover = resolve_wine_hover(hover_data, feature_lookup)
    if resolved_hover is not None:
        point, _ = resolved_hover
        feature_index = feature_indices.get(point["location"])
        if feature_index is not None:
            selectedpoints = [feature_index]

    patched_figure = Patch()
    patched_figure["data"][WINE_AOC_TRACE_INDEX]["selectedpoints"] = selectedpoints
    return patched_figure


def toggle_active(n_clicks):
    return bool(n_clicks and n_clicks % 2 == 1)


def regional_outlines_visible(n_clicks):
    return toggle_active(n_clicks)


def regional_outline_visibility_patch(n_clicks):
    patched_figure = Patch()
    patched_figure["layout"]["map"]["layers"][REGIONAL_OUTLINE_LAYER_INDEX]["visible"] = (
        regional_outlines_visible(n_clicks)
    )
    return patched_figure


def restaurant_overlay_visible(n_clicks_rest):
    return toggle_active(n_clicks_rest)


def selected_restaurant_stars(n_clicks_stars, ids):
    if not n_clicks_stars or not ids:
        return set(RESTAURANT_STAR_ORDER)

    return {
        button_id["index"]
        for n_clicks, button_id in zip(n_clicks_stars, ids)
        if n_clicks % 2 == 0
    }


def restaurant_filter_style(show_restaurants):
    return (
        {'width': '30%', 'display': 'block'}
        if show_restaurants
        else {'width': '30%', 'display': 'none'}
    )


def reset_restaurant_star_clicks(n_clicks_rest, ids):
    """Reset the star-filter parity when the restaurant overlay closes."""
    if restaurant_overlay_visible(n_clicks_rest) or not ids:
        return None
    return [0] * len(ids)


def restaurant_visibility_patch(n_clicks_rest, n_clicks_stars=None, ids=None):
    show_restaurants = restaurant_overlay_visible(n_clicks_rest)
    active_stars = selected_restaurant_stars(n_clicks_stars, ids)

    patched_figure = Patch()
    for star in RESTAURANT_STAR_ORDER:
        trace_index = RESTAURANT_TRACE_INDICES[star]
        patched_figure["data"][trace_index]["visible"] = (
            show_restaurants and star in active_stars
        )
        patched_figure["data"][trace_index]["below"] = RESTAURANT_TRACE_BELOW
    return patched_figure


def wine_geography_key(selected_region, selected_feature_id, search_lookup):
    """Identify the region/appellation that owns the current Wine viewport."""
    record = search_lookup.get(selected_feature_id)
    valid_feature_id = None
    if record is not None and (
        not selected_region or record.region == selected_region
    ):
        valid_feature_id = selected_feature_id

    return {
        "region": selected_region,
        "feature_id": valid_feature_id,
    }


def wine_view_revision(geography_key):
    """Return a stable Plotly view revision for one Wine geography."""
    return "wine-aoc-map-v1:{region}:{feature_id}".format(
        region=geography_key.get("region") or "all",
        feature_id=geography_key.get("feature_id") or "all",
    )


def selected_wine_map_view(
    selected_region,
    selected_feature_id,
    records,
    search_lookup,
):
    """Return the canonical viewport for the active Wine geography."""
    geography_key = wine_geography_key(
        selected_region,
        selected_feature_id,
        search_lookup,
    )
    feature_id = geography_key["feature_id"]
    if feature_id is not None:
        return map_view_for_feature(feature_id, search_lookup)
    return map_view_for_region(selected_region, records)


def wine_navigation_patch(
    selected_region,
    selected_feature_id,
    records,
    search_lookup,
):
    """Return a small deterministic viewport patch for one Wine geography."""
    selected_view = selected_wine_map_view(
        selected_region,
        selected_feature_id,
        records,
        search_lookup,
    )
    geography_key = wine_geography_key(
        selected_region,
        selected_feature_id,
        search_lookup,
    )
    if selected_view is None:
        return None

    patched_figure = Patch()
    patched_figure["layout"]["map"]["uirevision"] = wine_view_revision(
        geography_key
    )
    patched_figure["layout"]["map"]["zoom"] = selected_view["zoom"]
    patched_figure["layout"]["map"]["center"] = selected_view["center"]
    return patched_figure


def wine_navigation_command(
    selected_region,
    selected_feature_id,
    records,
    search_lookup,
):
    """Return the trusted camera target used for browser-side sequencing."""
    selected_view = selected_wine_map_view(
        selected_region,
        selected_feature_id,
        records,
        search_lookup,
    )
    if selected_view is None:
        return None

    geography_key = wine_geography_key(
        selected_region,
        selected_feature_id,
        search_lookup,
    )
    return {
        "uirevision": wine_view_revision(geography_key),
        "zoom": selected_view["zoom"],
        "center": selected_view["center"],
    }


def map_view_from_relayout(
    relayout_data,
    existing_data=None,
    geography_key=None,
):
    existing_data = dict(existing_data or {})

    if not relayout_data:
        return None

    user_interaction_keys = {'map.zoom', 'map.center'}
    if not user_interaction_keys.intersection(relayout_data.keys()):
        return None

    stored_geography = existing_data.get(WINE_VIEW_GEOGRAPHY_KEY)
    default_geography = {"region": None, "feature_id": None}
    if geography_key is not None:
        if stored_geography != geography_key and not (
            geography_key == default_geography and stored_geography is None
        ):
            return None

    zoom = relayout_data.get('map.zoom', existing_data.get('zoom'))
    center = relayout_data.get('map.center', existing_data.get('center'))
    if zoom is None or center is None:
        return None

    existing_data['zoom'] = zoom
    existing_data['center'] = center
    if geography_key is not None:
        existing_data[WINE_VIEW_GEOGRAPHY_KEY] = geography_key
    return existing_data


def updated_wine_view_store(
    triggered_ids,
    relayout_data,
    selected_region,
    selected_feature_id,
    records,
    search_lookup,
    existing_data=None,
):
    """Resolve navigation and manual Wine viewport updates deterministically."""
    triggered_ids = set(triggered_ids or ())
    geography_key = wine_geography_key(
        selected_region,
        selected_feature_id,
        search_lookup,
    )

    if triggered_ids.intersection({
        "wine-region-selector",
        "wine-appellation-search",
    }):
        map_view = selected_wine_map_view(
            selected_region,
            selected_feature_id,
            records,
            search_lookup,
        )
    else:
        return map_view_from_relayout(
            relayout_data,
            existing_data,
            geography_key,
        )

    if map_view is None:
        return None

    stored_view = dict(existing_data or {})
    stored_view.update(map_view)
    stored_view[WINE_VIEW_GEOGRAPHY_KEY] = geography_key
    return stored_view


def format_hectares(source_area_m2):
    """Format square metres as hectares rounded to two significant figures."""
    hectares = float(source_area_m2) / 10_000
    decimal_places = 1 - math.floor(math.log10(hectares))
    rounded = round(hectares, decimal_places)
    if decimal_places > 0:
        return f"{rounded:.{decimal_places}f}".rstrip("0").rstrip(".")
    return f"{rounded:.0f}"


def build_wine_region_heading(wine_feature, colour):
    area = format_hectares(wine_feature["source_area_m2"])
    return html.Div(
        className="wine-region-heading",
        children=[
            html.H3(
                wine_feature["region"],
                style={"color": colour},
            ),
            html.P(
                f"{wine_feature['display_name']} · {area} hectares",
                className="wine-appellation-area",
            ),
        ],
    )


def render_wine_info(content, region_colour):
    """Render a parsed Wine information response as semantic Dash components."""
    def text_value(field):
        value = content.get(field, "")
        return value.strip() if isinstance(value, str) else ""

    def string_items(field):
        values = content.get(field, [])
        if not isinstance(values, list):
            return []
        return [
            value.strip()
            for value in values
            if isinstance(value, str) and value.strip()
        ]

    def pill_section(heading, values, modifier):
        if not values:
            return None
        return html.Section(
            className="wine-info-section",
            children=[
                html.H4(heading, className="wine-info-section-heading"),
                html.Div(
                    [
                        html.Span(
                            value,
                            className=f"wine-info-pill wine-info-pill--{modifier}",
                        )
                        for value in values
                    ],
                    className="wine-info-pill-list",
                ),
            ],
        )

    children = [html.P(text_value("summary"), className="wine-info-summary")]

    principal_grapes = string_items("principal_grapes")
    supporting_grapes = string_items("supporting_grapes")
    if principal_grapes or supporting_grapes:
        grape_pills = [
            html.Span(
                grape,
                className="wine-info-pill wine-info-pill--principal-grape",
            )
            for grape in principal_grapes
        ]
        grape_pills.extend(
            html.Span(
                grape,
                className="wine-info-pill wine-info-pill--supporting-grape",
            )
            for grape in supporting_grapes
        )
        children.append(
            html.Section(
                className="wine-info-section",
                children=[
                    html.H4(
                        "Grape varieties / Cépages",
                        className="wine-info-section-heading",
                    ),
                    html.Div(grape_pills, className="wine-info-pill-list"),
                ],
            )
        )

    styles_section = pill_section("Styles", string_items("wine_styles"), "style")
    if styles_section:
        children.append(styles_section)

    pairings_section = pill_section(
        "Classic pairings",
        string_items("food_pairings"),
        "pairing",
    )
    if pairings_section:
        children.append(pairings_section)

    estates = string_items("renowned_estates")
    if estates:
        children.append(
            html.Section(
                className="wine-info-section",
                children=[
                    html.H4(
                        "Renowned estates",
                        className="wine-info-section-heading",
                    ),
                    html.Ul(
                        [html.Li(estate) for estate in estates],
                        className="wine-info-estates",
                    ),
                ],
            )
        )

    key_facts = content.get("key_facts", [])
    fact_items = []
    if isinstance(key_facts, list):
        for fact in key_facts:
            if not isinstance(fact, dict):
                continue
            label = fact.get("label")
            text = fact.get("text")
            if (
                isinstance(label, str)
                and label.strip()
                and isinstance(text, str)
                and text.strip()
            ):
                fact_items.append(
                    html.Div(
                        [html.Strong(f"{label.strip()}:"), f" {text.strip()}"],
                        className="wine-info-key-fact",
                    )
                )
    if fact_items:
        children.append(
            html.Section(
                className="wine-info-section",
                children=[
                    html.H4("Key facts", className="wine-info-section-heading"),
                    html.Div(fact_items),
                ],
            )
        )

    children.append(
        html.P(text_value("editorial_note"), className="wine-info-editorial-note")
    )
    return html.Div(
        children,
        className="wine-info-content",
        style={"--wine-region-accent": region_colour},
    )


def build_wine_info_response(
    click_data,
    feature_lookup,
    cache,
    openai_client,
    is_request_limit_exceeded,
    prompt_builder=generate_optimized_prompt,
):
    """Build the Wine information panel from semantic AOC click data."""
    if not click_data:
        return (
            "Click on an appellation to get more information",
            {"display": "none"},
            no_update,
            {"display": "none"},
        )

    wine_feature = resolve_wine_feature(click_data, feature_lookup)
    if wine_feature is None:
        return no_update, no_update, no_update, no_update

    wine_region = wine_feature["region"]
    appellation = wine_feature["app"]
    prompt_signals = wine_feature["prompt_signals"]

    cache_key = f"wine_info_v3_{appellation}_{wine_region}"
    cached_content = cache.get(cache_key)
    if isinstance(cached_content, dict) and isinstance(
        cached_content.get("content"), dict
    ):
        region_name_content = build_wine_region_heading(
            wine_feature,
            cached_content.get("color", wine_feature["colour"]),
        )
        print(f"Cached Information retrieved for {appellation}: {wine_region}")
        return (
            render_wine_info(
                cached_content["content"],
                cached_content.get("color", wine_feature["colour"]),
            ),
            {"display": "block"},
            region_name_content,
            {"display": "block"},
        )

    if is_request_limit_exceeded():
        error_message = "You have reached the maximum number of requests."
        styled_error = html.Div(error_message, style={"color": "red", "font-weight": "bold", "text-align": "center"})
        return styled_error, {"display": "none"}, no_update, {"display": "none"}

    region_color = wine_feature["colour"]

    try:
        prompt = prompt_builder(wine_region, appellation, prompt_signals)
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )
        content = response.choices[0].message.content
        try:
            parsed_content = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return (
                "We couldn't load the wine information. Please try again.",
                {"display": "none"},
                no_update,
                {"display": "none"},
            )

        if not isinstance(parsed_content, dict):
            return (
                "We couldn't load the wine information. Please try again.",
                {"display": "none"},
                no_update,
                {"display": "none"},
            )

        cache.set(cache_key, {'content': parsed_content, 'color': region_color})

        region_name_content = build_wine_region_heading(
            wine_feature,
            region_color,
        )
        return (
            render_wine_info(parsed_content, region_color),
            {"display": "block"},
            region_name_content,
            {"display": "block"},
        )

    except Exception as e:
        return f"Error fetching region details: {str(e)}", {"display": "none"}, no_update, {"display": "none"}


def register_wine_callbacks(app, data, config, cache, openai_client):
    all_france = data.all_france
    wine_df = data.wine_df
    region_df = data.region_df
    wine_feature_lookup = (
        wine_df.set_index("feature_id")[
            [
                "region",
                "app",
                "display_name",
                "colour",
                "categorie",
                "prompt_signals",
                "source_area_m2",
            ]
        ]
        .to_dict("index")
    )
    wine_feature_indices = {
        feature_id: index
        for index, feature_id in enumerate(wine_df["feature_id"])
    }
    wine_search_records = build_wine_search_index(wine_df)
    wine_feature_search_lookup = wine_search_lookup(wine_search_records)

    app.clientside_callback(
        """
        async function(command) {
            if (
                !command ||
                !command.center ||
                typeof command.zoom !== "number"
            ) {
                return window.dash_clientside.no_update;
            }

            const graph = document.querySelector(
                "#wine-map-graph .js-plotly-plot"
            );
            if (!graph || !window.Plotly) {
                return window.dash_clientside.no_update;
            }

            await window.Plotly.relayout(
                graph,
                {"map.zoom": command.zoom}
            );
            await new Promise(function(resolve) {
                window.requestAnimationFrame(function() {
                    window.requestAnimationFrame(resolve);
                });
            });
            await window.Plotly.relayout(
                graph,
                {"map.center": command.center}
            );
            return command.uirevision;
        }
        """,
        Output('wine-navigation-correction-output', 'children'),
        Input('wine-navigation-command', 'data'),
        prevent_initial_call=True,
    )

    def is_request_limit_exceeded():
        # Request limit for OpenAi API calls
        request_limit = config.openai_request_limit

        # Check if request_count exists in session
        if 'request_count' not in session:
            session['request_count'] = 0  # Initialize if not present

        session['request_count'] += 1  # Increment request count

        if session['request_count'] > request_limit:
            return True
        return False

    @app.callback(
        [Output('wine-map-graph', 'figure'),
         Output('wine-map-ready', 'data')],
        Input('url', 'pathname'),
        State('map-view-store', 'data')
    )
    def initialize_wine_map(pathname, map_view_data):
        if pathname != '/wine':
            raise PreventUpdate
        return plot_wine_choropleth_plotly(
            wine_df=wine_df,
            zoom_data=map_view_data,
            regional_outline_df=region_df,
            restaurants_df=all_france,
        ), True

    @app.callback(
        [Output('wine-map-graph', 'figure', allow_duplicate=True),
         Output('wine-navigation-command', 'data')],
        [Input('wine-region-selector', 'value'),
         Input('wine-appellation-search', 'value'),
         Input('wine-map-ready', 'data')],
        prevent_initial_call=True,
    )
    def navigate_wine_map(
        selected_region,
        selected_feature_id,
        map_ready,
    ):
        if not map_ready:
            raise PreventUpdate
        patch = wine_navigation_patch(
            selected_region,
            selected_feature_id,
            wine_search_records,
            wine_feature_search_lookup,
        )
        if patch is None:
            raise PreventUpdate
        command = wine_navigation_command(
            selected_region,
            selected_feature_id,
            wine_search_records,
            wine_feature_search_lookup,
        )
        return patch, command

    @app.callback(
        [Output('wine-map-graph', 'figure', allow_duplicate=True),
         Output('toggle-regional-outlines-wine', 'active')],
        Input('toggle-regional-outlines-wine', 'n_clicks'),
        prevent_initial_call=True,
    )
    def update_wine_regional_outlines(n_clicks):
        return regional_outline_visibility_patch(n_clicks), toggle_active(n_clicks)

    @app.callback(
        [Output('wine-map-graph', 'figure', allow_duplicate=True),
         Output('star-filter-container-wine', 'style'),
         Output('toggle-show-details-wine', 'active')],
        [Input('toggle-show-details-wine', 'n_clicks'),
         Input({'type': 'filter-button-wine', 'index': ALL}, 'n_clicks')],
        [State({'type': 'filter-button-wine', 'index': ALL}, 'id')],
        prevent_initial_call=True,
    )
    def update_wine_restaurant_visibility(n_clicks_rest, n_clicks_stars, ids):
        show_restaurants = restaurant_overlay_visible(n_clicks_rest)
        return (
            restaurant_visibility_patch(n_clicks_rest, n_clicks_stars, ids),
            restaurant_filter_style(show_restaurants),
            toggle_active(n_clicks_rest),
        )

    @app.callback(
        Output({'type': 'filter-button-wine', 'index': ALL}, 'n_clicks'),
        Input('toggle-show-details-wine', 'n_clicks'),
        State({'type': 'filter-button-wine', 'index': ALL}, 'id'),
        prevent_initial_call=True,
    )
    def reset_wine_restaurant_star_filters(n_clicks_rest, ids):
        reset_clicks = reset_restaurant_star_clicks(n_clicks_rest, ids)
        if reset_clicks is None:
            raise PreventUpdate
        return reset_clicks

    @app.callback(
        Output('wine-region-selector', 'options'),
        Input('url', 'pathname'),
    )
    def update_wine_region_options(pathname):
        if pathname != '/wine':
            raise PreventUpdate
        return wine_region_options(wine_search_records)

    @app.callback(
        Output('wine-appellation-search', 'options'),
        [Input('wine-appellation-search', 'search_value'),
         Input('wine-region-selector', 'value')],
        State('wine-appellation-search', 'value'),
    )
    def update_wine_appellation_options(search_value, selected_region, selected_feature_id):
        available_records = wine_records_for_region(wine_search_records, selected_region)
        return wine_search_options(
            available_records,
            search_value=search_value,
            selected_feature_id=selected_feature_id,
        )

    @app.callback(
        Output('map-view-store', 'data'),
        [Input('wine-map-graph', 'relayoutData'),
         Input('wine-region-selector', 'value'),
         Input('wine-appellation-search', 'value')],
        [State('map-view-store', 'data')]
    )
    def store_map_view(
        relayout_data,
        selected_region,
        selected_feature_id,
        existing_data,
    ):
        ctx = dash.callback_context
        triggered_ids = {
            item['prop_id'].split('.')[0]
            for item in ctx.triggered
            if item.get('prop_id')
        }
        map_view = updated_wine_view_store(
            triggered_ids,
            relayout_data,
            selected_region,
            selected_feature_id,
            wine_search_records,
            wine_feature_search_lookup,
            existing_data,
        )
        if map_view is not None:
            return map_view
        raise dash.exceptions.PreventUpdate

    @app.callback(
        [Output('wine-map-hover-appellation', 'children'),
         Output('wine-map-hover-region', 'children'),
         Output('wine-map-hover-overlay', 'hidden'),
         Output('wine-map-graph', 'figure', allow_duplicate=True)],
        Input('wine-map-graph', 'hoverData'),
        prevent_initial_call=True,
    )
    def update_wine_hover_overlay(hover_data):
        return (
            *wine_hover_overlay_response(hover_data, wine_feature_lookup),
            wine_hover_highlight_patch(
                hover_data,
                wine_feature_lookup,
                wine_feature_indices,
            ),
        )

    @app.callback(
        [Output({'type': 'filter-button-wine', 'index': ALL}, 'className'),
         Output({'type': 'filter-button-wine', 'index': ALL}, 'style')],
        [Input({'type': 'filter-button-wine', 'index': ALL}, 'n_clicks')],
        [State({'type': 'filter-button-wine', 'index': ALL}, 'id')]
    )
    def update_wine_button_active_state(n_clicks_list, ids):
        if not n_clicks_list:
            raise PreventUpdate
        return update_button_active_state_helper(n_clicks_list, ids, 'wine')

    @app.callback(
        [Output('llm-output-container', 'children'),
         Output('disclaimer-container', 'style'),
         Output('region-name-container', 'children'),
         Output('region-name-container', 'style')],
        Input('wine-map-graph', 'clickData')
    )
    def update_wine_info(clickData):
        return build_wine_info_response(
            click_data=clickData,
            feature_lookup=wine_feature_lookup,
            cache=cache,
            openai_client=openai_client,
            is_request_limit_exceeded=is_request_limit_exceeded,
        )
