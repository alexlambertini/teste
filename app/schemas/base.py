from pydantic import BaseModel
from typing import Optional, Dict

class ErrorResponse(BaseModel):
    error: str
    message: Optional[str] = None
    details: Optional[Dict] = None

class CategoriaSchema(BaseModel):
    id: int
    nome: str