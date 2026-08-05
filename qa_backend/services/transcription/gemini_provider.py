"""
Gemini 2.0 Flash audio transcription provider using google-genai v2 SDK.
Sends full audio directly to Gemini — no chunking, no preprocessing needed.
Handles Hindi, English, and Hinglish natively.
"""

import logging
import os
import tempfile
import time
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is required")

# Bajaj Finserv domain context injected into every transcription prompt
BAJAJ_CONTEXT = """This is a recorded phone call from Bajaj Finserv Health (a health insurance/benefits company in India).
Common words in these calls:
- "Bajaj Finserv Health", "benefits plan", "health plan", "coverage"
- "consultation", "appointment", "doctor", "dietician"
- "नमस्ते" (hello), "धन्यवाद" (thank you), "कॉल" (call)
- Customer service, policy, claim, helpline
Speakers: Customer service agent + patient/customer.
"""


class GeminiTranscriptionProvider:
    """
    Transcribes audio using Gemini 2.0 Flash multimodal API.

    Advantages over Groq/Whisper:
    - Sends full audio at once (no chunking artifacts)
    - Native Hindi + English + Hinglish support
    - Can identify speakers (agent vs patient)
    - Can provide timestamps
    - Understands context via system prompt
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY
        self._client = None

    def _get_client(self):
        if self._client is None:
            from google import genai
            from google.genai import types
            import httpx
            # Disable SSL verification — corporate proxy with self-signed cert
            http_client = httpx.Client(verify=False)
            self._client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(httpx_client=http_client),
            )
        return self._client

    def transcribe_file(self, audio_path: str, language: str = "auto") -> Tuple[str, Dict[str, Any]]:
        """
        Transcribe an audio file using Gemini.

        Args:
            audio_path: Path to local audio file (mp3, wav, m4a, etc.)
            language: "hi" for Hindi, "en" for English, "auto" for auto-detect

        Returns:
            Tuple of (transcript_text, metadata_dict)
        """
        from google import genai
        from google.genai import types

        client = self._get_client()

        logger.info(f"[Gemini] Reading audio file: {os.path.basename(audio_path)}")
        file_size = os.path.getsize(audio_path)
        logger.info(f"[Gemini] File size: {file_size} bytes")

        ext = os.path.splitext(audio_path)[1].lower()
        mime_map = {
            '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg', '.flac': 'audio/flac', '.aac': 'audio/aac',
        }
        mime_type = mime_map.get(ext, 'audio/mpeg')

        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()

        logger.info(f"[Gemini] Generating transcription...")

        # Build language-specific instruction
        if language == "hi":
            lang_instruction = "The audio is primarily in Hindi (हिंदी). Transcribe in Hindi/Devanagari script."
        elif language == "en":
            lang_instruction = "The audio is primarily in English. Transcribe in English."
        else:
            lang_instruction = "Detect the language automatically. If Hindi, transcribe in Devanagari. If English, in Latin script. If mixed (Hinglish), use the dominant script with natural code-switching."

        prompt = f"""{BAJAJ_CONTEXT}

TASK: Transcribe this audio call recording accurately.

{lang_instruction}

SPEAKER IDENTIFICATION:
- [Dietician]: The Bajaj Finserv Health agent — initiates call, asks patient's name, discusses consultation, sends guidelines
- [Customer]: The patient/customer — responds to questions, confirms health status

INSTRUCTIONS:
1. Transcribe every spoken word — do not summarize or skip anything
2. Label each line [Dietician]: or [Customer]: based on who is speaking
3. Mark unclear audio as [unclear] rather than guessing
4. Keep domain terms: "Bajaj Finserv Health", "consultation", "appointment", "guidelines"
5. Add natural punctuation based on speech tone

OUTPUT FORMAT — label every utterance individually:
[Dietician]: <what dietician said>
[Customer]: <what customer said>

NOTE: The SAME speaker can speak multiple consecutive lines without interruption.
Do NOT force alternation — label exactly what you hear, who says it.
"""

        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                prompt,
            ]
        )

        transcript = response.text.strip()
        logger.info(f"[Gemini] Transcription complete: {len(transcript)} chars")

        metadata = {
            "model": "gemini-2.0-flash",
            "language_requested": language,
            "file_size_bytes": file_size,
            "transcript_length": len(transcript),
            "has_speaker_labels": "[Agent]:" in transcript or "[Patient]:" in transcript,
        }

        return transcript, metadata

    def transcribe_and_extract(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe AND extract entities in one Gemini call.
        Uses inline base64 encoding — no Files API needed (works on free tier).
        """
        from google import genai
        from google.genai import types
        import json, base64

        client = self._get_client()

        ext = os.path.splitext(audio_path)[1].lower()
        mime_map = {'.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.m4a': 'audio/mp4',
                    '.ogg': 'audio/ogg', '.flac': 'audio/flac', '.aac': 'audio/aac'}
        mime_type = mime_map.get(ext, 'audio/mpeg')

        logger.info(f"[Gemini] Reading audio file for inline encoding...")
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        logger.info(f"[Gemini] Audio size: {len(audio_bytes)} bytes, encoded: {len(audio_b64)} chars")

        prompt = f"""{BAJAJ_CONTEXT}

TASK: Transcribe this audio call and extract key information.

CRITICAL — HOW TO IDENTIFY SPEAKERS:
These are OUTBOUND calls made by a Bajaj Finserv Health Dietician TO a customer/patient.

The DIETICIAN is the one who:
- Initiates and calls outbound — they are the CALLER
- Says "[Patient Name] ji bol rahe hain sir/ma'am?" — THIS IS THE DIETICIAN asking if the patient is there (even though it contains the patient's name)
- Mentions the consultation booking: "aapne TVS Bajaj mein consultation book kara tha"
- Asks about health: "aapko sehat ki koi dikkat hai?", "koi advice chahiye?"
- Offers WhatsApp guidelines: "general guideline bhej rahe hain"
- Repeats or clarifies when patient can't hear

The CUSTOMER/PATIENT is the one who:
- Picks up the phone (RECEIVER of the call)
- Says "Ji", "Haan", "Hello" in response to the dietician
- Says they are busy or can't hear: "main market mein hoon", "sunai nahi de raha", "baad mein call karo"
- Confirms health status: "sab theek hai", "koi problem nahi"

CRITICAL EXAMPLES to get RIGHT (common mistakes Gemini makes):
- "[Name] ji bol rahe hain sir?" → This is [Dietician] asking, NOT the patient saying their name
- "Main market mein hoon, sunai nahi de raha, baad mein baat karte hain" → This is [Customer] (patient is busy)
- "Hum general guideline bhej rahe hain WhatsApp pe" → Always [Dietician]
- "Ji" / "Haan" / "Theek hai" as single-word responses → Usually [Customer] confirming

SPEAKER LABELS TO USE:
- [Dietician]: for the Bajaj Finserv Health dietician/agent
- [Customer]: for the patient/customer

INSTRUCTIONS:
1. Transcribe EVERY spoken word — do not skip or summarize anything
2. Label each utterance as [Dietician]: or [Customer]: based on the speaker rules above
3. The SAME speaker CAN have multiple consecutive lines — do NOT force alternation
4. Mark truly unclear audio as [unclear] — do not guess wildly
5. Preserve Hinglish naturally (mix of Hindi and English as spoken)
6. Add natural punctuation based on speech tone

After transcription, extract:
- customer_name: Name of the customer/patient (the name asked by dietician e.g. "Umesh Ramesh ji?")
- dietician_name: Name of the dietician if mentioned
- organization: Always "Bajaj Finserv Health" if Bajaj is mentioned
- call_purpose: What the call is about (1 sentence)
- health_status: What the customer said about their health
- appointment_details: Any consultation/booking mentioned
- action_items: What will happen next (e.g. WhatsApp guidelines)
- call_language: "Hindi" / "English" / "Hinglish"
- call_outcome: "Resolved" / "Pending" / "Escalated" / "Unclear"

Return ONLY valid JSON (no markdown, no extra text):
{{
    "transcript": "[Dietician]: ...\\n[Customer]: ...",
    "entities": {{
        "customer_name": "...",
        "dietician_name": "...",
        "organization": "...",
        "call_purpose": "...",
        "health_status": "...",
        "appointment_details": "...",
        "action_items": "...",
        "call_language": "...",
        "call_outcome": "..."
    }},
    "audio_quality": "good/fair/poor",
    "confidence": "high/medium/low"
}}"""

        logger.info("[Gemini] Calling generate_content with inline audio...")
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                prompt,
            ]
        )

        raw_response = response.text.strip()

        # Parse JSON response
        cleaned = raw_response
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        # Find valid JSON boundaries
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end > start:
            cleaned = cleaned[start:end+1]

        try:
            data = json.loads(cleaned)
        except Exception as e:
            logger.error(f"[Gemini] JSON parse failed: {e}")
            # Return raw text as transcript if JSON parse fails
            data = {
                "transcript": raw_response,
                "entities": {},
                "audio_quality": "unknown",
                "confidence": "low",
            }

        logger.info(f"[Gemini] Transcription + extraction complete")
        return data
