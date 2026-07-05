"""Viewport-owned dropdown searchability for the responsive page layouts."""

from dash import Input, Output, State


SMALL_SCREEN_MAX_WIDTH = 1250
RESPONSIVE_INPUT_MODE_STORE_ID = "responsive-input-mode-store"

RESPONSIVE_DROPDOWN_IDS = {
    "guide": (
        "region-dropdown",
        "department-dropdown",
        "arrondissement-dropdown",
    ),
    "analysis": (
        "region-dropdown-analysis",
        "department-dropdown-analysis",
        "arrondissement-dropdown-analysis",
        "granularity-dropdown",
        "ranking-dropdown",
        "star-dropdown-ranking",
    ),
    "economics": (
        "category-dropdown-demographics",
        "granularity-dropdown-demographics",
        "demographics-dropdown-analysis",
    ),
    "wine": (
        "wine-region-selector",
        "wine-appellation-search",
    ),
}


def initial_responsive_input_mode():
    """Return the safe pre-browser state: dropdown text entry is disabled."""
    return {
        "ready": False,
        "is_small_screen": True,
        "max_width": SMALL_SCREEN_MAX_WIDTH,
    }


def _searchable_callback_source(output_count):
    return f"""
        function(mode, pageMarker) {{
            const searchable = Boolean(
                mode && mode.ready && !mode.is_small_screen
            );
            return Array({output_count}).fill(searchable);
        }}
    """


def register_responsive_input_callbacks(app):
    """Register viewport tracking and page-scoped dropdown configuration."""
    app.clientside_callback(
        f"""
        function(pathname, currentMode) {{
            const storeId = "{RESPONSIVE_INPUT_MODE_STORE_ID}";
            const maxWidth = {SMALL_SCREEN_MAX_WIDTH};
            const stateKey = "__michelinResponsiveInputMode";
            const previous = window[stateKey];

            if (previous && typeof previous.cleanup === "function") {{
                previous.cleanup();
            }}

            const viewportMode = function() {{
                const width = window.innerWidth || document.documentElement.clientWidth;
                return {{
                    ready: true,
                    is_small_screen: width <= maxWidth,
                    max_width: maxWidth
                }};
            }};

            let lastMode = viewportMode();

            const publishIfChanged = function() {{
                const nextMode = viewportMode();
                if (
                    lastMode.ready === nextMode.ready &&
                    lastMode.is_small_screen === nextMode.is_small_screen &&
                    lastMode.max_width === nextMode.max_width
                ) {{
                    return;
                }}
                lastMode = nextMode;
                window.dash_clientside.set_props(storeId, {{data: nextMode}});
            }};

            const cleanup = function() {{
                window.removeEventListener("resize", publishIfChanged);
                window.removeEventListener("orientationchange", publishIfChanged);
                window.removeEventListener("beforeunload", cleanup);
                if (window[stateKey] && window[stateKey].cleanup === cleanup) {{
                    delete window[stateKey];
                }}
            }};

            window.addEventListener("resize", publishIfChanged);
            window.addEventListener("orientationchange", publishIfChanged);
            window.addEventListener("beforeunload", cleanup);
            window[stateKey] = {{cleanup: cleanup}};

            if (
                currentMode && currentMode.ready === lastMode.ready &&
                currentMode.is_small_screen === lastMode.is_small_screen &&
                currentMode.max_width === lastMode.max_width
            ) {{
                return window.dash_clientside.no_update;
            }}
            return lastMode;
        }}
        """,
        Output(RESPONSIVE_INPUT_MODE_STORE_ID, "data"),
        Input("url", "pathname"),
        State(RESPONSIVE_INPUT_MODE_STORE_ID, "data"),
    )

    page_markers = {
        "guide": "region-dropdown",
        "analysis": "analysis-content-top",
        "economics": "demographics-content-top",
        "wine": "wine-content-top",
    }
    for page_name, dropdown_ids in RESPONSIVE_DROPDOWN_IDS.items():
        app.clientside_callback(
            _searchable_callback_source(len(dropdown_ids)),
            [Output(dropdown_id, "searchable") for dropdown_id in dropdown_ids],
            Input(RESPONSIVE_INPUT_MODE_STORE_ID, "data"),
            Input(page_markers[page_name], "id"),
        )
