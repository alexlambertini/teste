import json
from channels.generic.websocket import AsyncWebsocketConsumer

class AtivadoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("ativados_group", self.channel_name)
        print(f"Cliente conectado: {self.channel_name}")  # Log para debug

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("ativados_group", self.channel_name)
        print(f"Cliente desconectado: {self.channel_name}")  # Log para debug

    async def ativado_update(self, event):
        try:
            await self.send(text_data=json.dumps(event["data"]))
            print("Mensagem enviada:", event["data"])  # Log para debug
        except Exception as e:
            print("Erro ao enviar mensagem:", str(e))