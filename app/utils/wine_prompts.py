#
#
# def generate_optimized_prompt(wine_region):
#     """
#     Generates an optimized prompt for providing a concise overview of a specified wine region, tailored to its relationship
#     with Michelin-starred dining or local cuisine.
#
#     The function bins wine regions into two categories:
#     1. Regions known for their strong connection to Michelin-starred dining (e.g., Bordeaux, Bourgogne).
#     2. Regions where wines are more commonly associated with local, traditional dining (e.g., Provence, Dordogne).
#
#     Based on the category, the function creates a prompt that:
#     - For Michelin regions: Emphasizes the region's connection to high-end dining and gourmet wine pairings.
#     - For local cuisine regions: Focuses on how the wines complement the region's traditional cuisine, avoiding a forced Michelin connection.
#     - For other regions: Provides an accurate description without assuming a specific connection to Michelin or local cuisine.
#
#     Args:
#         wine_region (str): The name of the wine region for which the prompt is being generated.
#
#     Returns:
#         str: A prompt for generating a description of the wine region, tailored to either Michelin-starred dining or local cuisine contexts.
#
#     Example:
#         prompt = generate_optimized_prompt("Bordeaux")
#         print(prompt)
#         # Will generate a prompt emphasizing Bordeaux's connection to Michelin-starred dining.
#     """
#     michelin_regions = ['Bordeaux', 'Bourgogne', 'Loire', 'Champagne', 'Rhône', 'Alsace']
#     local_cuisine_regions = ['Provence', 'Dordogne', 'Languedoc-Roussillon']
#
#     if wine_region in michelin_regions:
#         focus = (
#             f"Explain how wines from {wine_region} are used in Michelin-level dining, "
#             f"with specific examples of pairings where appropriate."
#         )
#     elif wine_region in local_cuisine_regions:
#         focus = (
#             f"Explain how wines from {wine_region} complement the region’s traditional cuisine. "
#             f"Do not mention Michelin dining unless it is genuinely relevant."
#         )
#     else:
#         focus = (
#             "Describe how the region’s wines fit into both everyday local cuisine and fine dining when applicable."
#         )
#
#     prompt = (
#         f"Write a concise, factual overview of the {wine_region} wine region.\n"
#         f"- Include the main grape varieties.\n"
#         f"- Give a brief description of the climate and key terroir features, focusing on how they influence wine style.\n"
#         f"- List key appellations (only within {wine_region}).\n"
#         f"- {focus}\n"
#         f"- Structure the output in short, clear paragraphs (not bullet points).\n"
#         f"- Avoid exaggerated language.\n"
#         f"- Keep it to approximately 3–4 short paragraphs."
#     )
#
#     return prompt



def generate_optimized_prompt(wine_region):
    """
    Generate a concise, restrained prompt for a French wine-region overview.

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
        "Champagne": {
            "angle": "celebration, aperitif culture, and gastronomic versatility",
            "michelin_relevance": "high",
        },
        "Rhône": {
            "angle": "structured reds, aromatic whites, and robust regional cooking",
            "michelin_relevance": "medium",
        },
        "Alsace": {
            "angle": "aromatic white wines and distinctive Franco-German culinary traditions",
            "michelin_relevance": "medium",
        },
        "Provence": {
            "angle": "Mediterranean cuisine, rosé, herbs, seafood, and olive oil",
            "michelin_relevance": "low",
        },
        "Dordogne": {
            "angle": "traditional southwest cuisine, duck, walnuts, truffles, and rustic pairings",
            "michelin_relevance": "low",
        },
        "Languedoc-Roussillon": {
            "angle": "Mediterranean food culture, varied terroirs, and accessible regional wines",
            "michelin_relevance": "low",
        },
    }

    context = region_context.get(
        wine_region,
        {
            "angle": "the relationship between wine style, local food culture, and occasional fine-dining use",
            "michelin_relevance": "unknown",
        },
    )

    if context["michelin_relevance"] == "high":
        dining_instruction = (
            "Mention Michelin-level dining only where it feels natural, especially in relation "
            "to precision, ageing potential, prestige appellations, or classic pairings."
        )
    elif context["michelin_relevance"] == "medium":
        dining_instruction = (
            "Balance fine-dining relevance with everyday regional food culture. Do not overstate "
            "the Michelin connection."
        )
    elif context["michelin_relevance"] == "low":
        dining_instruction = (
            "Prioritise traditional regional cuisine and local food culture. Avoid implying a strong "
            "Michelin connection unless it is genuinely relevant."
        )
    else:
        dining_instruction = (
            "Do not assume a Michelin connection. Discuss fine dining only if it is clearly applicable."
        )

    return f"""
Write a concise, factual overview of the {wine_region} wine region for a refined gastronomy data app.

Cover:
- Main grape varieties.
- Climate and terroir features, only where they explain the wine style.
- Key appellations within {wine_region}; avoid naming appellations outside the region.
- The region's food-and-wine identity, with emphasis on {context["angle"]}.
- {dining_instruction}

Style rules:
- Write 3 short paragraphs.
- Do not use bullet points in the final answer.
- Avoid tourist-board language, clichés, and exaggerated claims.
- Prefer concrete, specific details over broad praise.
- Do not invent facts. If a detail is uncertain, omit it.
- Keep the total length around 120–170 words.
""".strip()
