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
        self.route("/notify", methods=['POST'])(self.notifylink)

    def fullmap(self):
        return render_template('map.html',
                               lat=config['ORIGINAL_LATITUDE'],
                               lng=config['ORIGINAL_LONGITUDE'],
                               gmaps_key=config['GMAPS_KEY'],
                               lang=config['LOCALE'])

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
        
        if(lat==None and lon==None):
            lat = request.form.get('lat', type=float)
            lon = request.form.get('lon', type=float)
        if not (lat and lon):
            print('[-] Invalid next location: %s,%s' % (lat, lon))
            return 'bad parameters', 400
        else:
            config['ORIGINAL_LATITUDE'] = lat
            config['ORIGINAL_LONGITUDE'] = lon
            return '<script>window.location="/"</script>'
            
    def updatelink(self):
            return '<script> getLocation(); function getLocation() { if (navigator.geolocation) { navigator.geolocation.getCurrentPosition(showPosition, showError); } else { window.alert("Geolocation is not supported by this browser."); } } function showPosition(position) { var latlon = position.coords.latitude + "," + position.coords.longitude; window.location="/next_loc?lat="+position.coords.latitude+"&lon="+position.coords.longitude } function showError(error) { switch(error.code) { case error.PERMISSION_DENIED: window.alert("Geolocation permissions have been denied."); break; case error.POSITION_UNAVAILABLE: window.alert("Location information is unavailable."); break; case error.TIMEOUT: window.alert("The request to get user location timed out."); break; case error.UNKNOWN_ERROR: window.alert("An unknown error occurred."); break; } window.location="/"} </script>'

    def notifylink(self):
        lat = request.form.get('lat', type=float)
        lon = request.form.get('lon', type=float)        
        name = request.form.get('pokename', type=str)
        disappear_time = request.form.get('time', type=int)
        disappear_time = disappear_time/1000
	pokeID = request.form.get('pokeID', type=int)
		
	if not(pokeID in [1,2,3,4,5,6,7,8,9,15,18,25,26,28,31,34,35,36,37,38,39,40,45,49,51,58,59,62,64,65,67,68,71,73,76,80,83,85,88,89,91,94,95,103,105,106,107,108,110,111,112,113,115,117,121,122,123,125,126,127,128,130,131,132,133,134,135,136,137,139,141,142,143,144,145,146,147,148,149,150,151]):
            return 'No alerted needed'
			
        import smtplib
        import time
	
        fromAddress = config['FROM_GMAIL_USER']  
	toAddress = config['NOTIFY_EMAIL']
	subject = 'Pokemon Alert'  
	body = str("ALERT: " + str(name) + " until: " + datetime.fromtimestamp(disappear_time).strftime("%H:%M:%S") + " http://maps.google.com/maps?z=12&t=m&q=loc:"+str(lat)+"+"+str(lon))
        email_text = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (fromAddress, toAddress, subject))
        email_text = email_text + body
        
	gmail_user = fromAddress
	gmail_password = config['FROM_GMAIL_PW']

        try:  
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(gmail_user, gmail_password)
            server.sendmail(fromAddress, toAddress, email_text)
            server.close()
            print '\t\t\t[+] Email sent!'
	except:  
            print '\t\t\t[***] Email alert couldnt be sent'

        return 'ok'
            
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
