from flask import jsonify


def success(data=None, message=None, status_code=200, meta=None):
    body = {}
    if message:
        body["message"] = message
    if data is not None:
        body["data"] = data
    if meta:
        body["meta"] = meta
    return jsonify(body), status_code


def error(message, status_code=400, **extra):
    return jsonify({"error": message, **extra}), status_code
