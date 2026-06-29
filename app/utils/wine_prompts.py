def generate_optimized_prompt(wine_region, appellation):
    """
    Generate a concise, context-aware prompt for a French wine appellation.

    This is an intentionally lightweight semantic layer. It uses broad regional
    rules and a small number of appellation-name signals without attempting to
    encode a complete French wine classification system.
    """

    common_signals = {
        "sparkling": (
            "Prioritise production method, principal grapes, sweetness level, and how "
            "the sparkling style differs from still wines of the region."
        ),
        "muscat": (
            "Clarify whether the appellation produces dry, sweet, or fortified Muscat, "
            "and do not infer one style from the name alone."
        ),
        "vin_doux_naturel": (
            "Explain the fortified sweet-wine style, principal grapes, and relevant "
            "ageing approach."
        ),
        "vin_jaune": (
            "Explain the oxidative Vin Jaune style, the role of Savagnin, and the "
            "production method that distinguishes the appellation."
        ),
        "fortified": (
            "Explain the fortified production method and distinguish the wine from "
            "ordinary still or sparkling wines of the same region."
        ),
        "multi_style": (
            "State clearly that the appellation permits several wine styles, and do "
            "not describe one style as though it defines the whole appellation."
        ),
    }

    region_rules = {
        "Bordeaux": {
            "default_focus": (
                "Explain whether the appellation is associated mainly with the Left Bank, "
                "Right Bank, dry white Bordeaux, or sweet wine production. Distinguish "
                "appellation identity from château classifications. Name two or three "
                "representative châteaux when established estates are important to "
                "understanding the appellation."
            ),
            "signals": {
                "1855_rules": (
                    "Explain that the 1855 classification applies to named estates rather "
                    "than to the appellation itself. Prioritise two or three renowned "
                    "classified châteaux that clearly represent the appellation."
                ),
                "right_bank": (
                    "Emphasise Merlot and Cabernet Franc where appropriate, together with "
                    "the role of clay, limestone, or gravel in shaping style. Mention one "
                    "or two renowned estates when estate identity is central to the "
                    "appellation's reputation."
                ),
                "sweet_wine": (
                    "Focus on sweet white wine production, botrytis where applicable, "
                    "principal grapes, acidity, texture, and ageing potential. Mention one "
                    "or two benchmark estates where they materially illustrate the style."
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
                "First determine whether the appellation is mainly still, sparkling, dry, "
                "sweet, red, white, or rosé. Then identify the principal grape and subregion."
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
                "First determine whether the appellation is geographic or method-based. "
                "Separate ordinary still wines from Vin Jaune, Vin de Paille, Macvin, "
                "and Crémant."
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
                "First identify whether the appellation is primarily dry still wine, "
                "sparkling wine, Muscat, or vin doux naturel. Then explain its "
                "subregional identity."
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

    if "crémant" in appellation_key or "cremant" in appellation_key:
        semantic_signals.append("sparkling")

    if "muscat" in appellation_key:
        semantic_signals.append("muscat")

    if appellation in {"Banyuls", "Maury", "Rivesaltes", "Grand Roussillon"}:
        semantic_signals.append("vin_doux_naturel")

    if appellation == "Macvin du Jura":
        semantic_signals.append("fortified")

    if appellation == "Château-Chalon":
        semantic_signals.append("vin_jaune")

    if appellation in {"Vouvray", "Montlouis-sur-Loire", "Limoux"}:
        semantic_signals.append("multi_style")

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

    signal_instructions = []
    for signal in dict.fromkeys(semantic_signals):
        if signal in context["signals"]:
            signal_instructions.append(context["signals"][signal])
        elif signal in common_signals:
            signal_instructions.append(common_signals[signal])

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

Open with the single fact that most clearly distinguishes this appellation. Do not
begin with generic geography unless location is itself the defining feature.

Choose the three most useful subjects for this appellation, in this order of priority:
1. what legally or stylistically defines the appellation;
2. principal grapes, wine colours, or production method;
3. hierarchy, classification, terroir, ageing, named sites, or estates only where
   genuinely distinctive.

Style rules:
- Focus on {appellation}; use {wine_region} only as context.
- Write 3 short paragraphs with no bullet points in the final answer.
- Avoid generic praise, tourist language, food-pairing filler, and Michelin references.
- Do not add producer, estate, classification, or prestige material unless it is
  essential to understanding the appellation.
- Do not invent classifications, permitted grapes, vineyard ownership, or production rules.
- If a detail is uncertain, omit it.
- Keep the total length around 120–170 words.
""".strip()
