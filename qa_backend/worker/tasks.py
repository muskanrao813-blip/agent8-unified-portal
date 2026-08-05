import logging
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_call_task(self, call_id: str):
    """Process a single call: transcription → metrics → LLM analysis → scoring."""
    try:
        from app.services.pipeline import process_call
        logger.info(f"Processing call {call_id}")
        process_call(call_id)
        logger.info(f"Successfully processed call {call_id}")
    except Exception as exc:
        logger.error(f"Error processing call {call_id}: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 60)
