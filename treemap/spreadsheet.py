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

# from: http://www.djangosnippets.org/snippets/1151/
class ExcelResponse(HttpResponse):
    
    def __init__(self, data, output_name='excel_data', headers=None,
                 force_csv=False, encoding='utf8'):
        
        # Make sure we've got the right type of data to work with
        valid_data = False
        if isinstance(data, ValuesQuerySet):
            data = list(data)
        elif isinstance(data, QuerySet):
            data = list(data.values())
        if hasattr(data, '__getitem__'):
            if isinstance(data[0], dict):
                if headers is None:
                    headers = data[0].keys()
                data = [[row[col] for col in headers] for row in data]
                data.insert(0, headers)
            if hasattr(data[0], '__getitem__'):
                valid_data = True
        assert valid_data is True, "ExcelResponse requires a sequence of sequences"
        
        import StringIO
        output = StringIO.StringIO()
        # Excel has a limit on number of rows; if we have more than that, make a csv
        use_xls = False
        if len(data) <= 65536 and force_csv is not True:
            try:
                import xlwt
            except ImportError:
                # xlwt doesn't exist; fall back to csv
                pass
            else:
                use_xls = True
        if use_xls:
            book = xlwt.Workbook(encoding=encoding)
            sheet = book.add_sheet('Sheet 1')
            styles = {'datetime': xlwt.easyxf(num_format_str='yyyy-mm-dd hh:mm:ss'),
                      'date': xlwt.easyxf(num_format_str='yyyy-mm-dd'),
                      'time': xlwt.easyxf(num_format_str='hh:mm:ss'),
                      'default': xlwt.Style.default_style}
            
            for rowx, row in enumerate(data):
                for colx, value in enumerate(row):
                    if isinstance(value, datetime.datetime):
                        cell_style = styles['datetime']
                    elif isinstance(value, datetime.date):
                        cell_style = styles['date']
                    elif isinstance(value, datetime.time):
                        cell_style = styles['time']
                    else:
                        cell_style = styles['default']
                    sheet.write(rowx, colx, value, style=cell_style)
            book.save(output)
            mimetype = 'application/vnd.ms-excel'
            file_ext = 'xls'
        else:
            for row in data:
                out_row = []
                for value in row:
                    if not isinstance(value, basestring):
                        value = unicode(value)
                    value = value.encode(encoding)
                    out_row.append(value.replace('"', '""'))
                output.write('"%s"\n' %
                             '","'.join(out_row))            
            mimetype = 'text/csv'
            file_ext = 'csv'
        output.seek(0)
        super(ExcelResponse, self).__init__(content=output.getvalue(),
                                            mimetype=mimetype)
        self['Content-Disposition'] = 'attachment;filename="%s.%s"' % \
            (output_name.replace('"', '\"'), file_ext)

# from: http://www.djangosnippets.org/snippets/1151/
def queryset_to_excel_file( qs, filename, force_csv=False,headers=None, encoding='utf8'):

        data = qs
        
        # Make sure we've got the right type of data to work with
        valid_data = False
        if isinstance(data, ValuesQuerySet):
            data = list(data)
        elif isinstance(data, QuerySet):
            data = list(data.values())
        if hasattr(data, '__getitem__'):
            if isinstance(data[0], dict):
                if headers is None:
                    headers = data[0].keys()
                data = [[row[col] for col in headers] for row in data]
                data.insert(0, headers)
            if hasattr(data[0], '__getitem__'):
                valid_data = True
        assert valid_data is True, "ExcelResponse requires a sequence of sequences"
        
        
        # Excel has a limit on number of rows; if we have more than that, make a csv
        use_xls = False
        file_ext = '.csv'
        if len(data) <= 65536 and force_csv is not True:
            try:
                import xlwt
            except ImportError:
                # xlwt doesn't exist; fall back to csv
                pass
            else:
                use_xls = True
                file_ext = '.xls'
        name = filename + file_ext
        output = file(name,'wb')
        if use_xls:
            book = xlwt.Workbook(encoding=encoding)
            sheet = book.add_sheet('Sheet 1')
            styles = {'datetime': xlwt.easyxf(num_format_str='yyyy-mm-dd hh:mm:ss'),
                      'date': xlwt.easyxf(num_format_str='yyyy-mm-dd'),
                      'time': xlwt.easyxf(num_format_str='hh:mm:ss'),
                      'default': xlwt.Style.default_style}
            
            for rowx, row in enumerate(data):
                for colx, value in enumerate(row):
                    if isinstance(value, datetime.datetime):
                        cell_style = styles['datetime']
                    elif isinstance(value, datetime.date):
                        cell_style = styles['date']
                    elif isinstance(value, datetime.time):
                        cell_style = styles['time']
                    else:
                        cell_style = styles['default']
                    sheet.write(rowx, colx, value, style=cell_style)
            book.save(output)
        else:
            for row in data:
                out_row = []
                for value in row:
                    if not isinstance(value, basestring):
                        value = unicode(value)
                    value = value.encode(encoding)
                    out_row.append(value.replace('"', '""'))
                output.write('"%s"\n' %
                             '","'.join(out_row))
        output.close()
        return name