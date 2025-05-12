from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from celery import shared_task
from celery.utils.log import get_task_logger
from django.db import transaction
from django.utils import timezone
from .models import AnalysisRequest
from .ml_utils import predict_success
from .chat_utils import generate_recommendations
from projects.models import Project

try:
    import sentry_sdk  # type: ignore
except ImportError:  # pragma: no cover
    sentry_sdk = None  # noqa: N816

try:
    from prometheus_client import Counter  # type: ignore

    ANALYSIS_TOTAL = Counter("analysis_total", "Total analysis runs", ["status"])
except ImportError:  # pragma: no cover
    # graceful fallback
    def _noop(*args: Any, **kwargs: Any) -> Any:  # noqa: D401
        return _noop

    ANALYSIS_TOTAL = _noop  # type: ignore

logger = get_task_logger(__name__)


# ───────────────────────────────────────────────────────────────────────────────
# Helpers
# ───────────────────────────────────────────────────────────────────────────────

def safe_float(val: Any, *, default: float = 0.0) -> float:
    """Convert arbitrary input to *float*.

    * **str**  – handles comma/point separator.
    * **dict** – returns first numeric value.
    * **None / invalid** – returns *default*.
    """
    if isinstance(val, (int, float)):
        return float(val)

    if isinstance(val, str):
        try:
            return float(val.replace(",", "."))
        except ValueError:
            return default

    if isinstance(val, dict):
        for v in val.values():
            try:
                return float(v)
            except (TypeError, ValueError):
                continue
        return default

    return default


@dataclass(slots=True)
class AnalysisParams:
    budget: float = 0.0
    competition: float = 0.0
    marketing_skill: float = 0.0
    team_experience: float = 0.0
    location_factor: float = 0.0
    extra_info: str = ""

    @classmethod
    def from_raw(cls, raw: Dict[str, Any]) -> "AnalysisParams":
        return cls(
            budget=safe_float(raw.get("budget")),
            competition=safe_float(raw.get("competition")),
            marketing_skill=safe_float(raw.get("marketing_skill")),
            team_experience=safe_float(raw.get("team_experience")),
            location_factor=safe_float(raw.get("location_factor")),
            extra_info=str(raw.get("extra_info", ""))[:2_000],  # limit 2k chars
        )


# ───────────────────────────────────────────────────────────────────────────────
# Celery task
# ───────────────────────────────────────────────────────────────────────────────

@shared_task(
    bind=True,
    acks_late=True,
    max_retries=3,
    default_retry_delay=60,
    soft_time_limit=60,  # seconds
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    expires=3600,  # 1 hour
)
def run_analysis_task(self, analysis_request_id: int) -> None:  # noqa: D401
    """Main analysis pipeline – ML prediction + ChatGPT recommendations."""
    try:
        analysis_req: AnalysisRequest = AnalysisRequest.objects.select_for_update().get(
            id=analysis_request_id
        )
    except AnalysisRequest.DoesNotExist as exc:
        logger.error("AnalysisRequest not found", extra={"id": analysis_request_id})
        ANALYSIS_TOTAL("not_found")
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        return

    params_raw: Dict[str, Any] = analysis_req.params or {}
    params: AnalysisParams = AnalysisParams.from_raw(params_raw)
    project: Project = analysis_req.project

    # ── Coordinates ───────────────────────────────────────────────────────────
    latitude: float = safe_float(getattr(project, "latitude", None))
    longitude: float = safe_float(getattr(project, "longitude", None))

    try:
        with transaction.atomic():
            analysis_req.status = "processing"
            analysis_req.save(update_fields=["status"])

            # ML model
            success_raw: Any = predict_success(
                params.budget,
                params.competition,
                params.marketing_skill,
                params.team_experience,
                latitude,
                longitude,
                params.location_factor,
            )
            success_prob: float = (
                safe_float(success_raw.get("probability"))
                if isinstance(success_raw, dict)
                else safe_float(success_raw)
            )

            # ChatGPT
            recommendations: str = generate_recommendations(success_prob, extra_info=params.extra_info)

            result: Dict[str, Any] = {
                "success_prob": round(success_prob * 100, 2),  # store as percentage 0‑100
                "recommendations": recommendations,
                "timestamp": timezone.now().isoformat(),
            }

            # save
            analysis_req.result = result
            analysis_req.status = "done"
            analysis_req.save(update_fields=["result", "status"])

            logger.info(
                "analysis done",
                extra={
                    "analysis_id": analysis_request_id,
                    "prob": success_prob,
                    "budget": params.budget,
                },
            )
            ANALYSIS_TOTAL("success")

    except Exception as exc:  # noqa: BLE001
        logger.exception("analysis failed", extra={"analysis_id": analysis_request_id})
        ANALYSIS_TOTAL("failure")

        try:
            analysis_req.status = "error"
            analysis_req.result = {"error": str(exc)}
            analysis_req.save(update_fields=["result", "status"])
        except Exception as inner_exc:  # noqa: BLE001
            logger.error("cannot mark analysis as error", extra={"e": str(inner_exc)})

        if sentry_sdk:
            sentry_sdk.capture_exception(exc)

        raise  # let Celery handle retry
