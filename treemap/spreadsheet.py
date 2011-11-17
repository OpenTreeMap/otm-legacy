import os
import shutil
import zipfile
import tempfile
import datetime

from django.db.models.query import QuerySet, ValuesQuerySet
from django.contrib.gis.db.models.fields import GeometryField
from django.utils import simplejson
from django.http import HttpResponse
from django.utils.encoding import smart_str, smart_unicode
from django.utils.translation import ugettext as _

class LazyIterator(object):
    def __init__(self, query_set, chunk_size=100):
        self.query_set = query_set
        self.chunk_size = chunk_size
        self.chunk_index = 0
        self.current_list_index = 0
        self.current_list_length = 0
        
    def __iter__(self): 
        return self

    def __len__(self): 
        raise Exception("You can't do that because calling length would make it not lazy")
    
    def reset(self):
        self.chunk_index = 0
        self.current_list_index = 0
        self.current_list_length = 0

    def next(self):
        if (self.current_list_index < self.current_list_length):
            # return the thing
            current_item = self.current_list[self.current_list_index]
            self.current_list_index = self.current_list_index + 1
            return current_item
        else: 
            self.next_chunk()
            if self.current_list_length == 0:
                raise StopIteration
            return self.next()

    def next_chunk(self):
        # Update index and set current list to the next chunk
        # if len(self.this_chunk) == 0 at the end of this then we're done
        next_index = self.chunk_index + self.chunk_size
        next_chunk = self.query_set[self.chunk_index:next_index]
        self.chunk_index = next_index
        self.current_list = list(next_chunk)
        self.current_list_index = 0
        self.current_list_length = len(self.current_list)

# from: http://www.djangosnippets.org/snippets/1151/
class ExcelResponse(HttpResponse):
    
    def __init__(self, data, output_name='excel_data', headers=None,
                 force_csv=False, encoding='utf8'):
        
        # Make sure we've got the right type of data to work with
        valid_data = False
        if isinstance(data, ValuesQuerySet):
            data = LazyIterator(data)
            #data = list(data)
        elif isinstance(data, QuerySet):
            data = LazyIterator(data.values())
        headers = next(data).keys()

        
        import StringIO
        output = StringIO.StringIO()
        output.write('"%s"\n' % '","'.join(headers))    
        flush_index = 0
        for row in data:
            row = [row[col] for col in headers]
            out_row = []
            for value in row:
                if not isinstance(value, basestring):
                    value = unicode(value)
                value = value.encode(encoding)
                out_row.append(value.replace('"', '""'))
            output.write('"%s"\n' %
                         '","'.join(out_row))     
            flush_index = flush_index + 1       
            if flush_index == 1000: 
                output.flush()
                print "Flushing!"
                flush_index = 0

        mimetype = 'text/csv'
        file_ext = 'csv'
        output.seek(0)
        super(ExcelResponse, self).__init__(content=output.getvalue(),
                                            mimetype=mimetype)
        self['Content-Disposition'] = 'attachment;filename="%s.%s"' % \
            (output_name.replace('"', '\"'), file_ext)


