from treekey.models import Node, Species, SpeciesImage, NodeImage, SpeciesLink
from django.contrib import admin


class SpeciesImageInline(admin.TabularInline):
    model = SpeciesImage
    extra = 0

class SpeciesLinkInline(admin.TabularInline):
    model = SpeciesLink
    extra = 0

class SpeciesInline(admin.TabularInline):
    model = Species

class NodeImageInline(admin.TabularInline):
    model = NodeImage
    extra = 0

class NodeAdmin(admin.ModelAdmin):
    inlines = [NodeImageInline]
    list_display = ('name', 'description')
    
class SpeciesAdmin(admin.ModelAdmin):
    inlines = [SpeciesImageInline, SpeciesLinkInline]
    list_display = ('genus', 'species', 'common_name')
    

admin.site.register(Node, NodeAdmin)
admin.site.register(Species, SpeciesAdmin)