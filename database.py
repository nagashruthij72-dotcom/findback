import sqlite3
from datetime import datetime


DATABASE = "lost_found.db"


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # --------------------------------------------------------
    # USERS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # --------------------------------------------------------
    # LOST ITEMS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lost_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            date_lost TEXT NOT NULL,
            image_path TEXT,
            contact TEXT,
            user_id INTEGER
        )
    """)

    # --------------------------------------------------------
    # FOUND ITEMS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS found_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            date_found TEXT NOT NULL,
            image_path TEXT,
            user_id INTEGER
        )
    """)

    # --------------------------------------------------------
    # NOTIFICATIONS TABLE
    # --------------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lost_item_id INTEGER,
            found_item_id INTEGER,
            message TEXT NOT NULL,
            match_score REAL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    # ========================================================
    # CHECK LOST ITEMS COLUMNS
    # ========================================================

    cursor.execute("PRAGMA table_info(lost_items)")

    lost_columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "image_path" not in lost_columns:

        cursor.execute("""
            ALTER TABLE lost_items
            ADD COLUMN image_path TEXT
        """)

    if "contact" not in lost_columns:

        cursor.execute("""
            ALTER TABLE lost_items
            ADD COLUMN contact TEXT
        """)

    if "user_id" not in lost_columns:

        cursor.execute("""
            ALTER TABLE lost_items
            ADD COLUMN user_id INTEGER
        """)

    # ========================================================
    # CHECK FOUND ITEMS COLUMNS
    # ========================================================

    cursor.execute("PRAGMA table_info(found_items)")

    found_columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "image_path" not in found_columns:

        cursor.execute("""
            ALTER TABLE found_items
            ADD COLUMN image_path TEXT
        """)

    if "user_id" not in found_columns:

        cursor.execute("""
            ALTER TABLE found_items
            ADD COLUMN user_id INTEGER
        """)

    # ========================================================
    # CHECK NOTIFICATION COLUMNS
    # ========================================================

    cursor.execute("PRAGMA table_info(notifications)")

    notification_columns = [
        column[1]
        for column in cursor.fetchall()
    ]

    if "lost_item_id" not in notification_columns:

        cursor.execute("""
            ALTER TABLE notifications
            ADD COLUMN lost_item_id INTEGER
        """)

    if "found_item_id" not in notification_columns:

        cursor.execute("""
            ALTER TABLE notifications
            ADD COLUMN found_item_id INTEGER
        """)

    # ========================================================
    # FIX OLD WINDOWS IMAGE PATHS
    # ========================================================

    # Old records may contain:
    #
    # static/uploads\lost\image.png
    #
    # Change them to:
    #
    # static/uploads/lost/image.png

    cursor.execute("""
        UPDATE lost_items
        SET image_path = REPLACE(image_path, char(92), '/')
        WHERE image_path LIKE '%' || char(92) || '%'
    """)

    cursor.execute("""
        UPDATE found_items
        SET image_path = REPLACE(image_path, char(92), '/')
        WHERE image_path LIKE '%' || char(92) || '%'
    """)

    # ========================================================
    # SAVE DATABASE
    # ========================================================

    connection.commit()
    connection.close()


# ============================================================
# USER FUNCTIONS
# ============================================================

def add_user(name, email, password):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users
        (name, email, password)
        VALUES (?, ?, ?)
    """, (
        name,
        email,
        password
    ))

    connection.commit()
    connection.close()


def get_user(email, password):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, email
        FROM users
        WHERE email = ?
        AND password = ?
    """, (
        email,
        password
    ))

    user = cursor.fetchone()

    connection.close()

    return user


def get_user_by_id(user_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, name, email
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()

    connection.close()

    return user


# ============================================================
# LOST ITEM FUNCTIONS
# ============================================================

def add_lost_item(
    item_name,
    category,
    description,
    location,
    date_lost,
    image_path=None,
    contact=None,
    user_id=None
):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO lost_items
        (
            item_name,
            category,
            description,
            location,
            date_lost,
            image_path,
            contact,
            user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item_name,
        category,
        description,
        location,
        date_lost,
        image_path,
        contact,
        user_id
    ))

    connection.commit()
    connection.close()


def get_lost_items():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            item_name,
            category,
            description,
            location,
            date_lost,
            image_path,
            contact,
            user_id
        FROM lost_items
        ORDER BY id DESC
    """)

    items = cursor.fetchall()

    connection.close()

    return items


def get_user_lost_items(user_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            item_name,
            category,
            description,
            location,
            date_lost,
            image_path,
            contact,
            user_id
        FROM lost_items
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    items = cursor.fetchall()

    connection.close()

    return items


def get_lost_item(item_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            item_name,
            category,
            description,
            location,
            date_lost,
            image_path,
            contact,
            user_id
        FROM lost_items
        WHERE id = ?
    """, (item_id,))

    item = cursor.fetchone()

    connection.close()

    return item


def update_lost_item(
    item_id,
    item_name,
    category,
    description,
    location,
    date_lost,
    contact
):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE lost_items
        SET
            item_name = ?,
            category = ?,
            description = ?,
            location = ?,
            date_lost = ?,
            contact = ?
        WHERE id = ?
    """, (
        item_name,
        category,
        description,
        location,
        date_lost,
        contact,
        item_id
    ))

    connection.commit()
    connection.close()


def delete_lost_item(item_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM lost_items
        WHERE id = ?
    """, (item_id,))

    connection.commit()
    connection.close()


# ============================================================
# FOUND ITEM FUNCTIONS
# ============================================================

def add_found_item(
    item_name,
    category,
    description,
    location,
    date_found,
    image_path=None,
    user_id=None
):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO found_items
        (
            item_name,
            category,
            description,
            location,
            date_found,
            image_path,
            user_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        item_name,
        category,
        description,
        location,
        date_found,
        image_path,
        user_id
    ))

    connection.commit()

    found_item_id = cursor.lastrowid

    connection.close()

    return found_item_id


def get_found_items():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            item_name,
            category,
            description,
            location,
            date_found,
            image_path,
            user_id
        FROM found_items
        ORDER BY id DESC
    """)

    items = cursor.fetchall()

    connection.close()

    return items


def get_user_found_items(user_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            item_name,
            category,
            description,
            location,
            date_found,
            image_path,
            user_id
        FROM found_items
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    items = cursor.fetchall()

    connection.close()

    return items


def get_found_item(item_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            item_name,
            category,
            description,
            location,
            date_found,
            image_path,
            user_id
        FROM found_items
        WHERE id = ?
    """, (item_id,))

    item = cursor.fetchone()

    connection.close()

    return item


def delete_found_item(item_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM found_items
        WHERE id = ?
    """, (item_id,))

    connection.commit()
    connection.close()


# ============================================================
# NOTIFICATION FUNCTIONS
# ============================================================

def add_notification(
    user_id,
    message,
    match_score,
    lost_item_id=None,
    found_item_id=None
):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cursor.execute("""
        INSERT INTO notifications
        (
            user_id,
            lost_item_id,
            found_item_id,
            message,
            match_score,
            is_read,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, 0, ?)
    """, (
        user_id,
        lost_item_id,
        found_item_id,
        message,
        match_score,
        created_at
    ))

    connection.commit()
    connection.close()


def get_user_notifications(user_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            message,
            match_score,
            is_read,
            created_at,
            lost_item_id,
            found_item_id
        FROM notifications
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    notifications = cursor.fetchall()

    connection.close()

    return notifications


def get_unread_notification_count(user_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM notifications
        WHERE user_id = ?
        AND is_read = 0
    """, (user_id,))

    count = cursor.fetchone()[0]

    connection.close()

    return count


def mark_notifications_read(user_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE notifications
        SET is_read = 1
        WHERE user_id = ?
    """, (user_id,))

    connection.commit()
    connection.close()