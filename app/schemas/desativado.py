from pydantic import BaseModel
from typing import Optional, Union
from datetime import date

class DesativadoSchema(BaseModel):
    id: Optional[int] = None
    nome: str
    motivo: str
    categoria: Union[str, int]
    equipamento_retirado: str
    data_desativacao: date 
    ativado_id: Optional[int] = None