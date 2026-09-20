from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from .models import BauEstacaoUsuario, Exercicio, ExercicioUsuario, Modulo, Secao, Estacao, ReporteExercicio, TentativaEstacao
from import_export.admin import ImportExportModelAdmin


class ExercicioAdminForm(forms.ModelForm):
    """Apresenta respostas alternativas como texto simples no Django Admin."""

    respostas_aceitas = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "cols": 60,
                "placeholder": "Uma alternativa por linha. Ex:\n++contador\ncontador += 1",
            }
        ),
        help_text="Opcional. Informe uma resposta aceita por linha; espaços e ; final são ignorados.",
    )

    class Meta:
        model = Exercicio
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            respostas = [
                self.instance.resposta_texto_codigo,
                *(self.instance.respostas_aceitas or []),
            ]
            self.initial["respostas_aceitas"] = "\n".join(
                resposta for resposta in respostas if resposta
            )

    def clean_respostas_aceitas(self):
        respostas = self.cleaned_data["respostas_aceitas"].splitlines()
        respostas = list(
            dict.fromkeys(resposta.strip() for resposta in respostas if resposta.strip())
        )
        if self.cleaned_data.get("tipo") == "lacuna" and not respostas:
            raise ValidationError("Informe pelo menos uma resposta aceita.")
        return respostas


@admin.register(ReporteExercicio)
class ReporteExercicioAdmin(admin.ModelAdmin):
    list_display = ("id", "exercicio", "motivo", "usuario", "criado_em", "status")
    list_filter = ("status", "motivo", "exercicio__modulo")
    search_fields = ("exercicio__titulo", "exercicio__enunciado", "usuario__username")
    list_select_related = ("exercicio", "usuario")
    readonly_fields = ("exercicio", "usuario", "motivo", "criado_em")
    list_editable = ("status",)


@admin.register(TentativaEstacao)
class TentativaEstacaoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "estacao", "iniciada_em", "concluida_em", "duracao_segundos", "primeira_conclusao")
    list_filter = ("primeira_conclusao", "estacao__secao__modulo")
    search_fields = ("usuario__username", "estacao__nome")
    readonly_fields = ("usuario", "estacao", "iniciada_em", "concluida_em", "duracao_segundos", "primeira_conclusao", "acertos", "erros", "percentual_acertos", "xp_ganho")


@admin.register(BauEstacaoUsuario)
class BauEstacaoUsuarioAdmin(admin.ModelAdmin):
    list_display = ("usuario", "secao", "cristais_recebidos", "xp_recebido", "coletado_em")
    list_filter = ("secao__modulo", "secao")
    search_fields = ("usuario__username", "secao__nome")
    readonly_fields = ("usuario", "secao", "cristais_recebidos", "xp_recebido", "coletado_em")


@admin.register(Exercicio)
class ExercicioAdmin(ImportExportModelAdmin):
    form = ExercicioAdminForm
    list_display = ("titulo", "estacao", "modulo", "tipo")
    list_filter = ("estacao__secao__modulo", "estacao__secao", "estacao", "tipo")
    search_fields = ("titulo", "enunciado")

    # Organiza os campos em grupos (fieldsets).
    # As 'classes' CSS são a chave para o formulário dinâmico.
    fieldsets = (
        (
            "Informações Gerais",
            {
                "fields": (
                    "titulo",
                    "enunciado",
                    "estacao",
                    "modulo",
                    "xp",
                    "explicacao",
                    "tipo",
                )
            },
        ),
        (
            "Campos para Múltipla Escolha",
            {
                "classes": (
                    "exercicio-tipo",
                    "exercicio-mcq",
                ),  # Mostra para o tipo 'mcq'
                "fields": (
                    "alternativa_1",
                    "alternativa_2",
                    "alternativa_3",
                    "alternativa_4",
                    "resposta_correta",
                ),
            },
        ),
        (
            "Campos para Lacuna",
            {
                "classes": (
                    "exercicio-tipo",
                    "exercicio-lacuna",
                ),  # Mostra para o tipo 'lacuna'
                "fields": ("codigo", "respostas_aceitas"),
            },
        ),
        (
            "Campos para Informativo",
            {
                "classes": (
                    "exercicio-tipo",
                    "exercicio-info",
                ),  # Mostra para o tipo 'info'
                "fields": ("imagem",),
            },
        ),
        (
            "Campos para Verdadeiro ou Falso",
            {
                "classes": (
                    "exercicio-tipo",
                    "exercicio-vf",
                ),  # Mostra para o tipo 'vf'
                "fields": ("resposta_vf_correta",),
            },
        ),
    )

    def get_changeform_initial_data(self, request):
        """
        Pré-preenche dados no formulário de adição de Exercicio.
        """
        initial = super().get_changeform_initial_data(request)
        estacao_id = request.GET.get("estacao")
        if estacao_id:
            try:
                # Otimiza a query usando select_related para buscar os modelos relacionados de uma só vez.
                estacao_obj = Estacao.objects.select_related("secao__modulo").get(
                    pk=estacao_id
                )
                initial["estacao"] = estacao_obj
                initial["modulo"] = estacao_obj.secao.modulo
            except Estacao.DoesNotExist:
                pass
        return initial

    # Carrega nosso JavaScript customizado na página de adição/edição de Exercicio
    class Media:
        js = ("admin/js/exercicio_form.js",)


@admin.register(Secao)
class SecaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "modulo", "ordem")
    list_filter = ("modulo",)
    search_fields = ("nome",)
    list_editable = ("ordem",)
    fields = ["nome", "modulo", "ordem", "link_adicionar_estacao_form"]
    readonly_fields = ["link_adicionar_estacao_form"]

    def link_adicionar_estacao_form(self, obj):
        if obj.pk:
            add_estacao_url = reverse("admin:exercicios_estacao_add")
            url = f"{add_estacao_url}?secao={obj.pk}"
            return format_html(
                '<a href="{}" class="button">Adicionar Nova Estação a esta Seção</a>',
                url,
            )
        return "Salve a seção primeiro para poder adicionar estações."

    link_adicionar_estacao_form.short_description = "Ações de Estação"

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if modulo_id := request.GET.get("modulo"):
            try:
                initial["modulo"] = Modulo.objects.get(pk=modulo_id)
            except Modulo.DoesNotExist:
                pass
        return initial


@admin.register(Estacao)
class EstacaoAdmin(admin.ModelAdmin):
    list_display = ("nome", "secao", "disponivel_para_visitantes")
    list_filter = ("secao__modulo", "secao", "disponivel_para_visitantes")
    search_fields = ("nome",)
    list_editable = ("secao",)
    fields = [
        "nome",
        "secao",
        "disponivel_para_visitantes",
        "exercicios_da_estacao",
        "link_adicionar_exercicio_form",
    ]
    readonly_fields = ["exercicios_da_estacao", "link_adicionar_exercicio_form"]

    def exercicios_da_estacao(self, obj):
        """Exibe os exercícios vinculados à estação com acesso à edição."""
        if not obj.pk:
            return "Salve a estação primeiro para visualizar seus exercícios."

        exercicios = obj.exercicios.all()
        if not exercicios:
            return "Esta estação ainda não possui exercícios."

        return format_html_join(
            "",
            '<div style="margin: 0 0 8px"><a href="{}">{}</a> <span style="color: var(--body-quiet-color)">— {}</span></div>',
            (
                (
                    reverse("admin:exercicios_exercicio_change", args=(exercicio.pk,)),
                    exercicio.titulo or f"Exercício #{exercicio.pk}",
                    exercicio.get_tipo_display(),
                )
                for exercicio in exercicios
            ),
        )

    exercicios_da_estacao.short_description = "Exercícios desta Estação"

    def link_adicionar_exercicio_form(self, obj):
        if obj.pk:
            add_exercicio_url = reverse("admin:exercicios_exercicio_add")
            url = f"{add_exercicio_url}?estacao={obj.pk}"
            return format_html(
                '<a href="{}" class="button">Adicionar Novo Exercício a esta Estação</a>',
                url,
            )
        return "Salve a estação primeiro para poder adicionar exercícios."

    link_adicionar_exercicio_form.short_description = "Ações de Exercício"

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        if secao_id := request.GET.get("secao"):
            try:
                initial["secao"] = Secao.objects.get(pk=secao_id)
            except Secao.DoesNotExist:
                pass
        return initial


@admin.register(ExercicioUsuario)
class ExercicioUsuarioAdmin(admin.ModelAdmin):
    """Gerencia o progresso individual, sem alterar o conteúdo compartilhado."""

    list_display = ("usuario", "exercicio", "status", "xp_concedido", "atualizado_em")
    list_filter = ("usuario", "status", "exercicio__modulo", "exercicio__estacao")
    search_fields = ("usuario__username", "exercicio__titulo")
    list_select_related = ("usuario", "exercicio", "exercicio__estacao")
    list_editable = ("status", "xp_concedido")
    autocomplete_fields = ("usuario", "exercicio")


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ("nome", "descricao", "ordem")
    search_fields = ("nome", "descricao")
    list_editable = ("ordem",)
    fields = ["nome", "descricao", "ordem", "link_adicionar_secao_form"]
    readonly_fields = ["link_adicionar_secao_form"]

    def link_adicionar_secao_form(self, obj):
        if obj.pk:
            add_secao_url = reverse("admin:exercicios_secao_add")
            url = f"{add_secao_url}?modulo={obj.pk}"
            return format_html(
                '<a href="{}" class="button">Adicionar Nova Seção a este Módulo</a>',
                url,
            )
        return "Salve o módulo primeiro para poder adicionar seções."

    link_adicionar_secao_form.short_description = "Ações de Seção"
