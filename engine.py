
import re
import json
from collections import Counter

# ML libraries
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


# =====================================================
# 1. SAFE BRAND DATA HELPERS
# =====================================================

def _parse_list(value):
    """Convert a JSON list or comma-separated text into a Python list."""

    if not value:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    try:
        result = json.loads(value)
        if isinstance(result, list):
            return [str(item).strip() for item in result if str(item).strip()]
    except (json.JSONDecodeError, TypeError):
        pass

    return [
        item.strip()
        for item in str(value).split(",")
        if item.strip()
    ]


def _get_brand_data(brand):
    """
    Existing database tuple compatibility:
    brand[1] = brand name
    brand[2] = tone
    brand[3] = approved words
    brand[4] = prohibited words
    brand[5] = additional rules
    """

    if not brand:
        return {
            "name": "Generic",
            "tone": "Professional",
            "approved": [],
            "prohibited": [],
            "rules": ""
        }

    return {
        "name": brand[1],
        "tone": brand[2],
        "approved": _parse_list(brand[3]),
        "prohibited": _parse_list(brand[4]),
        "rules": brand[5] or ""
    }


# =====================================================
# 2. TEXT MATCHING HELPERS
# =====================================================

def _contains_word(content, word):
    """Match a word or phrase without matching partial words."""

    pattern = r"(?<!\w)" + re.escape(word) + r"(?!\w)"

    return re.search(
        pattern,
        content,
        re.IGNORECASE
    ) is not None


def _find_evidence(content, word):
    """Return the actual text that triggered a finding."""

    pattern = r"(?<!\w)" + re.escape(word) + r"(?!\w)"

    match = re.search(
        pattern,
        content,
        re.IGNORECASE
    )

    return match.group(0) if match else word


# =====================================================
# 3. ML BRAND GUIDELINE SIMILARITY
# =====================================================

def calculate_guideline_similarity(content, brand=None):
    """
    Uses TF-IDF and cosine similarity to compare content
    with the selected brand's approved vocabulary and rules.

    This is a lexical similarity indicator, not a guarantee
    of semantic understanding.
    """

    if not ML_AVAILABLE:
        return {
            "score": None,
            "status": "ML unavailable",
            "method": "Rule-based fallback"
        }

    if not brand:
        return {
            "score": None,
            "status": "No brand selected",
            "method": "TF-IDF"
        }

    data = _get_brand_data(brand)

    guideline_text = " ".join([
        data["name"],
        data["tone"],
        " ".join(data["approved"]),
        data["rules"]
    ]).strip()

    if not guideline_text or not content.strip():
        return {
            "score": 0.0,
            "status": "Insufficient text",
            "method": "TF-IDF + Cosine Similarity"
        }

    try:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2)
        )

        vectors = vectorizer.fit_transform([
            content,
            guideline_text
        ])

        similarity = cosine_similarity(
            vectors[0:1],
            vectors[1:2]
        )[0][0]

        percentage = round(float(similarity) * 100, 2)

        if percentage >= 35:
            status = "Strong vocabulary alignment"
        elif percentage >= 15:
            status = "Moderate vocabulary alignment"
        else:
            status = "Low vocabulary alignment"

        return {
            "score": percentage,
            "status": status,
            "method": "TF-IDF + Cosine Similarity"
        }

    except ValueError:
        return {
            "score": 0.0,
            "status": "Unable to compare text",
            "method": "TF-IDF"
        }


# =====================================================
# 4. CONTENT REVIEW ENGINE
# =====================================================

def review_content(content, brand=None):

    issues = []

    if not content or not content.strip():
        return issues

    data = _get_brand_data(brand)

    informal_words = [
        "bro",
        "gonna",
        "wanna",
        "kinda",
        "lol"
    ]

    # ---------------------------------------------
    # Informal language detection
    # ---------------------------------------------

    for word in informal_words:

        if _contains_word(content, word):

            if any(
                word.lower() == banned.lower()
                for banned in data["prohibited"]
            ):
                continue

            issues.append({
                "issue": f"Informal word detected: {word}",
                "severity": "Medium",
                "category": "Tone",
                "evidence": _find_evidence(content, word),
                "suggestion": "Use professional language instead."
            })

    # ---------------------------------------------
    # Excessive punctuation
    # ---------------------------------------------

    if re.search(r"!{3,}", content):

        issues.append({
            "issue": "Excessive exclamation marks",
            "severity": "Low",
            "category": "Formatting",
            "evidence": re.search(r"!{3,}", content).group(0),
            "suggestion": "Use punctuation more professionally."
        })

    # ---------------------------------------------
    # Excessive uppercase words
    # ---------------------------------------------

    uppercase_matches = re.findall(
        r"\b[A-Z]{4,}\b",
        content
    )

    if uppercase_matches:

        issues.append({
            "issue": "Excessive use of capital letters",
            "severity": "Low",
            "category": "Formatting",
            "evidence": ", ".join(uppercase_matches[:5]),
            "suggestion": "Avoid unnecessary uppercase words."
        })

    # ---------------------------------------------
    # Brand-specific analysis
    # ---------------------------------------------

    if brand:

        brand_name = data["name"]
        brand_tone = data["tone"]

        # Prohibited vocabulary
        for word in data["prohibited"]:

            if _contains_word(content, word):

                issues.append({
                    "issue": (
                        f"Prohibited word detected for "
                        f"{brand_name}: {word}"
                    ),
                    "severity": "High",
                    "category": "Brand Vocabulary",
                    "evidence": _find_evidence(content, word),
                    "suggestion": (
                        f"Replace '{word}' with "
                        "brand-approved language."
                    )
                })

        # Tone mismatch
        tone_words = {
            "Professional": [
                "awesome",
                "super cool",
                "dude",
                "yaar"
            ],
            "Friendly": [
                "hereby",
                "aforementioned",
                "pursuant"
            ],
            "Casual": [
                "therefore",
                "furthermore",
                "nevertheless"
            ]
        }

        casual_words = tone_words.get(brand_tone, [])

        for word in casual_words:

            if _contains_word(content, word):

                issues.append({
                    "issue": "Brand tone mismatch",
                    "severity": "Medium",
                    "category": "Brand Tone",
                    "evidence": _find_evidence(content, word),
                    "suggestion": (
                        f"Adjust the wording to match "
                        f"the {brand_tone} brand tone."
                    )
                })

                break

        # Exaggerated claims
        exaggerated_phrases = [
            "best in the world",
            "number one",
            "100% guaranteed",
            "no. 1",
            "world's best"
        ]

        if "exaggerated" in data["rules"].lower():

            for phrase in exaggerated_phrases:

                if _contains_word(content, phrase):

                    issues.append({
                        "issue": "Potential exaggerated claim",
                        "severity": "High",
                        "category": "Claims",
                        "evidence": _find_evidence(content, phrase),
                        "suggestion": (
                            "Avoid unsupported superlative claims. "
                            "Use verifiable evidence."
                        )
                    })

        # Approved vocabulary opportunities
        missing_words = [
            word for word in data["approved"]
            if not _contains_word(content, word)
        ]

        if missing_words:

            issues.append({
                "issue": "Brand vocabulary opportunity",
                "severity": "Suggestion",
                "category": "Brand Vocabulary",
                "evidence": "Approved terms not found in content",
                "suggestion": (
                    "Consider using approved brand words: "
                    + ", ".join(missing_words)
                )
            })

    return issues


# =====================================================
# 5. COMPLIANCE SCORE ENGINE
# =====================================================

def calculate_compliance_score(content, brand=None):

    issues = review_content(content, brand)

    penalties = {
        "High": 15,
        "Medium": 7,
        "Low": 3,
        "Suggestion": 1
    }

    total_penalty = sum(
        penalties.get(issue["severity"], 0)
        for issue in issues
    )

    score = max(0, 100 - total_penalty)

    return {
        "score": score,
        "grade": (
            "Excellent" if score >= 90 else
            "Good" if score >= 75 else
            "Needs Improvement" if score >= 50 else
            "Critical"
        ),
        "total_issues": len(issues),
        "high_issues": sum(
            issue["severity"] == "High" for issue in issues
        ),
        "medium_issues": sum(
            issue["severity"] == "Medium" for issue in issues
        ),
        "low_issues": sum(
            issue["severity"] == "Low" for issue in issues
        )
    }


# =====================================================
# 6. SMART CORRECTION ENGINE
# =====================================================

def suggest_correction(content, brand=None):
    """
    Apply conservative, rule-based improvements while preserving meaning.
    This is a deterministic correction layer, not a full grammar model.
    """
    if not content or not content.strip():
        return content

    corrected = content.strip()
    data = _get_brand_data(brand)

    # Remove informal opening address terms and their punctuation.
    corrected = re.sub(
        r"^\s*(?:bro|dude|lol)\b\s*[,!?.:;\-]*\s*",
        "",
        corrected,
        flags=re.IGNORECASE
    )

    replacements = {
        "gonna": "going to",
        "wanna": "want to",
        "kinda": "somewhat",
        "bro": "",
        "lol": "",
        "dude": "",
        "awesome": "excellent",
        "cheap": "affordable",
    }

    for word in data["prohibited"]:
        replacements[word.lower()] = {
            "cheap": "affordable",
            "bro": "",
            "lol": "",
            "dude": "",
        }.get(word.lower(), "brand-approved")

    for word, replacement in replacements.items():
        pattern = r"(?<!\w)" + re.escape(word) + r"(?!\w)"
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)

    # Rewrite the complete construction to avoid "is the designed to".
    contextual_claims = [
        (r"\bis\s+the\s+best\s+in\s+the\s+world\b",
         "is designed to deliver reliable performance"),
        (r"\bare\s+the\s+best\s+in\s+the\s+world\b",
         "are designed to deliver reliable performance"),
        (r"\bthe\s+best\s+in\s+the\s+world\b",
         "a strong option"),
    ]
    for pattern, replacement in contextual_claims:
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)

    other_claims = {
        r"\bworld's\s+best\b": "designed for quality performance",
        r"\bnumber\s+one\b": "a strong choice",
        r"\b100%\s+guaranteed\b": "designed to provide dependable results",
        r"\bno\.\s*1\b": "a trusted choice",
    }
    for pattern, replacement in other_claims.items():
        corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)

    corrected = re.sub(
        r"\b(is|are)\s+the\s+(designed|built|created)\s+to\b",
        r"\1 \2 to", corrected, flags=re.IGNORECASE
    )

    # Fix common a/an article mismatches after vocabulary replacement.
    corrected = re.sub(r"\ba\s+([aeiou])", r"an \1", corrected, flags=re.IGNORECASE)
    corrected = re.sub(r"\ban\s+([^aeiou\W])", r"a \1", corrected, flags=re.IGNORECASE)

    # Reduce shouting-style uppercase words while retaining short acronyms.
    corrected = re.sub(
        r"\b[A-Z]{4,}\b",
        lambda match: match.group(0).capitalize(),
        corrected
    )

    # Clean spaces and punctuation left by removed terms.
    corrected = re.sub(r"[ \t]{2,}", " ", corrected)
    corrected = re.sub(r"\s+([,.;!?])", r"\1", corrected)
    corrected = re.sub(r"([,;:])(?=\S)", r"\1 ", corrected)
    corrected = re.sub(r"!{2,}", "!", corrected)
    corrected = re.sub(r"\?{2,}", "?", corrected)
    corrected = re.sub(r"\n[ \t]+", "\n", corrected)
    corrected = re.sub(r"\n{3,}", "\n\n", corrected)

    # Capitalize the first letter of each sentence.
    corrected = re.sub(
        r"(^|[.!?]\s+)([a-z])",
        lambda match: match.group(1) + match.group(2).upper(),
        corrected
    )

    return corrected.strip()


# =====================================================
# 7. COMPLETE INTELLIGENCE REPORT
# =====================================================

def analyze_content(content, brand=None):

    issues = review_content(content, brand)

    compliance = calculate_compliance_score(
        content,
        brand
    )

    ml_result = calculate_guideline_similarity(
        content,
        brand
    )

    correction = suggest_correction(
        content,
        brand
    )

    return {
        "issues": issues,
        "compliance": compliance,
        "ml_analysis": ml_result,
        "suggested_correction": correction,
        "total_issues": len(issues)
    }


def integrate_knowledge_findings(report, knowledge_report):
    """
    Merge sufficiently relevant numeric knowledge mismatches
    into the main findings and compliance score.
    """

    if not isinstance(report, dict):
        return report

    if not isinstance(knowledge_report, dict):
        return report

    issues = report.setdefault("issues", [])

    if knowledge_report.get("status") == "Success":
        for result in knowledge_report.get("results", []):

            conflicts = result.get("conflicts", [])

            # Only count mismatches with sufficiently relevant evidence.
            if (
                result.get("status") != "Potential factual mismatch"
                or result.get("similarity", 0) < 35
                or not conflicts
            ):
                continue

            conflict_details = []

            for conflict in conflicts:
                unit = conflict["unit"]

                submitted = conflict["submitted_value"]
                verified = conflict["verified_value"]

                conflict_details.append(
                    f"{submitted:g} {unit} vs {verified:g} {unit}"
                )

            evidence_text = (
                f"Submitted claim: {result['sentence']}\n"
                f"Verified knowledge: {result['evidence']}\n"
                f"Evidence source: {result['source']}\n"
                f"Conflicting values: {', '.join(conflict_details)}"
            )

            # Avoid inserting the same finding twice.
            already_exists = any(
                issue.get("category") == "Factual Verification"
                and issue.get("evidence") == evidence_text
                for issue in issues
            )

            if already_exists:
                continue

            issues.append({
                "issue": "Potential factual mismatch with verified brand knowledge",
                "severity": "High",
                "category": "Factual Verification",
                "evidence": evidence_text,
                "suggestion": (
                    "Verify the submitted claim against the cited "
                    "brand evidence. Correct the conflicting value "
                    "before publishing."
                )
            })

    # Recalculate compliance using the complete findings list.
    penalties = {
        "High": 15,
        "Medium": 7,
        "Low": 3,
        "Suggestion": 1
    }

    total_penalty = sum(
        penalties.get(issue.get("severity", "Low"), 0)
        for issue in issues
    )

    score = max(0, 100 - total_penalty)

    report["compliance"] = {
        "score": score,
        "grade": (
            "Excellent" if score >= 90 else
            "Good" if score >= 75 else
            "Needs Improvement" if score >= 50 else
            "Critical"
        ),
        "total_issues": len(issues),
        "high_issues": sum(
            issue.get("severity") == "High" for issue in issues
        ),
        "medium_issues": sum(
            issue.get("severity") == "Medium" for issue in issues
        ),
        "low_issues": sum(
            issue.get("severity") == "Low" for issue in issues
        )
    }

    report["total_issues"] = len(issues)

    return report

# =====================================================
# 8. SEMANTIC KNOWLEDGE RETRIEVAL
# =====================================================

from functools import lru_cache


@lru_cache(maxsize=1)
def _load_semantic_model():
    """
    Load the pretrained sentence embedding model once.
    First use requires an internet connection.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def verify_against_knowledge(
    content,
    knowledge_items,
    threshold=0.35
):
    """
    Retrieve semantically related brand knowledge for
    each sentence in the submitted content.

    Similarity indicates relevance, NOT factual proof.
    A human reviewer should confirm the evidence.
    """

    if not content or not content.strip():
        return {
            "status": "Empty content",
            "method": "Sentence Transformers",
            "results": [],
            "message": "Please enter content to analyze."
        }

    if not knowledge_items:
        return {
            "status": "No knowledge available",
            "method": "Sentence Transformers",
            "results": [],
            "message": "Add brand knowledge before verification."
        }

    try:
        import numpy as np

        model = _load_semantic_model()

        # Extract knowledge fields from database rows
        knowledge = []

        for item in knowledge_items:
            if len(item) < 7:
                continue

            evidence_text = str(item[4] or "").strip()

            if not evidence_text:
                continue

            knowledge.append({
                "title": item[2],
                "category": item[3],
                "content": evidence_text,
                "source": item[5] or "Source not provided"
            })

        if not knowledge:
            return {
                "status": "No usable evidence",
                "method": "Sentence Transformers",
                "results": [],
                "message": "No valid knowledge text was found."
            }

        # Split submitted content into sentences
        sentences = [
            sentence.strip()
            for sentence in re.split(
                r"(?<=[.!?])\s+",
                content
            )
            if sentence.strip()
        ]

        if not sentences:
            sentences = [content.strip()]

        evidence_texts = [
            item["content"] for item in knowledge
        ]

        # Generate normalized sentence embeddings
        sentence_vectors = model.encode(
            sentences,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        evidence_vectors = model.encode(
            evidence_texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        # Cosine similarity using normalized vectors
        similarity_matrix = np.matmul(
            sentence_vectors,
            evidence_vectors.T
        )

        
        results = []

        for index, sentence in enumerate(sentences):

            best_index = int(
                np.argmax(similarity_matrix[index])
            )

            score = float(
                similarity_matrix[index][best_index]
            )

            matched_item = knowledge[best_index]
            evidence = matched_item["content"]

            # Detect possible numeric contradictions
            number_pattern = (
    r"\b(\d+(?:,\d{3})*(?:\.\d+)?)\s*"
    r"(mah|gb|tb|mp|w|mw|kw|%|years?|months?|days?)\b"
)

            claim_values = re.findall(
                number_pattern, sentence, re.IGNORECASE
            )

            evidence_values = re.findall(
                number_pattern, evidence, re.IGNORECASE
            )

            claim_map = {
                unit.lower(): float(value.replace(",", ""))
                for value, unit in claim_values
            }

            evidence_map = {
                unit.lower(): float(value.replace(",", ""))
                for value, unit in evidence_values
            }

            conflicts = []

            for unit, claim_value in claim_map.items():
                if (
                    unit in evidence_map
                    and claim_value != evidence_map[unit]
                ):
                    conflicts.append({
                        "unit": unit,
                        "submitted_value": claim_value,
                        "verified_value": evidence_map[unit]
                    })

            if conflicts:
                result_status = "Potential factual mismatch"
            elif score >= threshold:
                result_status = "Related evidence found"
            else:
                result_status = "No close evidence found"

            results.append({
                "sentence": sentence,
                "title": matched_item["title"],
                "category": matched_item["category"],
                "evidence": evidence,
                "source": matched_item["source"],
                "similarity": round(score * 100, 2),
                "status": result_status,
                "conflicts": conflicts
            })

        return {
            "status": "Success",
            "method": "all-MiniLM-L6-v2 embeddings",
            "results": results,
            "message": (
                "Similarity measures semantic relevance. "
                "It does not prove or disprove a factual claim."
            )
        }

    except ImportError:
        return {
            "status": "Model unavailable",
            "method": "Sentence Transformers",
            "results": [],
            "message": (
                "Install sentence-transformers to enable "
                "semantic retrieval."
            )
        }

    except Exception as error:
        return {
            "status": "Error",
            "method": "Sentence Transformers",
            "results": [],
            "message": str(error)
        }