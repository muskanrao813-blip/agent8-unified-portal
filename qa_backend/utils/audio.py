"""Audio download and processing utilities."""

import os
import logging
import requests
import tempfile

logger = logging.getLogger(__name__)


def download_audio(recording_url: str, max_retries: int = 3, timeout: int = 30) -> str:
    """Download audio from URL or copy a locally uploaded file path. Returns local path."""
    try:
        if recording_url.startswith(("http://", "https://")):
            for attempt in range(max_retries):
                try:
                    logger.info(f"Downloading audio from {recording_url} (attempt {attempt + 1})")

                    response = requests.get(recording_url, timeout=timeout, stream=True, verify=False)
                    response.raise_for_status()

                    content_type = response.headers.get("content-type", "audio/wav")
                    ext = _get_extension_from_content_type(content_type)

                    temp_dir = tempfile.gettempdir()
                    import uuid
                    temp_filename = f"audio_{uuid.uuid4()}{ext}"
                    temp_path = os.path.join(temp_dir, temp_filename)

                    with open(temp_path, "wb") as tmp_file:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                tmp_file.write(chunk)

                    logger.info(f"Downloaded audio to {temp_path} ({os.path.getsize(temp_path)} bytes)")

                    if not os.path.exists(temp_path):
                        raise FileNotFoundError(f"Temp file not created: {temp_path}")

                    return temp_path

                except requests.RequestException as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        continue
                    raise

            raise RuntimeError(f"Failed to download audio after {max_retries} attempts")

        if os.path.exists(recording_url):
            resolved_path = os.path.abspath(recording_url)
            if os.path.isfile(resolved_path):
                logger.info(f"Local file found: {resolved_path}, copying to temp...")
                # Copy the file to temp directory to avoid Windows file lock issues
                import shutil
                import uuid
                temp_dir = tempfile.gettempdir()
                _, ext = os.path.splitext(resolved_path)
                temp_filename = f"audio_{uuid.uuid4()}{ext}"
                temp_path = os.path.join(temp_dir, temp_filename)

                shutil.copy2(resolved_path, temp_path)
                logger.info(f"Copied local file to: {temp_path} ({os.path.getsize(temp_path)} bytes)")

                if not os.path.exists(temp_path):
                    raise FileNotFoundError(f"Temp copy not created: {temp_path}")

                return temp_path
            raise ValueError(f"Path is not a file: {recording_url}")

        raise ValueError(f"Invalid audio source: {recording_url}")

    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        raise


def _get_extension_from_content_type(content_type: str) -> str:
    """Map content type to file extension."""
    mapping = {
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
        "audio/ogg": ".ogg",
        "audio/webm": ".webm",
        "video/mp4": ".mp4",
        "video/webm": ".webm",
    }
    return mapping.get(content_type, ".wav")


def cleanup_audio(file_path: str) -> None:
    """Delete temporary audio file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up temp audio file: {file_path}")
    except Exception as e:
        logger.warning(f"Error cleaning up audio file {file_path}: {e}")
