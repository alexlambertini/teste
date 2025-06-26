from pydantic import BaseModel
from typing import List
from .tecnico import TecnicoSchema

class DadosImpressaoSchema(BaseModel):
    nome: str
    sobrenome: str
    tecnicos: List[TecnicoSchema]  
    taxa: str
    data_ativacao: str
    empresa: str
    tecnologia: str
    isento: bool

class DadosImpressaoListaSchema(BaseModel):
    dados: List[DadosImpressaoSchema]