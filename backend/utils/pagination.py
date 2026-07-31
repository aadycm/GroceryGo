from flask import request


def paginate_query(query, default_per_page=20, max_per_page=100):
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get("per_page", default_per_page))
    except ValueError:
        per_page = default_per_page
    per_page = min(max(per_page, 1), max_per_page)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    meta = {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total_items": pagination.total,
        "total_pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_prev": pagination.has_prev,
    }
    return pagination.items, meta


def apply_sorting(query, model, default_field="id", default_dir="asc"):
    sort_by = request.args.get("sort_by", default_field)
    sort_dir = request.args.get("sort_dir", default_dir).lower()
    column = getattr(model, sort_by, None)
    if column is None:
        column = getattr(model, default_field)
    if sort_dir == "desc":
        column = column.desc()
    return query.order_by(column)
