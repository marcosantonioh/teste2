from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Exercicio, Modulo, Secao, Estacao
from import_export.admin import ExportMixin, ImportExportModelAdmin


@admin.register(Exercicio)
class ExercicioAdmin(ImportExportModelAdmin):
    pass

# Admin para Exercicio
class ExercicioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'estacao', 'modulo', 'tipo', 'status')
    list_filter = ('estacao__secao__modulo', 'estacao__secao', 'estacao', 'tipo', 'status')
    search_fields = ('titulo', 'enunciado')
    # Adicione aqui outros campos e configurações que você já utiliza ou deseja

    def get_changeform_initial_data(self, request):
        """
        Pré-preenche dados no formulário de adição de Exercicio.
        """
        initial = super().get_changeform_initial_data(request)
        estacao_id = request.GET.get('estacao') # Pega o ID da estação da URL
        if estacao_id:
            try:
                estacao_obj = Estacao.objects.get(pk=estacao_id)
                initial['estacao'] = estacao_obj
                # Opcional: Pré-preencher o módulo do exercício com base no módulo da estação
                if hasattr(estacao_obj, 'secao') and hasattr(estacao_obj.secao, 'modulo'):
                    initial['modulo'] = estacao_obj.secao.modulo
            except Estacao.DoesNotExist:
                # Lida com o caso de um ID de estação inválido, se necessário
                pass
        return initial

# Admin para Secao
class SecaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'modulo', 'status', 'ordem')
    list_filter = ('modulo', 'status')
    search_fields = ('nome',)
    list_editable = ('ordem',) # Permite editar a ordem diretamente na lista
    fields = ['nome', 'modulo', 'status', 'ordem', 'link_adicionar_estacao_form']
    readonly_fields = ['link_adicionar_estacao_form']

    def link_adicionar_estacao_form(self, obj):
        if obj.pk:
            add_estacao_url = reverse('admin:exercicios_estacao_add')
            url_com_parametro = f"{add_estacao_url}?secao={obj.pk}"
            return format_html(
                '<a href="{}" class="button">Adicionar Nova Estação a esta Seção</a>',
                url_com_parametro
            )
        return "Salve a seção primeiro para poder adicionar estações."
    link_adicionar_estacao_form.short_description = "Ações de Estação"

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        modulo_id = request.GET.get('modulo')
        if modulo_id:
            try:
                initial['modulo'] = Modulo.objects.get(pk=modulo_id)
            except Modulo.DoesNotExist:
                pass
        return initial

# Admin para Estacao
class EstacaoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'secao', 'status') # Adicione 'ordem' se implementado e desejado aqui
    list_filter = ('secao__modulo', 'secao', 'status')
    search_fields = ('nome',)
    list_editable = ('secao', 'status') # Permite editar a seção e o status diretamente na lista

    # Define os campos que aparecerão no formulário de edição/criação da Estacao
    # Incluímos nosso método que renderiza o link
    fields = ['nome', 'secao', 'status', 'link_adicionar_exercicio_form']
    readonly_fields = ['link_adicionar_exercicio_form'] # O link será um campo apenas de leitura

    def link_adicionar_exercicio_form(self, obj):
        """
        Renderiza um link no formulário de edição da Estacao para adicionar um novo Exercicio.
        'obj' é a instância da Estacao que está sendo editada.
        """
        if obj.pk: # Só mostra o link se a estação já foi salva (tem uma primary key)
            # Constrói a URL para a página de adição de Exercicio do admin
            # 'admin:app_label_model_name_add' é o padrão de nomenclatura
            add_exercicio_url = reverse('admin:exercicios_exercicio_add')
            # Adiciona o ID da estação atual como parâmetro GET para pré-preenchimento
            url_com_parametro = f"{add_exercicio_url}?estacao={obj.pk}"
            return format_html(
                '<a href="{}" class="button">Adicionar Novo Exercício a esta Estação</a>', 
                url_com_parametro
            )
        return "Salve a estação primeiro para poder adicionar exercícios."
    link_adicionar_exercicio_form.short_description = "Ações de Exercício" # Label do "campo" no formulário

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        secao_id = request.GET.get('secao')
        if secao_id:
            try:
                initial['secao'] = Secao.objects.get(pk=secao_id)
            except Secao.DoesNotExist:
                pass
        return initial

# Admin para Modulo
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'ordem')
    search_fields = ('nome', 'descricao')
    list_editable = ('ordem',) # Permite editar a ordem diretamente na lista
    fields = ['nome', 'descricao', 'ordem', 'link_adicionar_secao_form']
    readonly_fields = ['link_adicionar_secao_form']


    def link_adicionar_secao_form(self, obj):
        if obj.pk:
            add_secao_url = reverse('admin:exercicios_secao_add')
            url_com_parametro = f"{add_secao_url}?modulo={obj.pk}"
            return format_html(
                '<a href="{}" class="button">Adicionar Nova Seção a este Módulo</a>',
                url_com_parametro
            )
        return "Salve o módulo primeiro para poder adicionar seções."
    link_adicionar_secao_form.short_description = "Ações de Seção"




# Registra os modelos com suas classes Admin customizadas
# É uma boa prática desregistrar primeiro se eles já foram registrados de forma padrão
if admin.site.is_registered(Exercicio):
    admin.site.unregister(Exercicio)
admin.site.register(Exercicio, ExercicioAdmin)

if admin.site.is_registered(Estacao):
    admin.site.unregister(Estacao)
admin.site.register(Estacao, EstacaoAdmin)

if admin.site.is_registered(Secao):
    admin.site.unregister(Secao)
admin.site.register(Secao, SecaoAdmin)

if admin.site.is_registered(Modulo):
    admin.site.unregister(Modulo)
admin.site.register(Modulo, ModuloAdmin)