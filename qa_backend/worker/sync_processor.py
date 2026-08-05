"""Synchronous call processor (no Celery/Redis needed)."""

import logging
import time
from app.db.session import SessionLocal
from app.db import models
from app.services.pipeline import process_call

logger = logging.getLogger(__name__)


def process_pending_calls(batch_size: int = 5, polling_interval: int = 5):
    """Continuously process pending calls."""
    db = SessionLocal()

    try:
        while True:
            # Get pending calls
            pending_calls = db.query(models.Call).filter(
                models.Call.status == models.CallStatus.pending
            ).limit(batch_size).all()

            if not pending_calls:
                logger.debug(f"No pending calls. Waiting {polling_interval}s...")
                time.sleep(polling_interval)
                continue

            logger.info(f"Processing {len(pending_calls)} calls")

            for call in pending_calls:
                try:
                    logger.info(f"[{call.patient_name}] Processing call {call.id}...")
                    call.status = models.CallStatus.processing
                    db.commit()

                    # Run the pipeline
                    process_call(str(call.id))

                    logger.info(f"[{call.patient_name}] ✓ Complete")

                except Exception as e:
                    logger.error(f"[{call.patient_name}] ✗ Error: {e}")
                    call.status = models.CallStatus.failed
                    call.error_message = str(e)[:500]
                    db.commit()

            # Small delay before next batch
            time.sleep(2)

    except KeyboardInterrupt:
        logger.info("Worker stopped")
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    process_pending_calls()
