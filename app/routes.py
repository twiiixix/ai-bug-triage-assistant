from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from app import db
from app.ai_service import analyze_bug_with_ai
from app.models import BugReport, User
from app.services import analyze_bug

main_bp = Blueprint("main", __name__)
ALLOWED_STATUSES = {"Open", "In Progress", "Resolved"}


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Complete every required field.", "error")
        elif password != confirm_password:
            flash("The passwords do not match.", "error")
        elif len(password) < 8:
            flash("Use a password with at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account already exists for that email.", "error")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Your account was created.", "success")
            return redirect(url_for("main.home"))

    return render_template("register.html")


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash("The email or password is incorrect.", "error")
        else:
            login_user(user, remember=remember)
            return redirect(url_for("main.home"))

    return render_template("login.html")


@main_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.login"))


@main_bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    bug_data = None
    analysis = None

    if request.method == "POST":
        bug_data, analysis = process_bug_submission()

    search_term = request.args.get("search", "").strip()
    severity_filter = request.args.get("severity", "").strip()
    status_filter = request.args.get("status", "").strip()

    return render_template(
        "index.html",
        bug=bug_data,
        analysis=analysis,
        recent_bugs=get_filtered_bugs(search_term, severity_filter, status_filter),
        search_term=search_term,
        severity_filter=severity_filter,
        status_filter=status_filter,
        analytics=get_analytics(),
    )


@main_bp.route("/bugs/<int:bug_id>/status", methods=["POST"])
@login_required
def update_bug_status(bug_id: int):
    report = get_owned_report_or_404(bug_id)
    new_status = request.form.get("status", "").strip()

    if new_status in ALLOWED_STATUSES:
        report.status = new_status
        db.session.commit()

    return redirect(url_for("main.home"))


@main_bp.route("/bugs/<int:bug_id>/edit", methods=["GET", "POST"])
@login_required
def edit_bug(bug_id: int):
    report = get_owned_report_or_404(bug_id)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        status = request.form.get("status", "").strip()

        if title and description:
            analysis = analyze_bug_with_ai(title, description)
            if analysis is None:
                analysis = analyze_bug(title, description)

            report.title = title
            report.description = description
            report.summary = analysis["summary"]
            report.severity = analysis["severity"]
            report.category = analysis["category"]

            if status in ALLOWED_STATUSES:
                report.status = status

            db.session.commit()
            flash("The report was updated.", "success")
            return redirect(url_for("main.home"))

        flash("Title and description are required.", "error")

    return render_template("edit_bug.html", report=report)


@main_bp.route("/bugs/<int:bug_id>/delete", methods=["POST"])
@login_required
def delete_bug(bug_id: int):
    report = get_owned_report_or_404(bug_id)
    db.session.delete(report)
    db.session.commit()
    flash("The report was deleted.", "success")
    return redirect(url_for("main.home"))


def get_owned_report_or_404(bug_id: int) -> BugReport:
    return BugReport.query.filter_by(
        id=bug_id,
        user_id=current_user.id,
    ).first_or_404()


def process_bug_submission():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not title or not description:
        flash("Title and description are required.", "error")
        return None, None

    bug_data = {"title": title, "description": description}

    analysis = analyze_bug_with_ai(title, description)
    if analysis is None:
        analysis = analyze_bug(title, description)

    report = BugReport(
        title=title,
        description=description,
        summary=analysis["summary"],
        severity=analysis["severity"],
        category=analysis["category"],
        status="Open",
        user_id=current_user.id,
    )

    db.session.add(report)
    db.session.commit()

    return bug_data, analysis


def get_filtered_bugs(search_term: str, severity_filter: str, status_filter: str):
    query = BugReport.query.filter_by(user_id=current_user.id)

    if search_term:
        like_term = f"%{search_term}%"
        query = query.filter(
            or_(
                BugReport.title.ilike(like_term),
                BugReport.description.ilike(like_term),
                BugReport.summary.ilike(like_term),
                BugReport.category.ilike(like_term),
            )
        )

    if severity_filter:
        query = query.filter(BugReport.severity == severity_filter)

    if status_filter:
        query = query.filter(BugReport.status == status_filter)

    return query.order_by(BugReport.created_at.desc()).all()


def get_analytics() -> dict:
    base = BugReport.query.filter_by(user_id=current_user.id)

    return {
        "total": base.count(),
        "critical": base.filter_by(severity="Critical").count(),
        "open": base.filter_by(status="Open").count(),
        "resolved": base.filter_by(status="Resolved").count(),
    }
