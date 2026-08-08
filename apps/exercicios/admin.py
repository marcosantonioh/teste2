from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Exercicio, Modulo, Secao, Estacao
from import_export.admin import ImportExportModelAdmin


@admin.register(Exercicio)
class ExercicioAdmin(ImportExportModelAdmin):
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
                    "status",
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
                "fields": ("codigo", "resposta_texto_codigo"),
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
    list_display = ("nome", "modulo", "status", "ordem")
    list_filter = ("modulo", "status")
    search_fields = ("nome",)
    list_editable = ("ordem",)
    fields = ["nome", "modulo", "status", "ordem", "link_adicionar_estacao_form"]
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
    list_display = ("nome", "secao", "status", "disponivel_para_visitantes")
    list_filter = ("secao__modulo", "secao", "status", "disponivel_para_visitantes")
    search_fields = ("nome",)
    list_editable = ("secao", "status")
    fields = [
        "nome",
        "secao",
        "status",
        "disponivel_para_visitantes",
        "link_adicionar_exercicio_form",
    ]
    readonly_fields = ["link_adicionar_exercicio_form"]

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
