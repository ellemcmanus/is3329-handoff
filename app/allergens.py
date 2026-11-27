"""Reference data: the 14 allergens regulated under EU Regulation 1169/2011,
and the words guests commonly use for each.

Shared by the allergy handler and the safety rules engine.
"""
import re

EU_ALLERGENS = {
    "cereals_gluten": "Cereals containing gluten",
    "crustaceans": "Crustaceans",
    "eggs": "Eggs",
    "fish": "Fish",
    "peanuts": "Peanuts",
    "soybeans": "Soybeans",
    "milk": "Milk",
    "tree_nuts": "Tree nuts",
    "celery": "Celery",
    "mustard": "Mustard",
    "sesame": "Sesame",
    "sulphites": "Sulphites",
    "lupin": "Lupin",
    "molluscs": "Molluscs",
}

# Words that are too vague to map to one allergen. Reception must ask the guest.
AMBIGUOUS = {
    "nuts_unspecified": ("Nuts (type not specified)", "Ask: peanuts, tree nuts, or both?"),
    "shellfish_unspecified": ("Shellfish (type not specified)", "Ask: crustaceans (prawns, crab), molluscs (mussels, oysters), or both?"),
}

KEYWORDS = {
    "cereals_gluten": ["gluten", "coeliac", "celiac", "wheat", "barley", "rye", "spelt"],
    "crustaceans": ["prawn", "prawns", "shrimp", "shrimps", "crab", "lobster", "crayfish", "langoustine", "langoustines"],
    "eggs": ["egg", "eggs"],
    "fish": ["fish", "salmon", "cod", "tuna", "anchovy", "anchovies", "haddock", "hake", "mackerel"],
    "peanuts": ["peanut", "peanuts", "groundnut", "groundnuts"],
    "soybeans": ["soy", "soya", "tofu", "edamame"],
    "milk": ["milk", "dairy", "lactose", "cheese", "butter", "cream", "yoghurt", "yogurt"],
    "tree_nuts": ["tree nut", "tree nuts", "almond", "almonds", "hazelnut", "hazelnuts", "walnut", "walnuts",
                  "cashew", "cashews", "pecan", "pecans", "pistachio", "pistachios", "macadamia", "brazil nut"],
    "celery": ["celery", "celeriac"],
    "mustard": ["mustard"],
    "sesame": ["sesame", "tahini"],
    "sulphites": ["sulphite", "sulphites", "sulfite", "sulfites"],
    "lupin": ["lupin", "lupine"],
    "molluscs": ["mussel", "mussels", "oyster", "oysters", "clam", "clams", "scallop", "scallops", "squid", "octopus"],
    "nuts_unspecified": ["nut", "nuts"],
    "shellfish_unspecified": ["shellfish"],
}


def label(code: str) -> str:
    """Human-readable name for an allergen code."""
    if code in EU_ALLERGENS:
        return EU_ALLERGENS[code]
    if code in AMBIGUOUS:
        return AMBIGUOUS[code][0]
    return code


def find_allergens(text: str) -> dict[str, list[str]]:
    """Return {allergen_code: [words found]} for every allergen word in the text.

    Whole words only, so "nutmeg" or "coconut" do not count as nuts.
    "nuts" is only reported as unspecified when no specific nut was named.
    """
    lowered = text.lower()
    found: dict[str, list[str]] = {}
    for code, words in KEYWORDS.items():
        for word in words:
            if re.search(r"\b" + re.escape(word) + r"\b", lowered):
                found.setdefault(code, []).append(word)

    # If a specific type was named ("tree nuts", "peanuts", "prawns"),
    # the general word is not ambiguous any more.
    if "nuts_unspecified" in found and ("tree_nuts" in found or "peanuts" in found):
        del found["nuts_unspecified"]
    if "shellfish_unspecified" in found and ("crustaceans" in found or "molluscs" in found):
        del found["shellfish_unspecified"]
    return found