from venv import logger
from ninja import NinjaAPI, Schema
from typing import Union
from django.shortcuts import get_object_or_404
from app.models import Tecnico, Ativado, Desativado, Categoria
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from ninja.security import django_auth
from django.contrib.auth import authenticate
from ninja.security import HttpBasicAuth
from datetime import date, datetime
from django.http import JsonResponse
import win32print
from decimal import Decimal
from django.db import IntegrityError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.views.decorators.csrf import csrf_exempt 
from django.utils.decorators import method_decorator

from .schemas import (
    TecnicoSchema,
    AtivadoSchema,
    DesativadoSchema,
    DadosImpressaoListaSchema,
    ErrorResponse,
    CategoriaSchema,
)

# Criar a instância da API
api = NinjaAPI(auth=django_auth) 

class BasicAuth(HttpBasicAuth):
    def authenticate(self, request, username, password):
        user = authenticate(username=username, password=password)
        if user:
            return user


# Rotas para Categoria
@api.get("/categorias", response=list[CategoriaSchema])
def listar_categorias(request):
    categorias = Categoria.objects.all().values("id", "nome")  # Retorna um QuerySet de dicionários
    return list(categorias)  # Converte o QuerySet em uma lista de dicionários


# Rotas para Técnico
@api.get("/protected/")
@api.get("/tecnicos", response=List[TecnicoSchema])
def listar_tecnicos(request):
    return list(Tecnico.objects.all().values("id", "nome", "sobrenome"))

@api.post("/tecnicos")
def criar_tecnico(request, data: TecnicoSchema):
    tecnico = Tecnico.objects.create(**data.dict())
    return {"id": tecnico.id, "mensagem": "Técnico criado com sucesso"}


@api.get("/ativados", response=List[AtivadoSchema])
def listar_ativados(request):
    ativados = (
        Ativado.objects
        .all()
        .prefetch_related('tecnicos')
        .order_by('-data_ativacao', '-id')
    )

    response = []
    for ativado in ativados:
        tecnicos = [tecnico.id for tecnico in ativado.tecnicos.all()]
        taxa = "Isento" if ativado.isento else ativado.formatted_taxa()

        response.append(AtivadoSchema(
            id=ativado.id,
            nome=ativado.nome,
            sobrenome=ativado.sobrenome,
            tecnicos=tecnicos,
            taxa=None if ativado.isento else ativado.taxa,
            data_ativacao=ativado.data_ativacao.date().isoformat(),
            empresa=ativado.empresa,
            tecnologia=ativado.tecnologia,
            isento=ativado.isento
        ))
    
    return response



@api.post("/ativados", response={200: AtivadoSchema, 400: ErrorResponse})
def criar_ativado(request, payload: AtivadoSchema):
    print("Dados recebidos:", payload.dict()) 
    try:
        # Verificação de duplicados no banco
        exists = Ativado.objects.filter(
            nome__iexact=payload.nome.strip().lower(),
            sobrenome__iexact=payload.sobrenome.strip().lower(),
            ativo=True
        ).exists()

        if exists:
            return 400, {
                "error": "nome_duplicado",
                "message": "Já existe uma ativação com este nome",
                "suggestion": "Adicione um sufixo ou inicial diferente"
            }

        # Criação do objeto
        ativado = Ativado(
            nome=payload.nome.strip(),
            sobrenome=payload.sobrenome.strip(),
            empresa=payload.empresa.lower(),
            tecnologia=payload.tecnologia.lower(),
            taxa=float(payload.taxa) if (payload.taxa and not payload.isento) else None,
            isento=payload.isento,
            data_ativacao=datetime.strptime(payload.data_ativacao, "%Y-%m-%d").date()
        )
        ativado.save()

        # Associação de técnicos
        if payload.tecnicos:
            tecnicos = Tecnico.objects.filter(id__in=payload.tecnicos)
            ativado.tecnicos.set(tecnicos)

        # Serialização da resposta
        return 200, {
            "id": ativado.id,
            "nome": ativado.nome,
            "sobrenome": ativado.sobrenome,
            "tecnicos": [t.id for t in ativado.tecnicos.all()],
            "data_ativacao": ativado.data_ativacao.isoformat(),
            "empresa": ativado.empresa,
            "tecnologia": ativado.tecnologia,
            "isento": ativado.isento,
            "taxa": float(ativado.taxa) if ativado.taxa else None
        }

    except ValueError as e:
        # Captura erro de validação e retorna resposta
        return 400, {
            "error": "validation_error", 
            "message": str(e)
        }
    
    except IntegrityError as e:
        # Tratar erro de banco de dados, como violação de unicidade
        return 400, {
            "error": "database_error",
            "message": "Erro de banco de dados",
            "details": str(e)
        }
    
    except Exception as e:
        # Erro genérico
        return 400, {
            "error": "server_error",
            "message": "Erro interno no servidor",
            "details": str(e)
        }


@api.put("/ativados/{id}", response={200: AtivadoSchema, 400: ErrorResponse, 404: ErrorResponse})
def editar_ativado(request, id: int, payload: AtivadoSchema):
    try:
        # 1. Busca o ativado com tratamento de erro específico
        try:
            ativado = Ativado.objects.get(id=id)
        except Ativado.DoesNotExist:
            return 404, {
                "error": "not_found",
                "message": "Cliente não encontrado",
                "code": "ativado_404"
            }

        # 2. Validação de dados
        if Ativado.objects.filter(nome__iexact=payload.nome, sobrenome__iexact=payload.sobrenome).exclude(id=id).exists():
            return 400, {
                "error": "duplicate_entry",
                "message": "Já existe outro cliente com este nome e sobrenome",
                "code": "unique_violation"
            }

        # 3. Atualização dos campos básicos
        ativado.nome = payload.nome.strip()
        ativado.sobrenome = payload.sobrenome.strip()
        ativado.empresa = payload.empresa.lower()
        ativado.tecnologia = payload.tecnologia.lower()
        ativado.taxa = None if payload.isento else payload.taxa
        ativado.isento = payload.isento
        
        try:
            ativado.data_ativacao = datetime.strptime(payload.data_ativacao, "%Y-%m-%d").date()
        except ValueError:
            return 400, {
                "error": "invalid_date",
                "message": "Formato de data inválido. Use YYYY-MM-DD",
                "code": "date_format_error"
            }

        # 4. Atualização de técnicos (mais eficiente)
        try:
            tecnico_ids = list(set(payload.tecnicos))  # Remove duplicados
            tecnicos = Tecnico.objects.filter(id__in=tecnico_ids)
            
            # Verifica se todos os técnicos existem
            if len(tecnicos) != len(tecnico_ids):
                missing_ids = set(tecnico_ids) - {t.id for t in tecnicos}
                return 400, {
                    "error": "invalid_technicians",
                    "message": f"Técnicos não encontrados: {missing_ids}",
                    "code": "technicians_not_found"
                }
                
            ativado.tecnicos.set(tecnicos)
        except Exception as e:
            return 400, {
                "error": "technicians_update_failed",
                "message": str(e),
                "code": "technicians_error"
            }

        # 5. Persiste as alterações
        ativado.save()

        # 6. Notifica os clientes via WebSocket
        try:
            broadcast_refresh()
        except Exception as ws_error:
            logger.error(f"Erro WebSocket: {ws_error}", exc_info=True)

        # 7. Retorna a resposta padronizada
        return 200, {
            "id": ativado.id,
            "nome": ativado.nome,
            "sobrenome": ativado.sobrenome,
            "tecnicos": [t.id for t in ativado.tecnicos.all()],
            "taxa": "Isento" if ativado.isento else ativado.taxa,
            "data_ativacao": ativado.data_ativacao.isoformat(),
            "empresa": ativado.empresa,
            "tecnologia": ativado.tecnologia,
            "isento": ativado.isento,
            "message": "Cliente atualizado com sucesso"
        }

    except Exception as e:
        logger.error(f"Erro inesperado ao editar ativado: {e}", exc_info=True)
        return 500, {
            "error": "server_error",
            "message": "Erro interno no servidor",
            "code": "internal_error"
        }




# Rotas para Desativado
@api.get("/desativados", response=List[DesativadoSchema])
def listar_desativados(request):
    desativados_data = (
        Desativado.objects
        .all()
        .select_related('categoria')
        .order_by('-data_desativacao', '-id')  # <- Ordenação adicionada aqui
        .values(
            'nome',
            'motivo',
            'categoria__nome',
            'equipamento_retirado',
            'data_desativacao',
            'id'
        )
    )
    
    desativados = [
        {
            **data,
            'categoria': data['categoria__nome'],
            'equipamento_retirado': dict(Desativado.SIM_NAO_CHOICES).get(
                data['equipamento_retirado'], data['equipamento_retirado']
            ),
            'data_desativacao': data['data_desativacao'].date().isoformat()
        }
        for data in desativados_data
    ]
    
    return [DesativadoSchema(**data) for data in desativados]


@api.post("/desativados")
def criar_desativado(request, data: DesativadoSchema):
    try:
        # Verifica se já existe um desativado com o mesmo nome
        if Desativado.objects.filter(nome=data.nome).exists():
            return JsonResponse(
                {"detail": "Já existe um registro com esse nome."},
                status=400
            )

        # Obtém a categoria
        if isinstance(data.categoria, int):
            categoria = Categoria.objects.get(id=data.categoria)
        else:
            categoria = Categoria.objects.get(nome=data.categoria)

        # Cria o desativado - agora usando data.ativado_id diretamente
        desativado = Desativado.objects.create(
            nome=data.nome,
            motivo=data.motivo,
            categoria=categoria,
            equipamento_retirado=data.equipamento_retirado,
            data_desativacao=data.data_desativacao,
            ativado_id=data.ativado_id  # Modificado aqui
        )

        # Remove o ativado se existir
        if data.ativado_id:
            Ativado.objects.filter(id=data.ativado_id).delete()
    
        return {
            "id": desativado.id,
            "mensagem": "Desativação realizada com sucesso",
            "ativado_removido_id": data.ativado_id
        }
    
        
    except Categoria.DoesNotExist:
        return JsonResponse(
            {"detail": "Categoria não encontrada."},
            status=404
        )
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=400)



def broadcast_refresh():
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ativados_group",
            {
                "type": "ativado.update",
                "data": {
                    "action": "refresh",
                    "message": "Dados atualizados",
                    "timestamp": str(datetime.now())
                }
            }
        )
    except Exception as e:
        print("Erro ao notificar clientes:", str(e))



@method_decorator(csrf_exempt, name="dispatch")
@api.post("/imprimir-recibo/")
def imprimir_recibo(request, dados: DadosImpressaoListaSchema):
    try:
        # Nome da impressora (obtenha o nome correto no Painel de Controle)
        printer_name = win32print.GetDefaultPrinter()
        hprinter = win32print.OpenPrinter(printer_name)
        
        # Inicia o trabalho de impressão
        job = win32print.StartDocPrinter(hprinter, 1, ("Recibo de Instalação", None, "RAW"))
        win32print.StartPagePrinter(hprinter)
        
        # Comandos ESC/POS para aumentar o tamanho do texto
        comando_tamanho_duplo = b"\x1D\x21\x10"  # Tamanho duplo de altura e largura
        comando_tamanho_normal = b"\x1D\x21\x00"  # Volta ao tamanho normal

        # Comando para centralizar o texto
        comando_centralizar = b"\x1B\x61\x01"  # ESC a 1 (centralizar)

        # Comando para alinhar à esquerda (padrão)
        comando_esquerda = b"\x1B\x61\x00"  # ESC a 0 (alinhar à esquerda)

        # Texto a ser impresso (linha de corte)
        text = "\n\n*************** CORTAR AQUI ***************\n\n"

        # Função para imprimir uma via
        def imprimir_via(is_second_via=False):
            if is_second_via:
                # Ajuste para a segunda via, move o cursor para o meio da página
                win32print.WritePrinter(hprinter, b"\x0C")  # Form feed (pular para nova página)
            
            # Centraliza o cabeçalho
            win32print.WritePrinter(hprinter, comando_centralizar)
            win32print.WritePrinter(hprinter, comando_tamanho_duplo)  # Aumenta o tamanho do texto
            win32print.WritePrinter(hprinter, "HONEST TELECOMUNICAÇÕES\n".encode("cp860", errors="replace"))
            win32print.WritePrinter(hprinter, comando_tamanho_normal)  # Volta ao tamanho normal

            # Adiciona mais espaçamento entre as linhas
            win32print.WritePrinter(hprinter, b"\n")  # Quebras de linha para espaçamento extra

            # Descrição em tamanho menor (centralizada)
            win32print.WritePrinter(hprinter, "A internet que você pode confiar\n".encode("cp860", errors="replace"))
            
            # Adiciona mais espaçamento entre as linhas
            win32print.WritePrinter(hprinter, b"\n")  # Quebras de linha para espaçamento extra
            win32print.WritePrinter(hprinter, b"-" * 40 + b"\n")  # Linha separadora

            # Volta ao alinhamento à esquerda para os dados da empresa
            win32print.WritePrinter(hprinter, comando_esquerda)

            # Dados da empresa
            win32print.WritePrinter(hprinter, comando_centralizar)
            win32print.WritePrinter(hprinter, b"\n") 
            win32print.WritePrinter(hprinter, f"CNPJ: 07.428.380/0001-09\n".encode("cp860", errors="replace"))
            win32print.WritePrinter(hprinter, f"E-mail: comercial@honesttelecomunicações\n".encode("cp860", errors="replace"))
            win32print.WritePrinter(hprinter, f"Rua: Sorocabana 6-70 / Bauru- SP\n".encode("cp860", errors="replace"))
            win32print.WritePrinter(hprinter, f"CEP: 17014-260\n".encode("cp860", errors="replace"))
            win32print.WritePrinter(hprinter, f"FONE/WHATS: (14) 3016-1900\n".encode("cp860", errors="replace"))
            win32print.WritePrinter(hprinter, f"www.honesttelecom.com.br\n".encode("cp860", errors="replace"))
            
            # Adiciona mais espaçamento entre as linhas
            win32print.WritePrinter(hprinter, comando_centralizar)
            win32print.WritePrinter(hprinter, b"\n")  # Quebras de linha para espaçamento extra
            win32print.WritePrinter(hprinter, b"-" * 40 + b"\n")  # Linha separadora

            # Centraliza as instruções sobre a fatura
            win32print.WritePrinter(hprinter, comando_centralizar)
            win32print.WritePrinter(hprinter, b"\n") 
            win32print.WritePrinter(hprinter, "Para acessar a sua fatura, acesse nosso site\n".encode("cp860", errors="replace"))
            win32print.WritePrinter(hprinter, "e clique em 'CENTRAL DO ASSINANTE'\n".encode("cp860", errors="replace"))
            
            # Adiciona mais espaçamento entre as linhas
            win32print.WritePrinter(hprinter, b"\n")  # Quebras de linha para espaçamento extra
            win32print.WritePrinter(hprinter, b"-" * 40 + b"\n")  # Linha separadora

            # Volta ao alinhamento à esquerda para os dados do cliente
            win32print.WritePrinter(hprinter, comando_esquerda)

            # Dados do cliente (em tamanho normal)
            win32print.WritePrinter(hprinter, comando_centralizar)
            win32print.WritePrinter(hprinter, b"\n") 
            win32print.WritePrinter(hprinter, b"Dados do Cliente\n")
            win32print.WritePrinter(hprinter, b"\n")
            win32print.WritePrinter(hprinter, b"-" * 40 + b"\n")

            # Imprime dados do cliente
            for cliente in dados.dados:
                win32print.WritePrinter(hprinter, comando_centralizar)
                win32print.WritePrinter(hprinter, b"\n")
                win32print.WritePrinter(hprinter, f"Cliente: {cliente.nome} {cliente.sobrenome}\n".encode("cp860", errors="replace"))
                win32print.WritePrinter(hprinter, f"Técnico: {cliente.tecnicos[0].nome} {cliente.tecnicos[0].sobrenome}\n".encode("cp860", errors="replace"))
                win32print.WritePrinter(hprinter, f"Data: {cliente.data_ativacao}\n".encode("cp860", errors="replace"))
                win32print.WritePrinter(hprinter, f"Valor: {cliente.taxa}\n".encode("cp860", errors="replace"))
                 # Forma de pagamento
                win32print.WritePrinter(hprinter, b"\n")
                win32print.WritePrinter(hprinter, "(   ) Dinheiro     (   ) Cartão     (   ) Pix\n".encode("cp860", errors="replace"))
                win32print.WritePrinter(hprinter, b"\n")
                win32print.WritePrinter(hprinter, b"-" * 40 + b"\n")  # Linha separadora

                # Mais espaço para assinatura
                win32print.WritePrinter(hprinter, comando_centralizar)
                win32print.WritePrinter(hprinter, b"\n\n")  # Adiciona mais linhas para o espaço
                win32print.WritePrinter(hprinter, b"Assinatura do Cliente:\n")
                win32print.WritePrinter(hprinter, b"\n\n________________________\n")  # Linha de assinatura
                win32print.WritePrinter(hprinter, b"\n\n")  # Espaço para nova linha

                # Linha para corte entre vias
                win32print.WritePrinter(hprinter, comando_centralizar)
                win32print.WritePrinter(hprinter, text.encode("latin1", errors="replace"))
                win32print.WritePrinter(hprinter, b"\n\n\n\n")  # Adiciona espaço extra entre as vias

        # Imprime a primeira via
        imprimir_via(is_second_via=False)
        
        # Imprime a segunda via
        imprimir_via(is_second_via=True)

        # Cortar o papel entre as vias
        win32print.WritePrinter(hprinter, b"\x1B\x69")  # Comando de corte de papel

        # Finaliza o trabalho de impressão
        win32print.EndPagePrinter(hprinter)
        win32print.EndDocPrinter(hprinter)
        win32print.ClosePrinter(hprinter)

        return JsonResponse({"status": "Recibo(s) impresso(s) com sucesso!"})
    
    except Exception as e:
        return JsonResponse({
            "detail": [{
                "loc": ["body"],
                "msg": str(e),
                "type": "value_error"
            }]
    }, status=422)


    