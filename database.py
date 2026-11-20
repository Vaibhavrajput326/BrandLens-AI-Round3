import sqlite3
import json
from datetime import datetime

DB_NAME = "brandlens.db"


def get_connection():
    connection = sqlite3.connect(DB_NAME, timeout=20)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    # Existing review history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_content TEXT NOT NULL,
            issues TEXT,
            corrected_content TEXT,
            review_date TEXT
        )
    """)

    # Existing brand profiles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL UNIQUE,
            brand_tone TEXT,
            approved_words TEXT,
            prohibited_words TEXT,
            brand_rules TEXT,
            created_at TEXT
        )
    """)

    # Safe migration: add new review fields to existing table
    cursor.execute("PRAGMA table_info(reviews)")
    review_columns = [row[1] for row in cursor.fetchall()]

    if "brand_name" not in review_columns:
        cursor.execute(
            "ALTER TABLE reviews ADD COLUMN brand_name TEXT"
        )

    if "review_status" not in review_columns:
        cursor.execute("""
            ALTER TABLE reviews
            ADD COLUMN review_status TEXT DEFAULT 'Pending'
        """)

    if "final_content" not in review_columns:
        cursor.execute(
            "ALTER TABLE reviews ADD COLUMN final_content TEXT"
        )

    # Brand Knowledge Base
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand_name TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            content TEXT NOT NULL,
            source TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # Human review audit trail
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            previous_status TEXT,
            new_status TEXT,
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (review_id) REFERENCES reviews(id)
                ON DELETE CASCADE
        )
    """)

    connection.commit()
    connection.close()


def save_review(
    original_content,
    issues,
    corrected_content,
    brand_name=None
):
    connection = get_connection()
    cursor = connection.cursor()

    review_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO reviews (
            original_content,
            issues,
            corrected_content,
            review_date,
            brand_name,
            review_status,
            final_content
        )
        VALUES (?, ?, ?, ?, ?, 'Pending', ?)
    """, (
        original_content,
        json.dumps(issues),
        corrected_content,
        review_date,
        brand_name,
        corrected_content
    ))

    review_id = cursor.lastrowid

    cursor.execute("""
        INSERT INTO audit_log (
            review_id, action, previous_status,
            new_status, notes, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        review_id,
        "Review Created",
        None,
        "Pending",
        "Content analysis completed",
        review_date
    ))

    connection.commit()
    connection.close()

    return review_id


def get_all_reviews():
    connection = get_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT * FROM reviews ORDER BY id DESC
    """)

    reviews = cursor.fetchall()
    connection.close()
    return reviews


def get_review_count():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM reviews")
    count = cursor.fetchone()[0]

    connection.close()
    return count


def get_review_by_id(review_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT * FROM reviews WHERE id = ?",
        (review_id,)
    )

    review = cursor.fetchone()
    connection.close()
    return review


def update_review_status(review_id, new_status, notes=""):
    allowed_statuses = ["Pending", "Approved", "Rejected"]

    if new_status not in allowed_statuses:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT review_status FROM reviews WHERE id = ?",
        (review_id,)
    )
    row = cursor.fetchone()

    if not row:
        connection.close()
        return False

    previous_status = row[0] or "Pending"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE reviews
        SET review_status = ?
        WHERE id = ?
    """, (new_status, review_id))

    cursor.execute("""
        INSERT INTO audit_log (
            review_id, action, previous_status,
            new_status, notes, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        review_id,
        "Status Updated",
        previous_status,
        new_status,
        notes,
        now
    ))

    connection.commit()
    connection.close()
    return True


def update_final_content(review_id, final_content, notes=""):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT final_content, review_status FROM reviews WHERE id = ?",
        (review_id,)
    )
    row = cursor.fetchone()

    if not row:
        connection.close()
        return False

    previous_content, status = row

    cursor.execute("""
        UPDATE reviews
        SET final_content = ?
        WHERE id = ?
    """, (final_content, review_id))

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO audit_log (
            review_id, action, previous_status,
            new_status, notes, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        review_id,
        "Final Content Edited",
        status,
        status,
        notes or "Final content was edited",
        now
    ))

    connection.commit()
    connection.close()
    return True


def get_audit_log(review_id=None):
    connection = get_connection()
    cursor = connection.cursor()

    if review_id is None:
        cursor.execute("""
            SELECT * FROM audit_log ORDER BY id DESC
        """)
    else:
        cursor.execute("""
            SELECT * FROM audit_log
            WHERE review_id = ?
            ORDER BY id DESC
        """, (review_id,))

    logs = cursor.fetchall()
    connection.close()
    return logs


def add_knowledge_item(
    brand_name,
    title,
    category,
    content,
    source=""
):
    if not all([
        brand_name.strip(),
        title.strip(),
        content.strip()
    ]):
        return False

    connection = get_connection()
    cursor = connection.cursor()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO knowledge_base (
            brand_name, title, category,
            content, source, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        brand_name.strip(),
        title.strip(),
        category.strip() or "General",
        content.strip(),
        source.strip(),
        now
    ))

    connection.commit()
    connection.close()
    return True


def get_knowledge_items(brand_name=None):
    connection = get_connection()
    cursor = connection.cursor()

    if brand_name:
        cursor.execute("""
            SELECT * FROM knowledge_base
            WHERE brand_name = ?
            ORDER BY id DESC
        """, (brand_name,))
    else:
        cursor.execute("""
            SELECT * FROM knowledge_base
            ORDER BY id DESC
        """)

    items = cursor.fetchall()
    connection.close()
    return items


def delete_knowledge_item(item_id):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM knowledge_base WHERE id = ?",
        (item_id,)
    )

    deleted = cursor.rowcount > 0
    connection.commit()
    connection.close()
    return deleted


# Initialize and safely migrate database
initialize_database()

def save_brand(
    brand_name,
    brand_tone,
    approved_words,
    prohibited_words,
    brand_rules
):
    connection = get_connection()
    cursor = connection.cursor()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute("""
            INSERT INTO brands (
                brand_name,
                brand_tone,
                approved_words,
                prohibited_words,
                brand_rules,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            brand_name,
            brand_tone,
            json.dumps(approved_words),
            json.dumps(prohibited_words),
            brand_rules,
            created_at
        ))

        connection.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        connection.close()


def get_all_brands():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM brands ORDER BY id DESC
    """)

    brands = cursor.fetchall()
    connection.close()
    return brands


def get_brand_by_name(brand_name):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT * FROM brands WHERE brand_name = ?
    """, (brand_name,))

    brand = cursor.fetchone()
    connection.close()
    return brand


# =====================================================
# DEMO WORKSPACE DATA (IDEMPOTENT)
# =====================================================
def initialize_demo_data():
    """Create judge-friendly sample data once, without overwriting user data."""
    demo_brand = "TechNova"

# Create the sample brand only when it does not already exist.
    if get_brand_by_name(demo_brand) is None:
        save_brand(
            demo_brand,
            "Professional",
            ["Reliable", "Innovative", "Smart"],
            ["Cheap", "Fake", "Guaranteed"],
            "Use accurate product specifications. Avoid exaggerated or unsupported claims."
        )

    # Add the evidence item only once.
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM knowledge_base WHERE brand_name = ? AND title = ?",
        (demo_brand, "Battery Capacity")
    )
    knowledge_exists = cursor.fetchone() is not None
    connection.close()

    if not knowledge_exists:
        add_knowledge_item(
            demo_brand,
            "Battery Capacity",
            "Product Fact",
            "TechNova smartphone has a 5000 mAh battery capacity.",
            "Demo sample evidence — replace with an official source before real-world use"
        )

    # Sample 1: intentionally inconsistent claim, left Pending for human review.
    mismatch_content = (
        "[DEMO EXAMPLE] TechNova smartphone comes with a 10000 mAh battery capacity."
    )
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM reviews WHERE original_content = ? AND brand_name = ?",
        (mismatch_content, demo_brand)
    )
    mismatch_exists = cursor.fetchone() is not None
    connection.close()

    if not mismatch_exists:
        mismatch_issues = [{
            "issue": "Potential factual mismatch: claimed 10000 mAh vs stored 5000 mAh",
            "category": "Knowledge Base Verification",
            "severity": "High",
            "evidence": "Submitted claim: 10000 mAh; stored brand evidence: 5000 mAh",
            "suggestion": "Verify the official product specification and correct the claim before publication."
        }]
        mismatch_id = save_review(
            mismatch_content,
            mismatch_issues,
            "[DEMO SUGGESTION] Verify the battery capacity against the official product specification.",
            demo_brand
        )
        update_final_content(
            mismatch_id,
            "[DEMO PENDING] Battery capacity requires confirmation against the official specification.",
            "Demo record initialized for judge walkthrough"
        )

    # Sample 2: clean example, marked Approved to demonstrate workflow states.
    clean_content = (
        "[DEMO EXAMPLE] TechNova focuses on reliable and innovative smartphone experiences."
    )
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT id FROM reviews WHERE original_content = ? AND brand_name = ?",
        (clean_content, demo_brand)
    )
    clean_exists = cursor.fetchone() is not None
    connection.close()

    if not clean_exists:
        clean_id = save_review(
            clean_content,
            [],
            clean_content,
            demo_brand
        )
        update_final_content(
            clean_id,
            clean_content,
            "Demo record initialized for judge walkthrough"
        )
        update_review_status(
            clean_id,
            "Approved",
            "Demo approval showing the human review workflow"
        )

