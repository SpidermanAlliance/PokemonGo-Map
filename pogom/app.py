#!/usr/bin/python
# -*- coding: utf-8 -*-

import calendar
from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder
from datetime import datetime

from . import config
from .models import Pokemon, Gym, Pokestop


class Pogom(Flask):
    def __init__(self, import_name, **kwargs):
        super(Pogom, self).__init__(import_name, **kwargs)
        self.json_encoder = CustomJSONEncoder
        self.route("/", methods=['GET'])(self.fullmap)
        self.route("/raw_data", methods=['GET'])(self.raw_data)
        self.route("/next_loc", methods=['GET'])(self.next_loc)
        self.route("/update", methods=['GET'])(self.updatelink)

    def fullmap(self):
        return render_template('map.html',
                               lat=config['ORIGINAL_LATITUDE'],
                               lng=config['ORIGINAL_LONGITUDE'],
                               gmaps_key=config['GMAPS_KEY'])

    def raw_data(self):
        d = {}
        if request.args.get('pokemon', 'true') == 'true':
            d['pokemons'] = Pokemon.get_active()

        if request.args.get('pokestops', 'false') == 'true':
            d['pokestops'] = Pokestop.get_all()

        if request.args.get('gyms', 'true') == 'true':
            d['gyms'] = Gym.get_all()

        return jsonify(d)

    def next_loc(self):
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if not (lat and lon):
            print('[-] Invalid next location: %s,%s' % (lat, lon))
            return 'bad parameters', 400
        else:
            config['ORIGINAL_LATITUDE'] = lat
            config['ORIGINAL_LONGITUDE'] = lon
            return '<script>window.location="/"</script>'
            
    def updatelink(self):
            return '<script> getLocation(); function getLocation() { if (navigator.geolocation) { navigator.geolocation.getCurrentPosition(showPosition, showError); } else { window.alert("Geolocation is not supported by this browser."); } } function showPosition(position) { var latlon = position.coords.latitude + "," + position.coords.longitude; window.location="/next_loc?lat="+position.coords.latitude+"&lon="+position.coords.longitude } function showError(error) { switch(error.code) { case error.PERMISSION_DENIED: window.alert("Geolocation permissions have been denied."); break; case error.POSITION_UNAVAILABLE: window.alert("Location information is unavailable."); break; case error.TIMEOUT: window.alert("The request to get user location timed out."); break; case error.UNKNOWN_ERROR: window.alert("An unknown error occurred."); break; } } </script>'


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, datetime):
                if obj.utcoffset() is not None:
                    obj = obj - obj.utcoffset()
                millis = int(
                    calendar.timegm(obj.timetuple()) * 1000 +
                    obj.microsecond / 1000
                )
                return millis
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)
