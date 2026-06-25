"""HTTP routes for nonprofit dashboard platform (JWT-protected)."""
from flask import Blueprint, jsonify, request, Response

from auth import require_auth
import services.auth_service as auth_service
import services.nonprofit_service as nonprofit_service
import services.csv_import_service as csv_import_service

bp = Blueprint("api", __name__)
nonprofit_bp = Blueprint("nonprofit_api", __name__)


def _value_error_response(exc):
    msg = str(exc)
    if msg == "Forbidden":
        return jsonify({"error": msg}), 403
    if msg.endswith("not found") or "not found" in msg.lower():
        return jsonify({"error": msg}), 404
    return jsonify({"error": msg}), 400


@bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    try:
        result = auth_service.login(data.get("email", ""), data.get("password", ""))
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


@nonprofit_bp.route("/nonprofits/public", methods=["GET"])
def list_nonprofits_public():
    try:
        return jsonify(nonprofit_service.list_nonprofits_public())
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits", methods=["GET"])
@require_auth
def list_nonprofits():
    try:
        return jsonify(nonprofit_service.list_nonprofits())
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits", methods=["POST"])
@require_auth
def create_nonprofit():
    data = request.get_json() or {}
    try:
        result = nonprofit_service.create_nonprofit(
            data.get("name"),
            data.get("mission"),
            data.get("location"),
            data.get("slug"),
        )
        return jsonify(result), 201
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>", methods=["GET"])
@require_auth
def get_nonprofit(nonprofit_id):
    try:
        return jsonify(nonprofit_service.get_nonprofit(nonprofit_id))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>", methods=["PUT"])
@require_auth
def update_nonprofit(nonprofit_id):
    data = request.get_json() or {}
    try:
        return jsonify(nonprofit_service.update_nonprofit(nonprofit_id, data))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/dashboard", methods=["GET"])
@require_auth
def get_dashboard(nonprofit_id):
    try:
        week_start = request.args.get("weekStart")
        return jsonify(nonprofit_service.get_dashboard(nonprofit_id, week_start=week_start))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/metrics", methods=["PUT"])
@require_auth
def update_metrics(nonprofit_id):
    data = request.get_json() or {}
    try:
        return jsonify(nonprofit_service.update_metrics(nonprofit_id, data))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/programs", methods=["GET"])
@require_auth
def list_programs(nonprofit_id):
    try:
        return jsonify(nonprofit_service.list_programs(nonprofit_id))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/programs", methods=["POST"])
@require_auth
def create_program(nonprofit_id):
    data = request.get_json() or {}
    try:
        result = nonprofit_service.create_program(
            nonprofit_id,
            data.get("name"),
            data.get("status", "active"),
            data.get("participants", 0),
            data.get("budget", 0),
        )
        return jsonify(result), 201
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/programs/<int:program_id>", methods=["PUT"])
@require_auth
def update_program(nonprofit_id, program_id):
    data = request.get_json() or {}
    try:
        return jsonify(nonprofit_service.update_program(nonprofit_id, program_id, data))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/programs/<int:program_id>", methods=["DELETE"])
@require_auth
def delete_program(nonprofit_id, program_id):
    try:
        return jsonify(nonprofit_service.delete_program(nonprofit_id, program_id))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/report", methods=["GET"])
@require_auth
def download_report(nonprofit_id):
    try:
        week_start = request.args.get("weekStart")
        pdf_bytes = nonprofit_service.generate_report_pdf(nonprofit_id, week_start=week_start)
        filename = "nonprofit-dashboard-report.pdf"
        if week_start:
            filename = f"nonprofit-dashboard-report-{week_start}.pdf"
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/members", methods=["GET"])
@require_auth
def list_org_members(nonprofit_id):
    try:
        return jsonify(nonprofit_service.list_org_members(nonprofit_id))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/members", methods=["POST"])
@require_auth
def create_org_member(nonprofit_id):
    data = request.get_json() or {}
    try:
        result = nonprofit_service.create_org_member(nonprofit_id, data)
        return jsonify(result), 201
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/members/<int:user_id>", methods=["PUT"])
@require_auth
def update_org_member(nonprofit_id, user_id):
    data = request.get_json() or {}
    try:
        return jsonify(nonprofit_service.update_org_member(nonprofit_id, user_id, data))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/<int:nonprofit_id>/members/<int:user_id>", methods=["DELETE"])
@require_auth
def delete_org_member(nonprofit_id, user_id):
    try:
        return jsonify(nonprofit_service.delete_org_member(nonprofit_id, user_id))
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/users", methods=["GET"])
@require_auth
def list_users():
    try:
        return jsonify(nonprofit_service.list_users())
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/import/template", methods=["GET"])
@require_auth
def import_template():
    try:
        csv_text = csv_import_service.get_template_csv()
        return Response(
            csv_text,
            mimetype="text/csv",
            headers={"Content-Disposition": 'attachment; filename="nonprofit-import-template.csv"'},
        )
    except ValueError as e:
        return _value_error_response(e)


@nonprofit_bp.route("/nonprofits/import", methods=["POST"])
@require_auth
def import_nonprofit_csv():
    if "file" not in request.files:
        return jsonify({"error": "file is required"}), 400
    upload = request.files["file"]
    if not upload.filename:
        return jsonify({"error": "file is required"}), 400

    mode = request.args.get("mode", "auto")
    nonprofit_id = request.args.get("nonprofitId", type=int)

    try:
        parsed = csv_import_service.parse_csv(upload.stream)
        result = csv_import_service.import_csv(parsed, mode=mode, nonprofit_id=nonprofit_id)
        return jsonify(result)
    except ValueError as e:
        return _value_error_response(e)
