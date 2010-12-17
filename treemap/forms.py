from django import forms
from models import Tree, Species, TreePhoto, Neighborhood, ZipCode
from django.contrib.auth.models import User
from django.contrib.localflavor.us.forms import USZipCodeField

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, 
           help_text="Full Name", widget=forms.TextInput(attrs={'size':'40'}),required=False)
    subject = forms.CharField(max_length=100, 
              help_text="Subject of your message", widget=forms.TextInput(attrs={'size':'40'}))
    sender = forms.EmailField(
              help_text="Your email address", widget=forms.TextInput(attrs={'size':'40'}),required=True)
    message = forms.CharField(
              help_text="Please enter as much text as you would like", 
              widget=forms.Textarea(attrs={'rows':'12','cols':'60'}))
    cc_myself = forms.BooleanField(required=False, 
                help_text="Send yourself a copy of this message")
                
class TreeEditPhotoForm(forms.ModelForm):
    class Meta:
        model = TreePhoto
        exclude = ('reported_by',)
        fields = ('title','photo',)

class TreeAddForm(forms.Form):
    edit_address_street = forms.CharField(required=False)
    edit_address_city = forms.CharField(required=True)
    edit_address_zip = USZipCodeField(required=False)
    species_name = forms.CharField(max_length=200,required=False)
    dbh = forms.FloatField(required=False)
    #species_id = forms.CharField(required=False)
    species_id = forms.CharField(widget=forms.HiddenInput, required=False)
    lat = forms.FloatField(widget=forms.HiddenInput,required=True)
    lon = forms.FloatField(widget=forms.HiddenInput,required=True)
 
    def save(self,request):
        from django.contrib.gis.geos import Point
        species = self.cleaned_data.get('species_id')
        if species:
            spp = Species.objects.filter(symbol=species)
            if spp:
                new_tree = Tree(species=spp[0])
            else:
                new_tree = Tree()
        else:
            new_tree = Tree()
        add = self.cleaned_data.get('edit_address_street')
        if add:
            new_tree.address_street = add
            new_tree.geocoded_address = add
        city = self.cleaned_data.get('edit_address_city')
        if city:
            new_tree.address_city = city

        zip_ = self.cleaned_data.get('edit_address_zip')
        if zip_:
            new_tree.address_zip = zip_
            
        #import pdb;pdb.set_trace()
        pnt = Point(self.cleaned_data.get('lon'),self.cleaned_data.get('lat'),srid=4326)
        new_tree.geometry = pnt
        print pnt
        n = Neighborhood.objects.filter(geometry__contains=pnt)
        z = ZipCode.objects.filter(geometry__contains=pnt)
        print n, z
        if n: new_tree.neighborhood = n[0]
        else: new_tree.neighborhood = None
        if z: new_tree.zipcode = z[0]
        else: new_tree.zipcode = None
        new_tree.last_updated_by = request.user
        new_tree.save()
        dbh = self.cleaned_data.get('dbh')
        if dbh:
            ts = TreeStatus(
                reported_by = request.user,
                value = dbh,
                key = 'dbh',
                tree = new_tree)
            ts.save()
        return new_tree
#(-75.1593616604804993 39.9517746248708292)
       
class _TreeAddForm(forms.ModelForm):
    data_owner = forms.CharField(widget=forms.HiddenInput, required=False)
    geometry = forms.CharField(required=True)
    species = forms.CharField(required=True)
    #species = forms.CharField(required=False)

    def clean_data_owner(self):
        """
        generally should be the editing user, but if owner already exists, then keep it as it was
        """
        data = self.cleaned_data['data_owner']
        if data:
            user = User.objects.get(id=data)
            return user
        
    
    def clean_species(self):
        """
        for a new tree, we're expecting something in the form of: 
            "Accepted_Symbol,cultivar_name"
        where cultivar may be blank
        """
        data = self.cleaned_data['species']
        #if not data:
        #    return
        if data.isdigit():
            existing_species = Species.objects.get(id=int(data)) 
            if existing_species == self.instance.species:
                print 'species unchanged'
                return existing_species
        
        
        species,cultivar = data.split(',')
        result = Species.objects.filter(accepted_symbol=species)
        
        if cultivar:
            result = result.filter(cultivar_name = cultivar)
        if not result:
            raise forms.ValidationError("%s is an invalid species" % data)
        return result[0]

    class Meta:
        model = Tree
        fields = (
        'data_owner',
        'address_street',
        'address_city',
        'address_zip',
        'geometry',
        # not required will add in edit_form...
        #'species',
        #'condition',
        #'tree_owner',
        #'plot_length',
        #'plot_width',
        #'plot_type',
        #'powerline_conflict_potential',
        )

    def __init__(self, *args, **kwargs):
        super(TreeAddForm, self).__init__(*args, **kwargs)
