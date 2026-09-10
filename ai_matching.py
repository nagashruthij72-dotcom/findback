from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text):

    if text is None:
        return ""

    text = str(text).lower().strip()

    # Remove special characters
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text)

    return text


# ============================================================
# TEXT SIMILARITY
# ============================================================

def text_similarity(text1, text2):

    text1 = normalize_text(text1)
    text2 = normalize_text(text2)

    if not text1 or not text2:
        return 0

    # Exact match
    if text1 == text2:
        return 100

    try:

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2)
        )

        matrix = vectorizer.fit_transform(
            [text1, text2]
        )

        score = cosine_similarity(
            matrix[0:1],
            matrix[1:2]
        )[0][0] * 100

        return round(score, 2)

    except Exception:
        return 0


# ============================================================
# CATEGORY SIMILARITY
# ============================================================

def category_similarity(category1, category2):

    category1 = normalize_text(category1)
    category2 = normalize_text(category2)

    if not category1 or not category2:
        return 0

    if category1 == category2:
        return 100

    return text_similarity(
        category1,
        category2
    )


# ============================================================
# LOCATION SIMILARITY
# ============================================================

def location_similarity(location1, location2):

    location1 = normalize_text(location1)
    location2 = normalize_text(location2)

    if not location1 or not location2:
        return 0

    # Exact location
    if location1 == location2:
        return 100

    words1 = set(location1.split())
    words2 = set(location2.split())

    common_words = words1.intersection(words2)

    if common_words:

        smaller_word_count = min(
            len(words1),
            len(words2)
        )

        if smaller_word_count > 0:

            word_match = (
                len(common_words)
                / smaller_word_count
            ) * 100

            if word_match >= 50:
                return round(word_match, 2)

    return text_similarity(
        location1,
        location2
    )


# ============================================================
# CALCULATE COMPLETE TEXT MATCH
# ============================================================

def calculate_similarity(
    lost_item_name,
    lost_description,
    lost_category,
    lost_location,
    found_item_name,
    found_description,
    found_category,
    found_location
):

    # --------------------------------------------------------
    # Individual scores
    # --------------------------------------------------------

    name_score = text_similarity(
        lost_item_name,
        found_item_name
    )

    description_score = text_similarity(
        lost_description,
        found_description
    )

    category_score = category_similarity(
        lost_category,
        found_category
    )

    location_score = location_similarity(
        lost_location,
        found_location
    )

    # --------------------------------------------------------
    # Base weighted score
    # --------------------------------------------------------

    final_score = (
        name_score * 0.25
        + description_score * 0.35
        + category_score * 0.25
        + location_score * 0.15
    )

    # --------------------------------------------------------
    # SAME CATEGORY BONUS
    # --------------------------------------------------------

    if (
        normalize_text(lost_category)
        == normalize_text(found_category)
        and normalize_text(lost_category)
    ):
        final_score += 3

    # --------------------------------------------------------
    # SAME LOCATION BONUS
    # --------------------------------------------------------

    if (
        normalize_text(lost_location)
        == normalize_text(found_location)
        and normalize_text(lost_location)
    ):
        final_score += 3

    # --------------------------------------------------------
    # Cap score at 100
    # --------------------------------------------------------

    final_score = min(
        final_score,
        100
    )

    return round(final_score, 2)


# ============================================================
# MATCH LEVEL
# ============================================================

def get_match_level(score):

    if score >= 80:
        return "Very Strong Match"

    elif score >= 65:
        return "Strong Match"

    elif score >= 40:
        return "Possible Match"

    else:
        return "Low Match"