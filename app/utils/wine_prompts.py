PROMPT_SIGNAL_CONTEXT = {
    "sparkling": "Sparkling wine styles may be relevant.",
    "cremant": "Crémant sparkling wine may be relevant.",
    "ancestral_method": (
        "The ancestral method of sparkling-wine production may be relevant."
    ),
    "noble_rot_botrytis": (
        "Noble rot or botrytis may be relevant to the wine's style."
    ),
    "late_harvest": (
        "Late harvesting may increase sweetness, ripeness, and concentration."
    ),
    "successive_pickings": (
        "Grapes may be harvested through successive selective pickings."
    ),
    "fortified_sweet": "A sweet fortified wine style may be relevant.",
    "fortified_or_liqueur_wine": (
        "A fortified or liqueur-wine style may be relevant."
    ),
    "oxidative_speciality": (
        "An oxidative speciality wine style may be relevant."
    ),
    "straw_wine": (
        "A straw-wine style made from dried grapes may be relevant."
    ),
    "primeur": "A wine intended for early release may be relevant.",
    "sur_lie": "Lees ageing or bottling sur lie may be relevant.",
}


def prompt_signal_instructions(prompt_signals):
    """Return trusted prompt context for ordered machine-readable signals."""
    unknown_signals = [
        signal for signal in prompt_signals
        if signal not in PROMPT_SIGNAL_CONTEXT
    ]
    if unknown_signals:
        raise ValueError(
            "Unknown Wine prompt signals: "
            + ", ".join(dict.fromkeys(unknown_signals))
        )
    return [PROMPT_SIGNAL_CONTEXT[signal] for signal in prompt_signals]


def curated_signals_for_appellation(wine_region, appellation):
    """Return hand-maintained hierarchy, geography, and estate signals."""
    appellation_key = appellation.casefold()
    curated_signals = []

    if wine_region == "Bordeaux":
        if appellation in {"Margaux", "Pauillac", "Saint-Julien", "Saint-Estèphe"}:
            curated_signals.append("1855_rules")
        if appellation in {"Pomerol", "Saint-Émilion", "Saint-Emilion"}:
            curated_signals.extend(["right_bank", "estate_required"])
        if appellation in {"Sauternes", "Barsac"}:
            curated_signals.extend(["sweet_wine", "estate_required"])

    if (
        wine_region in {"Bourgogne", "Alsace"}
        and "grand cru" in appellation_key
    ):
        curated_signals.append("grand_cru")

    if wine_region == "Bourgogne" and appellation in {
        "Romanée-Conti",
        "La Tâche",
        "Richebourg",
        "Chambertin",
        "Clos de Vougeot",
        "Clos de Vougeot ou Clos Vougeot",
        "Montrachet",
    }:
        curated_signals.extend(["grand_cru", "renowned_vineyards"])

    return list(dict.fromkeys(curated_signals))


def generate_optimized_prompt(wine_region, appellation, prompt_signals=()):
    """
    Generate a concise, context-aware prompt for a French wine appellation.

    Dataset-backed prompt signals own production and style context. Curated
    signals are restricted to hierarchy, geography, classification, and estate
    guidance that the dataset does not provide.
    """

    region_rules = {
        "Bordeaux": {
            "default_focus": (
                "Explain whether the appellation is associated mainly with the Left Bank, "
                "Right Bank, dry white Bordeaux, or sweet wine production. Distinguish "
                "appellation identity from château classifications. Populate renowned_estates "
                "only when the estates are unquestionably associated with the exact appellation; "
                "otherwise return an empty array."
            ),
            "signals": {
                "1855_rules": (
                    "Explain that the 1855 classification applies to named estates rather "
                    "than to the appellation itself. Populate renowned_estates only with "
                    "widely recognised classified châteaux unambiguously tied to the exact appellation."
                ),
                "right_bank": (
                    "Emphasise Merlot and Cabernet Franc where appropriate, together with "
                    "the role of clay, limestone, or gravel in shaping style. Populate "
                    "renowned_estates only when the association with the exact appellation "
                    "is unquestionable."
                ),
                "estate_required": (
                    "Renowned estate identity is central to understanding this appellation. "
                    "Return 2 or 3 unquestionably established estates directly associated with "
                    "the exact appellation. Do not return an empty renowned_estates array unless "
                    "no such estates can be stated with high confidence."
                ),
                "sweet_wine": (
                    "Focus on sweet white wine production, botrytis where applicable, "
                    "principal grapes, acidity, texture, and ageing potential. Populate "
                    "renowned_estates only with benchmark estates unquestionably associated "
                    "with the exact appellation."
                ),
            },
        },
        "Bourgogne": {
            "default_focus": (
                "Explain the appellation's place within Burgundy's regional, village, "
                "Premier Cru, and Grand Cru hierarchy where this is relevant. Keep vineyard, "
                "appellation, and climat identities distinct."
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

    curated_signals = curated_signals_for_appellation(
        wine_region,
        appellation,
    )

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
    for signal in curated_signals:
        signal_instructions.append(context["signals"][signal])

    semantic_instruction = " ".join(signal_instructions)
    if not semantic_instruction:
        semantic_instruction = (
            "Do not force a classification or prestige narrative if it is not clearly relevant."
        )

    source_context = prompt_signal_instructions(prompt_signals)
    source_context_section = ""
    if source_context:
        source_context_section = (
            "\n\nAdditional source context:\n"
            + "\n".join(f"- {instruction}" for instruction in source_context)
        )

    estate_regions = {"Bordeaux", "Rhône", "Alsace"}

    if wine_region not in estate_regions:
        estates_instruction = (
            f"Return an empty renowned_estates array for {wine_region}. "
            "Estate recommendations are not enabled for this region."
        )
    elif "estate_required" in curated_signals:
        estates_instruction = (
            "Return 2 or 3 widely recognised estates unambiguously associated with "
            "this exact appellation. Estate identity is important here, so do not "
            "leave renowned_estates empty when high-confidence examples exist. "
            "Do not infer names from nearby appellations or naming conventions."
        )
    else:
        estates_instruction = (
            "You may return up to 3 renowned estates only when each estate is widely "
            "recognised and unambiguously associated with this exact appellation. "
            "Prefer an empty array over a plausible, obscure, disputed, or uncertain name. "
            "Do not infer estates from naming conventions, nearby appellations, or the wider region."
        )

    return f"""
Create compact factual content for this French wine appellation.

Appellation: {appellation}
Region: {wine_region}

Focus:
- {context["default_focus"]}
- {semantic_instruction}{source_context_section}

Estate policy:
- {estates_instruction}

Return valid JSON only, matching this exact shape:
{{
  "summary": "",
  "principal_grapes": [],
  "supporting_grapes": [],
  "wine_styles": [],
  "food_pairings": [],
  "renowned_estates": [],
  "key_facts": [
    {{"label": "", "text": ""}},
    {{"label": "", "text": ""}},
    {{"label": "", "text": ""}}
  ],
  "editorial_note": ""
}}

Field limits:
- summary: Maximum 20 words. Follow naturally after the appellation heading and
  state its most distinctive non-redundant feature. Do not repeat the appellation,
  region, mapped area, grape names, food pairings, or simple wine-style labels.
- principal_grapes: Maximum 3 grapes central to the appellation's recognised wines.
- supporting_grapes: Maximum 3 commonly relevant supporting grapes. Exclude
  marginal or merely permitted varieties.
- wine_styles: Maximum 4 concise labels such as "Dry red", "Sweet white", or
  "Traditional-method sparkling".
- food_pairings: Maximum 3 pairings with a strong, widely recognised connection
  to the appellation's principal wine styles. Do not infer pairings from the
  broader region or nearby local cuisine. Prefer familiar dish categories over
  obscure named regional specialities. Return [] when no pairing is clearly
  established.
- key_facts: Return 2 or 3 appellation-specific facts. Use a third fact only when
  it adds distinct, useful information. Use a short label and no more than 24
  words of text for each. Do not repeat the summary.
- renowned_estates: Maximum 3 names only. Follow the Estate policy exactly.
- editorial_note: Maximum 24 words. Distinguish the appellation from a commonly
  confused neighbouring appellation or broader wine category. Return "" when no
  useful distinction is important.

Rules:
- Include every top-level key.
- Use [] or "" when information is uncertain or not relevant.
- Never state, estimate, compare, interpret, or infer mapped area.
- Use only high-confidence, appellation-specific facts.
- Do not repeat facts between summary, key_facts, and editorial_note.
- Grape names belong only in principal_grapes and supporting_grapes.
- Food belongs only in food_pairings.
- Producer or estate names belong only in renowned_estates.
- Do not invent classifications, permitted grapes, production rules, vineyard
  ownership, or estates.
- Avoid generic praise, tourist language, and Michelin references.
- Output JSON only, with no Markdown or surrounding text.
""".strip()
