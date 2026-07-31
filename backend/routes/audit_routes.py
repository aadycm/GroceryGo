from flask import Blueprint
from models import AuditLog
from models.role import ADMIN
from auth.decorators import token_required, roles_required
from utils.responses import success
from utils.pagination import paginate_query, apply_sorting

bp = Blueprint("audit", __name__, url_prefix="/api/audit-logs")


@bp.get("")
@token_required
@roles_required(ADMIN)
def list_audit_logs():
    query = apply_sorting(AuditLog.query, AuditLog, default_field="created_at", default_dir="desc")
    items, meta = paginate_query(query)
    return success([a.to_dict() for a in items], meta=meta)
