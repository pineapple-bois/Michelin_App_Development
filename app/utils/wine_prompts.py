def generate_optimized_prompt(wine_region, appellation):
    """
    Generate a concise, restrained prompt for a French wine-appellation overview.

    The output is intended for a Michelin / gastronomy data app, so the tone should
    be informed and elegant without sounding promotional.
    """

    region_context = {
        "Bordeaux": {
            "angle": "fine dining and age-worthy red wine traditions",
            "michelin_relevance": "high",
        },
        "Bourgogne": {
            "angle": "terroir-driven wines and precise food pairings",
            "michelin_relevance": "high",
        },
        "Loire": {
            "angle": "varied wine styles, freshness, and regional cuisine",
            "michelin_relevance": "medium",
        },
        "Rhône": {
            "angle": "structured reds, aromatic whites, and robust regional cooking",
            "michelin_relevance": "medium",
        },
        "Alsace": {
            "angle": (
                "aromatic white wines and distinctive Franco-German "
                "culinary traditions"
            ),
            "michelin_relevance": "medium",
        },
        "Provence": {
            "angle": (
                "Mediterranean cuisine, rosé, herbs, seafood, and olive oil"
            ),
            "michelin_relevance": "low",
        },
        "Dordogne": {
            "angle": (
                "traditional southwest cuisine, duck, walnuts, truffles, "
                "and rustic pairings"
            ),
            "michelin_relevance": "low",
        },
        "Languedoc-Roussillon": {
            "angle": (
                "Mediterranean food culture, varied terroirs, and accessible "
                "regional wines"
            ),
            "michelin_relevance": "low",
        },
        "Sud-ouest": {
            "angle": (
                "diverse local grape varieties, regional cooking, and robust "
                "food pairings"
            ),
            "michelin_relevance": "low",
        },
        "Jura": {
            "angle": (
                "distinctive wine styles, mountain cuisine, cheese, and "
                "precise food pairings"
            ),
            "michelin_relevance": "medium",
        },
        "Corse": {
            "angle": (
                "Mediterranean cuisine, island grape varieties, herbs, "
                "seafood, and charcuterie"
            ),
            "michelin_relevance": "low",
        },
        "Savoie": {
            "angle": (
                "Alpine wines, freshness, mountain cheeses, and regional cuisine"
            ),
            "michelin_relevance": "low",
        },
    }

    context = region_context.get(
        wine_region,
        {
            "angle": (
                "the relationship between wine style, local food culture, "
                "and occasional fine-dining use"
            ),
            "michelin_relevance": "unknown",
        },
    )

    if context["michelin_relevance"] == "high":
        dining_instruction = (
            "Mention Michelin-level dining only where it feels natural, "
            "especially in relation to precision, ageing potential, "
            "prestige, or classic pairings."
        )
    elif context["michelin_relevance"] == "medium":
        dining_instruction = (
            "Balance fine-dining relevance with everyday regional food culture. "
            "Do not overstate the Michelin connection."
        )
    elif context["michelin_relevance"] == "low":
        dining_instruction = (
            "Prioritise traditional regional cuisine and local food culture. "
            "Avoid implying a strong Michelin connection unless it is genuinely relevant."
        )
    else:
        dining_instruction = (
            "Do not assume a Michelin connection. Discuss fine dining only "
            "if it is clearly applicable."
        )

    return f"""
Write a concise, factual overview of the {appellation} appellation within the
{wine_region} wine region for a refined gastronomy data app.

Cover:
- The appellation's place within {wine_region}.
- Its main grape varieties and typical wine styles.
- Climate and terroir only where they directly explain those styles.
- Its food-and-wine identity, with emphasis on {context["angle"]}.
- {dining_instruction}

Style rules:
- Focus on {appellation}; use {wine_region} only as regional context.
- Write 3 short paragraphs.
- Do not use bullet points in the final answer.
- Avoid tourist-board language, clichés, and exaggerated claims.
- Prefer concrete, specific details over broad praise.
- Do not invent classifications, permitted grapes, or production rules.
- If a detail is uncertain, omit it.
- Keep the total length around 120–170 words.
""".strip()
