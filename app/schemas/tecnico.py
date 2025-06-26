from pydantic import BaseModel, validator
from typing import Optional

class TecnicoSchema(BaseModel):
    id: int
    nome: str
    sobrenome: str

    @validator('nome', 'sobrenome')
    def check_empty(cls, v):
        if not v.strip():
            raise ValueError("Não pode ser vazio")
        return v.strip()