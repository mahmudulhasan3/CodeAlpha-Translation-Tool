from io import BytesIO

from deep_translator import GoogleTranslator
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from gtts import gTTS
from pydantic import BaseModel, Field

MAX_TEXT_LENGTH = 5000

app = FastAPI(title="Translation Tool")


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    source: str = "auto"
    target: str


class TranslateResponse(BaseModel):
    translated_text: str
    source: str
    target: str


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH)
    lang: str


@app.get("/health")
def health():
    return {"status": "ok", "service": "translation-tool"}


@app.get("/languages")
def languages():
    try:
        supported = GoogleTranslator().get_supported_languages(as_dict=True)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Could not load languages: {e}")
    return {"languages": supported}


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    if req.source != "auto" and req.source == req.target:
        raise HTTPException(
            status_code=400, detail="Source and target languages must be different"
        )

    try:
        result = GoogleTranslator(source=req.source, target=req.target).translate(
            req.text
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Translation failed: {e}")

    if not result:
        raise HTTPException(
            status_code=502, detail="Translation service returned nothing"
        )

    return TranslateResponse(
        translated_text=result, source=req.source, target=req.target
    )


@app.post("/tts")
def text_to_speech(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        audio_buffer = BytesIO()
        gTTS(text=req.text, lang=req.lang).write_to_fp(audio_buffer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {e}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Speech generation failed: {e}")

    return Response(content=audio_buffer.getvalue(), media_type="audio/mpeg")
