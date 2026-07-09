import pytest

from app.utils.wine_prompts import (
    PROMPT_SIGNAL_CONTEXT,
    curated_signals_for_appellation,
    generate_optimized_prompt,
    prompt_signal_instructions,
)


def test_prompt_signal_context_uses_tentative_language():
    assert PROMPT_SIGNAL_CONTEXT
    assert all(
        "may" in instruction.casefold()
        for instruction in PROMPT_SIGNAL_CONTEXT.values()
    )


def test_runtime_prompt_signals_have_context_mappings(data_boundary):
    runtime_signals = {
        signal
        for signals in data_boundary.wine_df["prompt_signals"]
        for signal in signals
    }

    assert runtime_signals
    assert runtime_signals <= PROMPT_SIGNAL_CONTEXT.keys()


def test_prompt_signal_instructions_preserve_order_and_multiple_signals():
    assert prompt_signal_instructions(
        ["noble_rot_botrytis", "late_harvest"]
    ) == [
        PROMPT_SIGNAL_CONTEXT["noble_rot_botrytis"],
        PROMPT_SIGNAL_CONTEXT["late_harvest"],
    ]


def test_prompt_signal_instructions_reject_unknown_signals():
    with pytest.raises(ValueError, match="unknown_signal"):
        prompt_signal_instructions(["unknown_signal"])


@pytest.mark.parametrize(
    ("region", "appellation", "expected"),
    [
        ("Bordeaux", "Pauillac", ["1855_rules"]),
        ("Bordeaux", "Pomerol", ["right_bank", "estate_required"]),
        ("Bordeaux", "Sauternes", ["sweet_wine", "estate_required"]),
        (
            "Bourgogne",
            "Romanée-Conti",
            ["grand_cru", "renowned_vineyards"],
        ),
        (
            "Bourgogne",
            "Clos de Vougeot ou Clos Vougeot",
            ["grand_cru", "renowned_vineyards"],
        ),
        ("Alsace", "Alsace grand cru Brand", ["grand_cru"]),
    ],
)
def test_curated_signals_cover_classification_hierarchy_and_estates(
    region,
    appellation,
    expected,
):
    assert curated_signals_for_appellation(region, appellation) == expected


@pytest.mark.parametrize(
    ("region", "appellation"),
    [
        ("Alsace", "Crémant d'Alsace"),
        ("Alsace", "Muscat d'Alsace"),
        ("Languedoc-Roussillon", "Banyuls"),
        ("Jura", "Macvin du Jura"),
        ("Jura", "Château-Chalon"),
        ("Loire", "Vouvray"),
    ],
)
def test_style_names_do_not_create_curated_signals(region, appellation):
    assert curated_signals_for_appellation(region, appellation) == []


def test_prompt_includes_derived_context_without_raw_categories():
    prompt = generate_optimized_prompt(
        "Alsace",
        "Alsace grand cru Brand",
        ["noble_rot_botrytis", "late_harvest"],
    )

    assert "Additional source context:" in prompt
    assert PROMPT_SIGNAL_CONTEXT["noble_rot_botrytis"] in prompt
    assert PROMPT_SIGNAL_CONTEXT["late_harvest"] in prompt
    assert "Vin de sélection de grains nobles" not in prompt
    assert "Vin de vendanges tardives" not in prompt


def test_prompt_omits_additional_source_context_without_signals():
    prompt = generate_optimized_prompt("Bordeaux", "Pauillac", [])

    assert "Additional source context:" not in prompt
