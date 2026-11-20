
import streamlit as st
import json

from engine import review_content, suggest_correction

from database import (
    save_review,
    get_all_reviews,
    get_review_count,
    save_brand,
    get_all_brands,
    get_brand_by_name
)


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="BrandLens AI",
    page_icon="🔍",
    layout="wide"
)


# ==========================================
# 2. CUSTOM CSS
# ==========================================

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}

[data-testid="stMetric"] {
    background-color: #f5f7fb;
    padding: 15px;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. HEADER
# ==========================================

st.title("🔍 BrandLens AI")

st.subheader(
    "Your Intelligent Brand Governance Assistant"
)

st.write(
    "Analyze marketing content, detect brand guideline "
    "violations and improve brand communication."
)

st.divider()


# ==========================================
# 4. SIDEBAR NAVIGATION
# ==========================================

st.sidebar.title("🔍 BrandLens AI")
st.sidebar.caption("Brand Governance Platform")

menu = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "New Review",
        "Review History",
        "Brand Guidelines"
    ]
)

st.sidebar.divider()
st.sidebar.success("SQLite Database Connected")


# ==========================================
# 5. DASHBOARD
# ==========================================

if menu == "Dashboard":

    st.header("📊 Dashboard")

    reviews = get_all_reviews()
    total_reviews = get_review_count()

    total_issues = sum(
        len(json.loads(review[2] or "[]"))
        for review in reviews
    )

    if total_reviews > 0:

        clean_reviews = sum(
            1
            for review in reviews
            if len(json.loads(review[2] or "[]")) == 0
        )

        compliance = round(
            (clean_reviews / total_reviews) * 100
        )

    else:
        compliance = 0

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Reviews", total_reviews)
    col2.metric("Issues Detected", total_issues)
    col3.metric("Clean Reviews", f"{compliance}%")

    st.divider()

    st.subheader("Welcome to BrandLens AI!")

    st.write("""
    Your AI-powered brand governance platform.

    **Available Features:**

    - Content analysis
    - Brand-specific prohibited word detection
    - Brand tone checking
    - Custom guideline checking
    - Suggested corrections
    - Review history
    - Multiple brand profiles
    - SQLite database storage
    """)

    st.subheader("Recent Reviews")

    for review in reviews[:5]:

        with st.expander(
            f"Review #{review[0]} | {review[4]}"
        ):

            st.write("**Original Content:**")
            st.write(review[1])

            issues = json.loads(review[2] or "[]")

            st.write(f"**Issues Detected:** {len(issues)}")
            st.write("**Suggested Correction:**")
            st.write(review[3])


# ==========================================
# 6. NEW CONTENT REVIEW
# ==========================================

elif menu == "New Review":

    st.header("📝 New Content Review")

    st.write(
        "Select a brand and submit your marketing content."
    )

    # Load saved brands
    brands = get_all_brands()

    brand_options = ["Generic Review"] + [
        brand[1] for brand in brands
    ]

    selected_brand_name = st.selectbox(
        "🏢 Select Brand Profile",
        brand_options
    )

    selected_brand = None

    if selected_brand_name != "Generic Review":

        selected_brand = get_brand_by_name(
            selected_brand_name
        )

        if selected_brand:

            st.info(
                f"Active Brand: {selected_brand[1]} | "
                f"Tone: {selected_brand[2]}"
            )

    content = st.text_area(
        "Enter your marketing content",
        height=220,
        placeholder="Paste your content here..."
    )

    if st.button(
        "🔍 Analyze Content",
        type="primary"
    ):

        if content.strip():

            # Brand-aware analysis
            issues = review_content(
                content,
                selected_brand
            )

            # Generate correction
            corrected_content = suggest_correction(
    content,
    selected_brand
)

            # Save review
            save_review(
                content,
                issues,
                corrected_content
            )

            st.success(
                "Content analyzed and saved successfully!"
            )

            if selected_brand:

                st.caption(
                    f"Analysis performed using {selected_brand[1]} guidelines."
                )

            else:

                st.caption(
                    "Generic content analysis performed."
                )

            st.divider()

            # Analysis results
            st.subheader("📋 Analysis Results")

            if issues:

                st.warning(
                    f"{len(issues)} issue(s) detected."
                )

                for index, issue in enumerate(
                    issues,
                    start=1
                ):

                    with st.expander(
                        f"Issue {index}: {issue['issue']}",
                        expanded=True
                    ):

                        st.write(
                            "**Severity:**",
                            issue["severity"]
                        )

                        st.write(
                            "**Suggestion:**",
                            issue["suggestion"]
                        )

            else:

                st.success(
                    "No issues detected by the current rules!"
                )

            st.divider()

            # Suggested correction
            st.subheader("✨ Suggested Correction")

            col1, col2 = st.columns(2)

            with col1:

                st.write("**Original Content**")

                st.text_area(
                    "Original",
                    value=content,
                    height=150,
                    disabled=True,
                    key="original_content"
                )

            with col2:

                st.write("**Improved Content**")

                st.text_area(
                    "Suggested Version",
                    value=corrected_content,
                    height=150,
                    disabled=True,
                    key="corrected_content"
                )

        else:

            st.error(
                "Please enter some content first."
            )


# ==========================================
# 7. REVIEW HISTORY
# ==========================================

elif menu == "Review History":

    st.header("📚 Review History")

    reviews = get_all_reviews()

    if reviews:

        st.write(
            f"Total saved reviews: {len(reviews)}"
        )

        for review in reviews:

            review_id = review[0]
            original = review[1]
            issues = json.loads(review[2] or "[]")
            corrected = review[3]
            review_date = review[4]

            with st.expander(
                f"Review #{review_id} | {review_date}"
            ):

                st.write("**Original Content:**")
                st.write(original)

                st.write("**Issues Detected:**")

                if issues:

                    for issue in issues:

                        st.write(
                            f"- {issue['issue']} "
                            f"({issue['severity']})"
                        )

                else:

                    st.success("No issues detected.")

                st.write("**Suggested Correction:**")
                st.write(corrected)

    else:

        st.info(
            "No review history available. Analyze content first."
        )


# ==========================================
# 8. BRAND GUIDELINES
# ==========================================

elif menu == "Brand Guidelines":

    st.header("📘 Brand Guidelines")

    st.write(
        "Create and manage multiple brand profiles."
    )

    tab1, tab2 = st.tabs(
        ["➕ Create Brand", "📚 Manage Brands"]
    )

    # --------------------------------------
    # CREATE BRAND
    # --------------------------------------

    with tab1:

        st.subheader("Create New Brand Profile")

        with st.form("brand_form"):

            brand_name = st.text_input(
                "Brand Name",
                placeholder="Example: TechNova"
            )

            brand_tone = st.selectbox(
                "Select Brand Tone",
                [
                    "Professional",
                    "Friendly",
                    "Luxury",
                    "Casual",
                    "Technical",
                    "Inspirational"
                ]
            )

            approved_input = st.text_area(
                "Approved Words",
                placeholder="Innovative, Reliable, Smart"
            )

            prohibited_input = st.text_area(
                "Prohibited Words",
                placeholder="Cheap, Bro, LOL"
            )

            brand_rules = st.text_area(
                "Additional Brand Rules",
                placeholder="Avoid exaggerated claims."
            )

            submitted = st.form_submit_button(
                "💾 Save Brand Profile",
                type="primary"
            )

            if submitted:

                if not brand_name.strip():

                    st.error("Please enter a brand name.")

                else:

                    approved_words = [
                        word.strip()
                        for word in approved_input.split(",")
                        if word.strip()
                    ]

                    prohibited_words = [
                        word.strip()
                        for word in prohibited_input.split(",")
                        if word.strip()
                    ]

                    success = save_brand(
                        brand_name.strip(),
                        brand_tone,
                        approved_words,
                        prohibited_words,
                        brand_rules.strip()
                    )

                    if success:

                        st.success(
                            f"{brand_name} saved successfully!"
                        )

                    else:

                        st.error(
                            "This brand name already exists."
                        )

    # --------------------------------------
    # MANAGE BRANDS
    # --------------------------------------

    with tab2:

        st.subheader("Saved Brand Profiles")

        brands = get_all_brands()

        if brands:

            st.write(
                f"Total registered brands: {len(brands)}"
            )

            for brand in brands:

                with st.expander(
                    f"🏢 {brand[1]}"
                ):

                    st.write("**Brand Tone:**", brand[2])

                    st.write("**Approved Words:**")
                    st.write(
                        ", ".join(
                            json.loads(brand[3] or "[]")
                        ) or "None"
                    )

                    st.write("**Prohibited Words:**")
                    st.write(
                        ", ".join(
                            json.loads(brand[4] or "[]")
                        ) or "None"
                    )

                    st.write("**Additional Rules:**")
                    st.write(
                        brand[5] or "No additional rules"
                    )

                    st.caption(
                        f"Created: {brand[6]}"
                    )

        else:

            st.info(
                "No brand profiles found. Create your first brand!"
            )


# ==========================================
# 9. FOOTER
# ==========================================

st.divider()

st.caption(
    "BrandLens AI | AI-Powered Brand Governance Platform"
)
