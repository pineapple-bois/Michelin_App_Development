# def generate_optimized_prompt(wine_region, appellation):
#     """
#     Generate a concise, restrained prompt for a French wine-appellation overview.
#
#     The output is intended for a Michelin / gastronomy data app, so the tone should
#     be informed and elegant without sounding promotional.
#     """
#
#     region_context = {
#         "Bordeaux": {
#             "angle": "fine dining and age-worthy red wine traditions",
#             "michelin_relevance": "high",
#         },
#         "Bourgogne": {
#             "angle": "terroir-driven wines and precise food pairings",
#             "michelin_relevance": "high",
#         },
#         "Loire": {
#             "angle": "varied wine styles, freshness, and regional cuisine",
#             "michelin_relevance": "medium",
#         },
#         "Rhône": {
#             "angle": "structured reds, aromatic whites, and robust regional cooking",
#             "michelin_relevance": "medium",
#         },
#         "Alsace": {
#             "angle": (
#                 "aromatic white wines and distinctive Franco-German "
#                 "culinary traditions"
#             ),
#             "michelin_relevance": "medium",
#         },
#         "Provence": {
#             "angle": (
#                 "Mediterranean cuisine, rosé, herbs, seafood, and olive oil"
#             ),
#             "michelin_relevance": "low",
#         },
#         "Dordogne": {
#             "angle": (
#                 "traditional southwest cuisine, duck, walnuts, truffles, "
#                 "and rustic pairings"
#             ),
#             "michelin_relevance": "low",
#         },
#         "Languedoc-Roussillon": {
#             "angle": (
#                 "Mediterranean food culture, varied terroirs, and accessible "
#                 "regional wines"
#             ),
#             "michelin_relevance": "low",
#         },
#         "Sud-ouest": {
#             "angle": (
#                 "diverse local grape varieties, regional cooking, and robust "
#                 "food pairings"
#             ),
#             "michelin_relevance": "low",
#         },
#         "Jura": {
#             "angle": (
#                 "distinctive wine styles, mountain cuisine, cheese, and "
#                 "precise food pairings"
#             ),
#             "michelin_relevance": "medium",
#         },
#         "Corse": {
#             "angle": (
#                 "Mediterranean cuisine, island grape varieties, herbs, "
#                 "seafood, and charcuterie"
#             ),
#             "michelin_relevance": "low",
#         },
#         "Savoie": {
#             "angle": (
#                 "Alpine wines, freshness, mountain cheeses, and regional cuisine"
#             ),
#             "michelin_relevance": "low",
#         },
#     }
#
#     context = region_context.get(
#         wine_region,
#         {
#             "angle": (
#                 "the relationship between wine style, local food culture, "
#                 "and occasional fine-dining use"
#             ),
#             "michelin_relevance": "unknown",
#         },
#     )
#
#     if context["michelin_relevance"] == "high":
#         dining_instruction = (
#             "Mention Michelin-level dining only where it feels natural, "
#             "especially in relation to precision, ageing potential, "
#             "prestige, or classic pairings."
#         )
#     elif context["michelin_relevance"] == "medium":
#         dining_instruction = (
#             "Balance fine-dining relevance with everyday regional food culture. "
#             "Do not overstate the Michelin connection."
#         )
#     elif context["michelin_relevance"] == "low":
#         dining_instruction = (
#             "Prioritise traditional regional cuisine and local food culture. "
#             "Avoid implying a strong Michelin connection unless it is genuinely relevant."
#         )
#     else:
#         dining_instruction = (
#             "Do not assume a Michelin connection. Discuss fine dining only "
#             "if it is clearly applicable."
#         )
#
#     return f"""
# Write a concise, factual overview of the {appellation} appellation within the
# {wine_region} wine region for a refined gastronomy data app.
#
# Cover:
# - The appellation's place within {wine_region}.
# - Its main grape varieties and typical wine styles.
# - Climate and terroir only where they directly explain those styles.
# - Its food-and-wine identity, with emphasis on {context["angle"]}.
# - {dining_instruction}
#
# Style rules:
# - Focus on {appellation}; use {wine_region} only as regional context.
# - Write 3 short paragraphs.
# - Do not use bullet points in the final answer.
# - Avoid tourist-board language, clichés, and exaggerated claims.
# - Prefer concrete, specific details over broad praise.
# - Do not invent classifications, permitted grapes, or production rules.
# - If a detail is uncertain, omit it.
# - Keep the total length around 120–170 words.
# """.strip()


def generate_optimized_prompt(wine_region, appellation):
    """
    Generate a concise, context-aware prompt for a French wine appellation.

    This is an intentionally lightweight semantic layer. It uses broad regional
    rules and a small number of appellation-name signals without attempting to
    encode a complete French wine classification system.
    """

    region_rules = {
        "Bordeaux": {
            "default_focus": (
                "Explain whether the appellation is associated mainly with the Left Bank, "
                "Right Bank, dry white Bordeaux, or sweet wine production. Distinguish "
                "appellation identity from château classifications."
            ),
            "signals": {
                "1855_rules": (
                    "Where relevant, explain that the 1855 classification applies to named "
                    "estates rather than to the appellation itself. Mention renowned estates "
                    "only when they materially help explain the appellation."
                ),
                "right_bank": (
                    "Emphasise Merlot and Cabernet Franc where appropriate, together with "
                    "the role of clay, limestone, or gravel in shaping style."
                ),
                "sweet_wine": (
                    "Focus on sweet white wine production, botrytis where applicable, "
                    "principal grapes, acidity, texture, and ageing potential."
                ),
            },
        },
        "Bourgogne": {
            "default_focus": (
                "Explain the appellation's place within Burgundy's regional, village, "
                "Premier Cru, and Grand Cru hierarchy where this is relevant. Keep vineyard, "
                "appellation, climat, and producer identities distinct."
            ),
            "signals": {
                "grand_cru": (
                    "If the appellation is a Grand Cru, explain its vineyard identity and "
                    "status clearly, without treating prestige as a substitute for detail."
                ),
                "renowned_vineyards": (
                    "Mention renowned vineyards or climats only when they are central to "
                    "understanding the appellation."
                ),
            },
        },
        "Alsace": {
            "default_focus": (
                "Prioritise grape variety, dryness or sweetness, aromatic style, and the "
                "relationship between village, lieu-dit, and Grand Cru identity where relevant."
            ),
            "signals": {
                "grand_cru": (
                    "If Grand Cru status is relevant, explain it as part of the Alsace system "
                    "and avoid generalising from Burgundy or Bordeaux terminology."
                ),
            },
        },
        "Loire": {
            "default_focus": (
                "Identify the dominant wine colour, grape variety, and subregional context. "
                "Distinguish still, sparkling, sweet, and dry styles where applicable."
            ),
            "signals": {},
        },
        "Rhône": {
            "default_focus": (
                "Clarify whether the appellation belongs to the Northern or Southern Rhône, "
                "then focus on its principal grapes, wine colours, and characteristic style."
            ),
            "signals": {},
        },
        "Jura": {
            "default_focus": (
                "Clarify whether the appellation is associated with still wine, Vin Jaune, "
                "Vin de Paille, or sparkling wine, and explain the relevant grape varieties."
            ),
            "signals": {},
        },
        "Savoie": {
            "default_focus": (
                "Emphasise local grape varieties, alpine geography, freshness, and the "
                "specific wine styles permitted by the appellation."
            ),
            "signals": {},
        },
        "Corse": {
            "default_focus": (
                "Emphasise indigenous or regionally important grape varieties, coastal or "
                "mountain influence, and the appellation's principal wine styles."
            ),
            "signals": {},
        },
        "Provence": {
            "default_focus": (
                "Do not assume the appellation is defined only by rosé. Identify its permitted "
                "wine colours, principal grapes, and any distinctive local style."
            ),
            "signals": {},
        },
        "Languedoc-Roussillon": {
            "default_focus": (
                "Identify the appellation's subregional setting, principal grapes, wine colours, "
                "and any distinctive production style."
            ),
            "signals": {},
        },
        "Sud-ouest": {
            "default_focus": (
                "Prioritise local grape varieties, the appellation's precise geographic context, "
                "and the wine styles that distinguish it from neighbouring areas."
            ),
            "signals": {},
        },
        "Dordogne": {
            "default_focus": (
                "Prioritise local grape varieties, wine colour, sweetness where relevant, and "
                "the appellation's relationship to the wider southwest."
            ),
            "signals": {},
        },
    }

    appellation_key = appellation.casefold()
    semantic_signals = []

    if wine_region == "Bordeaux":
        if appellation in {"Margaux", "Pauillac", "Saint-Julien", "Saint-Estèphe"}:
            semantic_signals.append("1855_rules")
        if appellation in {"Pomerol", "Saint-Émilion", "Saint-Emilion"}:
            semantic_signals.append("right_bank")
        if appellation in {"Sauternes", "Barsac"}:
            semantic_signals.append("sweet_wine")

    if wine_region in {"Bourgogne", "Alsace"} and "grand cru" in appellation_key:
        semantic_signals.append("grand_cru")

    if wine_region == "Bourgogne" and appellation in {
        "Romanée-Conti",
        "La Tâche",
        "Richebourg",
        "Chambertin",
        "Clos de Vougeot",
        "Montrachet",
    }:
        semantic_signals.extend(["grand_cru", "renowned_vineyards"])

    context = region_rules.get(
        wine_region,
        {
            "default_focus": (
                "Explain what distinguishes this appellation from its parent region, focusing "
                "on grape varieties, wine styles, terroir, and any relevant hierarchy."
            ),
            "signals": {},
        },
    )

    signal_instructions = [
        context["signals"][signal]
        for signal in dict.fromkeys(semantic_signals)
        if signal in context["signals"]
    ]

    semantic_instruction = " ".join(signal_instructions)
    if not semantic_instruction:
        semantic_instruction = (
            "Do not force a classification or prestige narrative if it is not clearly relevant."
        )

    return f"""
Write a concise, factual overview of the {appellation} appellation within the
{wine_region} wine region.

Regional context:
- {context["default_focus"]}

Appellation-specific direction:
- {semantic_instruction}

Select the three most informative aspects of this appellation rather than covering
every category mechanically. Useful subjects may include appellation identity,
classification, principal grapes, wine colour, production method, terroir, ageing,
renowned vineyards or estates, and the distinction between appellation and producer.

Style rules:
- Focus on {appellation}; use {wine_region} only as context.
- Write 3 short paragraphs with no bullet points in the final answer.
- Avoid generic praise, tourist language, food-pairing filler, and Michelin references.
- Mention renowned vineyards, estates, classifications, or special status only when
  they materially explain the appellation.
- Do not invent classifications, permitted grapes, vineyard ownership, or production rules.
- If a detail is uncertain, omit it.
- Keep the total length around 120–170 words.
""".strip()
