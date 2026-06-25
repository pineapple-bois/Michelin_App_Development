

def generate_optimized_prompt(wine_region):
    """
    Generates an optimized prompt for providing a concise overview of a specified wine region, tailored to its relationship
    with Michelin-starred dining or local cuisine.

    The function bins wine regions into two categories:
    1. Regions known for their strong connection to Michelin-starred dining (e.g., Bordeaux, Bourgogne).
    2. Regions where wines are more commonly associated with local, traditional dining (e.g., Provence, Dordogne).

    Based on the category, the function creates a prompt that:
    - For Michelin regions: Emphasizes the region's connection to high-end dining and gourmet wine pairings.
    - For local cuisine regions: Focuses on how the wines complement the region's traditional cuisine, avoiding a forced Michelin connection.
    - For other regions: Provides an accurate description without assuming a specific connection to Michelin or local cuisine.

    Args:
        wine_region (str): The name of the wine region for which the prompt is being generated.

    Returns:
        str: A prompt for generating a description of the wine region, tailored to either Michelin-starred dining or local cuisine contexts.

    Example:
        prompt = generate_optimized_prompt("Bordeaux")
        print(prompt)
        # Will generate a prompt emphasizing Bordeaux's connection to Michelin-starred dining.
    """
    michelin_regions = ['Bordeaux', 'Bourgogne', 'Loire', 'Champagne', 'Rhône', 'Alsace']
    local_cuisine_regions = ['Provence', 'Dordogne', 'Languedoc-Roussillon']

    if wine_region in michelin_regions:
        focus = (
            f"Explain how wines from {wine_region} are used in Michelin-level dining, "
            f"with specific examples of pairings where appropriate."
        )
    elif wine_region in local_cuisine_regions:
        focus = (
            f"Explain how wines from {wine_region} complement the region’s traditional cuisine. "
            f"Do not mention Michelin dining unless it is genuinely relevant."
        )
    else:
        focus = (
            "Describe how the region’s wines fit into both everyday local cuisine and fine dining when applicable."
        )

    prompt = (
        f"Write a concise, factual overview of the {wine_region} wine region.\n"
        f"- Include the main grape varieties.\n"
        f"- Give a brief description of the climate and key terroir features, focusing on how they influence wine style.\n"
        f"- List key appellations (only within {wine_region}).\n"
        f"- {focus}\n"
        f"- Structure the output in short, clear paragraphs (not bullet points).\n"
        f"- Avoid exaggerated language.\n"
        f"- Keep it to approximately 3–4 short paragraphs."
    )

    return prompt
