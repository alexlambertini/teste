from django.db import models



class Tecnico(models.Model):
    nome = models.CharField(max_length=255)
    sobrenome = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return f"{self.nome}, {self.sobrenome}"

    class Meta:
        unique_together = ('nome', 'sobrenome')



class Categoria(models.Model):
    nome = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.nome        
    

class Ativado(models.Model):
    nome = models.CharField(max_length=255)
    sobrenome = models.CharField(max_length=255)
    data_ativacao = models.DateTimeField(auto_now_add=True)
    tecnicos = models.ManyToManyField(Tecnico)
    taxa = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=100.00)

    EMPRESA_CHOICES = [
        ('honest', 'Honest'),
        ('solunet', 'Solunet'),
    ]
    
    empresa = models.CharField(
        max_length=252, 
        choices=EMPRESA_CHOICES,
        default='honest',
    )

    TECNOLOGIA_CHOICES = [
        ('radio', 'Rádio'),
        ('fibra', 'Fibra'),
    ]

    tecnologia = models.CharField(
        max_length=100,
        choices=TECNOLOGIA_CHOICES,
        default='radio',
    )

    isento = models.BooleanField(default=False)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nome} {self.sobrenome}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['nome', 'sobrenome'],
                name='unique_nome_sobrenome',
                condition=models.Q(ativo=True),
                violation_error_message="Já existe um cliente ativo com esta combinação de nome e sobrenome"
            )
        ]

    def formatted_taxa(self):
        if self.taxa is None:
            return "Isento"
        return f"R$ {self.taxa:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    
    

class Desativado(models.Model):
    ativado = models.OneToOneField(
        Ativado, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="desativacao"
    )
    
    nome = models.CharField(max_length=255, blank=True)
    motivo = models.TextField(default="", blank=False)
    data_desativacao = models.DateTimeField(auto_now_add=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    SIM_NAO_CHOICES = [('sim', 'Sim'), ('nao', 'Não')]

    equipamento_retirado = models.CharField(
        max_length=3, 
        choices=SIM_NAO_CHOICES, 
        default='sim' 
    )

    def save(self, *args, **kwargs):
        # Se houver um ativado associado, exclui o registro do modelo Ativado
        if self.ativado:
            self.ativado.delete()  # Exclui o registro do modelo Ativado
            self.ativado = None  # Define o campo ativado como None

        super().save(*args, **kwargs)