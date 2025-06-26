from pydantic import BaseModel, validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

class AtivadoSchema(BaseModel):
    nome: str
    sobrenome: str
    tecnicos: List[int]
    taxa: Optional[Decimal] = None
    data_ativacao: str
    empresa: str
    tecnologia: str
    isento: bool = False

    @validator('nome', 'sobrenome')
    def validate_non_empty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Não pode ser vazio")
        return v

    @validator('data_ativacao')
    def validate_date_format(cls, v):
        try:
            # Tenta parsear a data (aceita tanto YYYY-MM-DD quanto ISO completo)
            parsed_date = datetime.fromisoformat(v)
            # Retorna apenas a parte da data (YYYY-MM-DD)
            return parsed_date.date().isoformat()
        except ValueError:
            raise ValueError("Formato de data inválido. Use YYYY-MM-DD")