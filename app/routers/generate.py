from fastapi import APIRouter, Depends, HTTPException, status

from app.deps import get_current_user
from app.models.user import User
from app.schemas import GenerateRequest, GenerateResponse
from app.services.deepseek import generate_post


router = APIRouter(prefix="/generate", tags=["generate"])


@router.post("", response_model=GenerateResponse)
async def generate(req: GenerateRequest, _user: User = Depends(get_current_user)):
    try:
        text = await generate_post(req.topic, req.description)
    except Exception as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Generation failed: {e}")
    return GenerateResponse(generated_text=text)
