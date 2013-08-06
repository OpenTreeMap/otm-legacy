![OpenTreeMap Logo](https://github.com/azavea/OpenTreeMap/raw/master/static/images/Philadelphia/es/2011_opentreemap_trans.png)

#Updates? Issues? Questions?#
For updates join the announcement email list here: http://groups.google.com/group/opentreemap-user
For issues or questions you can try mailing the user list: http://groups.google.com/group/opentreemap-user or connect with us via IRC at #opentreemap on freenode (freenode.net).

This is v1.3 of OpenTreeMap, the in development version.

#Other Repositories
OpenTreeMap is also available for iOS and Android.

iOS app code is available at https://github.com/azavea/OpenTreeMap-iOS <br>
Default graphics and config files for the OpenTreeMap iOS app are available at https://github.com/azavea/OpenTreeMap-iOS-skin

Android app code is available at https://github.com/azavea/OpenTreeMap-Android <br>
A default skin is included in the repository, as are "howto.pdf" build instructions.

#Installation Instructions#
###Required programs:###
* Webserver - Gunicorn is recommended
* Database - Postgres 8.1 + postgis 1.5 is recommended (postgis 2.0+ is not yet supported)
* Map tile renderer - GeoServer(java) on tomcat is recommended
* SMTP service - sendmail is recommended
* tile caching service - tilecache is recommended (port 8080 through apache)
* Python 2.7

###Required python libraries (installed via pip)###
* BeautifulSoup (3.2.0)
* Django (1.3.4)
* PIL (1.1.7)
* South (0.7.5)
* Unidecode (0.04.9)
* django-badges (0.1.6)
* django-debug-toolbar (0.9.1)
* django-extensions (0.7.1)
* django-pagination (1.0.7)
* django-profiles (0.2)
* django-shapes (0.2.0)
* django-sorting (0.1)
* django-tagging (0.3.1)
* django-threadedcomments
* django-pipeline (1.1.27)
* feedparser (5.1)
* geopy (0.94.1)
* psycopg2 (2.4.1)
* python-omgeo (1.4.1)
* simplejson (2.3.2)
* sorl-thumbnail (11.12)
* template-utils (0.4p2)
* wsgiref (0.1.2)
* xlrd (0.7.1)
* yuicompressor (2.4.6.1)

###Optional libraries###
* gunicorn (0.14.3) (via pip)
* libapache2-mod-wsgi (if you want to run with apache) (via apt)

###Required libraries from aptitude###
* binutils
* libgeos-3.2.0
* libgeos-c1
* libgdal1-1.6.0
* libproj0
* gdal-bin

###Required libraries from the web###
* wget http://sourceforge.net/projects/dbfpy/files/dbfpy/2.2.5/dbfpy-2.2.5.tar.gz
* wget https://bitbucket.org/ubernostrum/django-registration/downloads/django-registration-0.8-alpha-1.tar.gz
* git clone git://github.com/miracle2k/webassets.git
* pip install django-pipeline==1.1.27

###Patches:###
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
                sudo cp django_sorting -R /usr/local/lib/python2.6/dist-packages/django_sorting
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
                relevant_reputation_actions = UserReputationAction.objects.filter(user=user).filter........
                ....
                if expected_delta <= MAX_REPUTATION_GAIN_PER_DAY and expected_delta >= -1 * MAX_REPUTATION_LOSS_PER_DAY:
                    delta = action_value
                elif expected_delta > MAX_REPUTATION_GAIN_PER_DAY:
                    delta = 0
                elif expected_delta < MAX_REPUTATION_LOSS_PER_DAY:
                    delta = 0
                ...
    Fix Tilecache TMS issue
                In tilecache/Services/TMS.py - change >
                        ...
                        elif len(parts) < 2:
                                return self.serviceCapabilities(host, self.service.layers)
                        else:
                    + parts = parts[-5:]
                                layer = self.getLayer(parts[1])
                                if len(parts) < 3:
                                return self.layerCapabilities(host, layer)
                        ...
