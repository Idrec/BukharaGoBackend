import logging


audit_logger = logging.getLogger("api.audit")


def log_user_action(*, user=None, action: str, result: str, details: dict | None = None) -> None:
    payload = {
        "user_id": getattr(user, "id", None),
        "role": getattr(user, "role", None),
        "action": action,
        "result": result,
    }
    if details:
        payload.update(details)
    audit_logger.info("user_action", extra={"audit": payload})
