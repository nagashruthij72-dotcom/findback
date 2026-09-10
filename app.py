import os
import uuid
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.utils import secure_filename

from database import (
    create_database,

    add_user,
    get_user,
    get_user_by_id,

    add_lost_item,
    get_lost_items,
    get_user_lost_items,
    get_lost_item,
    update_lost_item,
    delete_lost_item,

    add_found_item,
    get_found_items,
    get_user_found_items,
    get_found_item,
    delete_found_item,

    add_notification,
    get_user_notifications,
    get_unread_notification_count,
    mark_notifications_read
)

from ai_matching import (
    calculate_similarity,
    normalize_text
)

from image_matching import (
    calculate_image_similarity
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.secret_key = "findback-secret-key-change-this"


# ============================================================
# UPLOAD SETTINGS
# ============================================================

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}


# ============================================================
# DATABASE
# ============================================================

create_database()


# ============================================================
# IMAGE FUNCTIONS
# ============================================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def save_uploaded_image(image, folder):

    if not image:
        return None

    if not image.filename:
        return None

    if not allowed_file(image.filename):
        return None

    original_filename = secure_filename(
        image.filename
    )

    if "." not in original_filename:
        return None

    extension = (
        original_filename
        .rsplit(".", 1)[1]
        .lower()
    )

    unique_filename = (
        str(uuid.uuid4())
        + "."
        + extension
    )

    upload_folder = os.path.join(
        "static",
        "uploads",
        folder
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    file_path = os.path.join(
        upload_folder,
        unique_filename
    )

    image.save(file_path)

    return file_path.replace(
        "\\",
        "/"
    )


# ============================================================
# LOGIN REQUIRED
# ============================================================

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please login to continue.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    return decorated_function


# ============================================================
# NOTIFICATION COUNT
# ============================================================

@app.context_processor
def inject_notification_count():

    count = 0

    if session.get("user_id"):

        count = get_unread_notification_count(
            session["user_id"]
        )

    return {
        "notification_count": count
    }


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# REGISTER
# ============================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if not name:

            return render_template(
                "register.html",
                error="Please enter your name."
            )

        if not email:

            return render_template(
                "register.html",
                error="Please enter your email."
            )

        if not password:

            return render_template(
                "register.html",
                error="Please enter a password."
            )

        try:

            add_user(
                name,
                email,
                password
            )

            flash(
                "Registration successful. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Exception:

            return render_template(
                "register.html",
                error="Email already registered."
            )

    return render_template(
        "register.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        user = get_user(
            email,
            password
        )

        if user:

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_email"] = user[2]

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("home")
            )

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("home")
    )


# ============================================================
# REPORT LOST
# ============================================================

@app.route(
    "/report-lost",
    methods=["GET", "POST"]
)
@login_required
def report_lost():

    if request.method == "POST":

        item_name = request.form.get(
            "item_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        date_lost = request.form.get(
            "date_lost",
            ""
        ).strip()

        contact = request.form.get(
            "contact",
            ""
        ).strip()

        image = request.files.get(
            "image"
        )

        user_id = session["user_id"]

        if not item_name:

            return render_template(
                "report-lost.html",
                error="Please enter the item name."
            )

        if not category:

            return render_template(
                "report-lost.html",
                error="Please select a category."
            )

        if not description:

            return render_template(
                "report-lost.html",
                error="Please enter a description."
            )

        if not location:

            return render_template(
                "report-lost.html",
                error="Please enter the location."
            )

        if not date_lost:

            return render_template(
                "report-lost.html",
                error="Please enter the date lost."
            )

        image_path = save_uploaded_image(
            image,
            "lost"
        )

        add_lost_item(
            item_name,
            category,
            description,
            location,
            date_lost,
            image_path,
            contact,
            user_id
        )

        flash(
            "Lost item reported successfully.",
            "success"
        )

        return redirect(
            url_for("lost_items")
        )

    return render_template(
        "report-lost.html"
    )


# ============================================================
# LOST ITEMS
# ============================================================

@app.route("/lost-items")
def lost_items():

    items = get_lost_items()

    return render_template(
        "lost-items.html",
        items=items
    )


# ============================================================
# LOST ITEM DETAILS
# ============================================================

@app.route(
    "/lost-item/<int:item_id>"
)
def lost_item_details(item_id):

    item = get_lost_item(
        item_id
    )

    if not item:

        return (
            "Lost item not found",
            404
        )

    return render_template(
        "lost-item-details.html",
        item=item
    )


# ============================================================
# EDIT LOST
# ============================================================

@app.route(
    "/edit-lost/<int:item_id>",
    methods=["GET", "POST"]
)
@login_required
def edit_lost(item_id):

    item = get_lost_item(
        item_id
    )

    if not item:

        return (
            "Lost item not found",
            404
        )

    if item[8] != session["user_id"]:

        flash(
            "You can only edit your own reports.",
            "error"
        )

        return redirect(
            url_for("my_reports")
        )

    if request.method == "POST":

        item_name = request.form.get(
            "item_name",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        date_lost = request.form.get(
            "date_lost",
            ""
        ).strip()

        contact = request.form.get(
            "contact",
            ""
        ).strip()

        update_lost_item(
            item_id,
            item_name,
            category,
            description,
            location,
            date_lost,
            contact
        )

        flash(
            "Lost item updated successfully.",
            "success"
        )

        return redirect(
            url_for("my_reports")
        )

    return render_template(
        "edit-lost.html",
        item=item
    )


# ============================================================
# DELETE LOST
# ============================================================

@app.route(
    "/delete-lost/<int:item_id>",
    methods=["POST", "GET"]
)
@login_required
def delete_lost(item_id):

    item = get_lost_item(
        item_id
    )

    if not item:

        return (
            "Lost item not found",
            404
        )

    if item[8] != session["user_id"]:

        flash(
            "You can only delete your own reports.",
            "error"
        )

        return redirect(
            url_for("my_reports")
        )

    delete_lost_item(
        item_id
    )

    flash(
        "Lost item deleted successfully.",
        "success"
    )

    return redirect(
        url_for("my_reports")
    )


# ============================================================
# REPORT FOUND
# ============================================================

@app.route(
    "/report-found",
    methods=["GET", "POST"]
)
@login_required
def report_found():

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "report-found.html"
        )

    # --------------------------------------------------------
    # FORM DATA
    # --------------------------------------------------------

    item_name = request.form.get(
        "item_name",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    date_found = request.form.get(
        "date_found",
        ""
    ).strip()

    image = request.files.get(
        "image"
    )

    found_user_id = session["user_id"]

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not item_name:

        return render_template(
            "report-found.html",
            error="Please enter the item name."
        )

    if not category:

        return render_template(
            "report-found.html",
            error="Please select a category."
        )

    if not description:

        return render_template(
            "report-found.html",
            error="Please enter the description."
        )

    if not location:

        return render_template(
            "report-found.html",
            error="Please enter the location."
        )

    if not date_found:

        return render_template(
            "report-found.html",
            error="Please enter the date found."
        )

    # --------------------------------------------------------
    # SAVE IMAGE
    # --------------------------------------------------------

    image_path = save_uploaded_image(
        image,
        "found"
    )

    # --------------------------------------------------------
    # SAVE FOUND ITEM
    # --------------------------------------------------------

    found_item_id = add_found_item(
        item_name,
        category,
        description,
        location,
        date_found,
        image_path,
        found_user_id
    )

    print()
    print("========================================")
    print("FOUND ITEM SAVED")
    print("========================================")
    print("Found User ID:", found_user_id)
    print("Found Item ID:", found_item_id)
    print("Name:", item_name)
    print("Category:", category)
    print("Location:", location)
    print("Image:", image_path)
    print("========================================")

    # ========================================================
    # GET LOST ITEMS
    # ========================================================

    lost_items_list = get_lost_items()

    print(
        "Total lost items:",
        len(lost_items_list)
    )

    matches = []

    # ========================================================
    # MATCHING
    # ========================================================

    for lost_item in lost_items_list:

        lost_id = lost_item[0]
        lost_name = lost_item[1]
        lost_category = lost_item[2]
        lost_description = lost_item[3]
        lost_location = lost_item[4]
        lost_date = lost_item[5]
        lost_image = lost_item[6]
        lost_contact = lost_item[7]
        lost_user_id = lost_item[8]

        # ----------------------------------------------------
        # NEVER MATCH AGAINST SAME USER
        # ----------------------------------------------------

        if lost_user_id == found_user_id:

            print(
                "Skipping own lost item:",
                lost_name,
                "| User ID:",
                lost_user_id
            )

            continue

        # ----------------------------------------------------
        # TEXT MATCH
        # ----------------------------------------------------

        text_score = calculate_similarity(

            lost_name,
            lost_description,
            lost_category,
            lost_location,

            item_name,
            description,
            category,
            location
        )

        print(
            "TEXT MATCH:",
            lost_name,
            "->",
            text_score,
            "%"
        )

        # ----------------------------------------------------
        # IMAGE MATCH
        # ----------------------------------------------------

        image_score = 0

        if (
            image_path
            and lost_image
            and os.path.exists(image_path)
            and os.path.exists(lost_image)
        ):

            try:

                image_score = calculate_image_similarity(
                    lost_image,
                    image_path
                )

                print(
                    "IMAGE MATCH:",
                    lost_name,
                    "->",
                    image_score,
                    "%"
                )

            except Exception as error:

                print(
                    "IMAGE MATCH ERROR:",
                    error
                )

                image_score = 0

        # ----------------------------------------------------
        # FINAL SCORE
        # ----------------------------------------------------

        if image_score > 0:

            final_score = (
                text_score * 0.65
                + image_score * 0.35
            )

        else:

            final_score = text_score

        # ----------------------------------------------------
        # CATEGORY BONUS
        # ----------------------------------------------------

        if (
            normalize_text(lost_category)
            == normalize_text(category)
            and normalize_text(category)
        ):

            final_score += 2

        # ----------------------------------------------------
        # LOCATION BONUS
        # ----------------------------------------------------

        if (
            normalize_text(lost_location)
            == normalize_text(location)
            and normalize_text(location)
        ):

            final_score += 2

        final_score = min(
            final_score,
            100
        )

        final_score = round(
            final_score,
            2
        )

        print(
            "FINAL MATCH:",
            lost_name,
            "->",
            final_score,
            "%"
        )

        # ----------------------------------------------------
        # MATCH LEVEL
        # ----------------------------------------------------

        if final_score >= 80:

            match_level = "Very Strong Match"

        elif final_score >= 65:

            match_level = "Strong Match"

        elif final_score >= 40:

            match_level = "Possible Match"

        else:

            match_level = "Low Match"

        # ----------------------------------------------------
        # SAVE MATCH
        # ----------------------------------------------------

        if final_score >= 40:

            matches.append({

                "lost_id": lost_id,

                "name": lost_name,

                "category": lost_category,

                "description": lost_description,

                "location": lost_location,

                "date_lost": lost_date,

                "image_path": lost_image,

                "contact": lost_contact,

                "score": final_score,

                "match_level": match_level

            })

    # ========================================================
    # SORT MATCHES
    # ========================================================

    matches.sort(
        key=lambda match: match["score"],
        reverse=True
    )

    # ========================================================
    # TOP 3
    # ========================================================

    matches = matches[:3]

    # ========================================================
    # PRINT RESULTS
    # ========================================================

    print()
    print("========================================")
    print("AI MATCH RESULTS")
    print("========================================")

    print(
        "Matches found:",
        len(matches)
    )

    for match in matches:

        print(
            match["name"],
            "->",
            match["score"],
            "%",
            "->",
            match["match_level"]
        )

    print("========================================")
    print()

    # ========================================================
    # CREATE NOTIFICATIONS
    # ========================================================

    print("========================================")
    print("CREATING NOTIFICATIONS")
    print("========================================")

    notifications_created = 0

    for match in matches:

        lost_item = get_lost_item(
            match["lost_id"]
        )

        if not lost_item:

            print(
                "Lost item not found:",
                match["lost_id"]
            )

            continue

        # ----------------------------------------------------
        # OWNER OF LOST ITEM
        # ----------------------------------------------------

        lost_user_id = lost_item[8]

        print(
            "Matched lost item:",
            match["name"]
        )

        print(
            "Lost item owner:",
            lost_user_id
        )

        print(
            "Found item reporter:",
            found_user_id
        )

        # ----------------------------------------------------
        # SAFETY CHECK
        # ----------------------------------------------------

        if not lost_user_id:

            print(
                "NO USER ID - notification skipped"
            )

            continue

        if lost_user_id == found_user_id:

            print(
                "Same user - notification skipped"
            )

            continue

        # ====================================================
        # NOTIFICATION MESSAGE
        # ====================================================

        notification_message = (
            f"A found item may match your lost item "
            f"'{match['name']}'. "
            f"AI Match: {match['score']}% "
            f"({match['match_level']})."
        )

        # ====================================================
        # SAVE NOTIFICATION
        # ====================================================

        try:

            add_notification(

                lost_user_id,

                notification_message,

                match["score"],

                lost_item_id=match["lost_id"],

                found_item_id=found_item_id

            )

            notifications_created += 1

            print(
                "NOTIFICATION CREATED SUCCESSFULLY!"
            )

            print(
                "Notification User ID:",
                lost_user_id
            )

            print(
                "Notification Score:",
                match["score"]
            )

        except Exception as error:

            print(
                "NOTIFICATION ERROR:",
                error
            )

    print(
        "Total notifications created:",
        notifications_created
    )

    print("========================================")
    print()

    # ========================================================
    # SHOW MATCH RESULTS
    # ========================================================

    return render_template(

        "report-found.html",

        matches=matches,

        submitted=True

    )


# ============================================================
# FOUND ITEMS
# ============================================================

@app.route("/found-items")
def found_items():

    items = get_found_items()

    return render_template(
        "found-items.html",
        items=items
    )


# ============================================================
# DELETE FOUND
# ============================================================

@app.route(
    "/delete-found/<int:item_id>",
    methods=["POST", "GET"]
)
@login_required
def delete_found(item_id):

    item = get_found_item(
        item_id
    )

    if not item:

        return (
            "Found item not found",
            404
        )

    if item[7] != session["user_id"]:

        flash(
            "You can only delete your own reports.",
            "error"
        )

        return redirect(
            url_for("my_reports")
        )

    delete_found_item(
        item_id
    )

    flash(
        "Found item deleted successfully.",
        "success"
    )

    return redirect(
        url_for("my_reports")
    )


# ============================================================
# MY REPORTS
# ============================================================

@app.route("/my-reports")
@login_required
def my_reports():

    user_id = session["user_id"]

    lost_items = get_user_lost_items(
        user_id
    )

    found_items_list = get_user_found_items(
        user_id
    )

    return render_template(

        "my-reports.html",

        lost_items=lost_items,

        found_items=found_items_list

    )


# ============================================================
# NOTIFICATIONS
# ============================================================

@app.route("/notifications")
@login_required
def notifications():

    user_id = session["user_id"]

    notification_list = get_user_notifications(
        user_id
    )

    print()
    print("========================================")
    print("NOTIFICATION PAGE")
    print("Logged-in User ID:", user_id)
    print(
        "Notifications:",
        len(notification_list)
    )
    print("========================================")

    return render_template(

        "notifications.html",

        notifications=notification_list

    )


# ============================================================
# MARK NOTIFICATIONS READ
# ============================================================

@app.route(
    "/notifications/read",
    methods=["POST", "GET"]
)
@login_required
def mark_notifications_as_read():

    user_id = session["user_id"]

    mark_notifications_read(
        user_id
    )

    return redirect(
        url_for("notifications")
    )


# ============================================================
# 404
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return render_template(
        "index.html"
    ), 404


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )