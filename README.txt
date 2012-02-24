Installation Instructions
------------

Required programs: 
    Webserver - Apache2 is recommended
    Database - Postgres 8.4 + postgis 1.5 is recommended, Something compatable with Django required
    Map tile renderer - GeoServer(java) on tomcat is recommended (port 8081)
    SMTP service - sendmail is recommended
    tile caching service - tilecache is recommended (port 8080 through apache)
    Python 2.7 

Required libraries from aptitude
    python-django (version 1.3)
    libapache2-mod-wsgi
    python-psycopg2 (only for postgres access)
    binutils
    libgeos-3.2.0
    libgeos-cl
    libgdal1-1.6.0
    libproj0
    python-django-tagging 
    python-imaging 
    python-xlrd 
    python-feedparser 
    python-memcache 
    python-beautifulsoup 
    python-django-debug-toolbar 
    python-simplejson 
    python-django-extensions
    python-gdal
    gdal-bin

Required libraries from the web    
    wget http://django-template-utils.googlecode.com/files/template_utils-0.4p2.tar.gz
    wget https://bitbucket.org/ubernostrum/django-profiles/get/tip.tar.gz
    wget http://pypi.python.org/packages/source/U/Unidecode/Unidecode-0.04.5.tar.gz
    wget http://geopy.googlecode.com/files/geopy-0.94.tar.gz
    wget http://django-pagination.googlecode.com/files/django-pagination-1.0.5.tar.gz
    wget https://bitbucket.org/springmeyer/django-shapes/get/tip.tar.gz
    wget http://thumbnail.sorl.net/sorl-thumbnail-3.2.5.tar.gz
    wget http://sourceforge.net/projects/dbfpy/files/dbfpy/2.2.5/dbfpy-2.2.5.tar.gz
    wget https://bitbucket.org/jiaaro/django-badges/get/tip.tar.gz
    wget https://bitbucket.org/ubernostrum/django-registration/downloads/django-registration-0.8-alpha-1.tar.gz
    git clone git://github.com/miracle2k/webassets.git
    pip install django-pipeline

Patches:
    Fix to proj to deal with spherical mercator
        wget http://download.osgeo.org/proj/proj-datumgrid-1.4.tar.gz
        tar -xzf /proj-datumgrid-1.4.tar.gz
        cd proj-datumgrid-1.4
        nad2bin null < null.lla
		sudo cp null /usr/share/proj
    Get django-sorting and fix bug
        git clone git://github.com/directeur/django-sorting.git
		Apply patch to django-sorting: 
            https://github.com/directeur/django-sorting/issues#issue/8
			-including comment by Alsaihn
		sudo cp django-sorting -R /usr/local/lib/python2.6/dist-packages/django_sorting
    Get django-shapes and remove HttpResponse call
        wget https://bitbucket.org/springmeyer/django-shapes/get/tip.tar.gz
        In shapes/views/export.py - zip-response method - change >
            # Stick it all in a django HttpResponse
            #response = HttpResponse(zip_stream, mimetype=mimetype)
            #response['Content-Disposition'] = 'attachment; filename=%s.zip' % file_name.replace('.shp','')
            #response['Content-length'] = str(len(zip_stream))
            #response['Content-Type'] = mimetype
            #response.write(zip_stream)
            return zip_stream
    Get django-reputation and fix default config and user bug
        svn checkout http://django-reputation.googlecode.com/svn/trunk/ django-reputation
		cd django-reputation
		sudo cp django_reputation -R /usr/local/lib/python2.6/dist-packages/django_reputation
		Change default config and user bug: (b/c it doesn't seem to accept values in settings.py)
			cd /usr/local/lib/python2.6/dist-packages/django_reputation
			In config.py - <change values as needed>
            In model.py - change >
                ....
                relevent_reputation_actions = UserReputationAction.onbjects.filter(user=user).filter........
                ....
                if expected_delta <= MAX_REPUTATION_GAIN_PER_DAY and expected_delta >= -1 * MAX_REPUTATION_LOSS_PER_DAY:
                    delta = action_value
                elif expected_delta > MAX_REPUTATION_GAIN_PER_DAY:
                    delta = 0
                elif expected_delta < MAX_REPUTATION_LOSS_PER_DAY:
                    delta = 0
                ...
    Fix Tilecache TMS issue if needed
		In tilecache/Services/TMS.py - change > 
			...
			elif len(parts) < 2:
				return self.serviceCapabilities(host, self.service.layers)
			else:
		     +  parts = parts[-5:]
				layer = self.getLayer(parts[1])
				if len(parts) < 3:
				return self.layerCapabilities(host, layer)
			...

