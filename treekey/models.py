from django.db import models

# Species identification info for the key
# try to focus on what sets this species apart
class Species(models.Model):
    genus = models.CharField(max_length=200)
    species = models.CharField(max_length=200, blank=True)
    variety = models.CharField(max_length=200, blank=True)
    common_name = models.CharField(max_length=200)
    symbol = models.CharField(max_length=10, blank=True)
    feature = models.CharField(max_length=500)
    type = models.CharField(max_length=200, blank=True)
    form = models.CharField(max_length=500, blank=True)
    leaf = models.CharField(max_length=500, blank=True)
    flower = models.CharField(max_length=500, blank=True)
    bark = models.CharField(max_length=500, blank=True)
    fruit = models.CharField(max_length=500, blank=True)
    other = models.CharField(max_length=200, blank=True)
    
    class Meta:
        verbose_name_plural = "Species"
    
    def __unicode__(self):
        return self.common_name
        
    # Pull the first image for the node display
    def first_image_url(self):
        if self.speciesimage_set.count() == 0:
            return "/static/Species/tree_not_found.png"
        si_list = self.speciesimage_set.all()
        return si_list[0].image.url
            
# Each species can have more than one image
# The first image entered should be iconic or aid in identification
class SpeciesImage(models.Model):
    image = models.FileField(upload_to='Species')
    caption = models.CharField(max_length=200)
    species = models.ForeignKey(Species)
    attrib_text = models.CharField(max_length=200, blank=True)
    attrib_link = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.species.common_name

# Link to outside resources for a spieces
class SpeciesLink(models.Model):
    text = models.CharField(max_length=200)
    url = models.CharField(max_length=200)
    species = models.ForeignKey(Species)

# Nodes are decision points in a key and have a child view and parent page
# A node can point up to either another node (though their parent_node fields)
#    or point down to one or more species, and may do both
class Node(models.Model):
    name = models.CharField(max_length=200)  
    description = models.CharField(max_length=500)  #longer description for the child display
    question = models.CharField(max_length=500)  #short quesiton choice for the parent display
    parent_node = models.ForeignKey('self', blank=True, null=True, related_name='child_set')
    species = models.ManyToManyField(Species, null=True, blank=True)

    def __unicode__(self):
        return self.name
        
    def has_children(self):
        return self.child_set.count() > 0
        
    def has_parent(self):
        return self.parent_node != None

# An iconic image to help users at the child display of this node. 
# There should only be one per node, but this is not enforced
class NodeImage(models.Model):
    image = models.FileField(upload_to='Nodes')
    caption = models.CharField(max_length=200)
    node = models.ForeignKey(Node)
    attrib_text = models.CharField(max_length=200, blank=True)
    attrib_link = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return self.node.name        
