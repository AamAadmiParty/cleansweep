from flask import (request, Response)
import json
import requests
from ..app import app
from ..models import Place
from flask_cors import CORS

cors = CORS(app, resources={r"/api/*": {"origins": "*", "headers": "accept, x-requested-with"}})

@app.route("/api/geosearch")
def api_geosearch():
    if 'lat' not in request.args or 'lon' not in request.args:
        d = {"error": "Please specify lat and lon parameters"}
        return Response(json.dumps(d), mimetype="application/json")        
    else:
        response = requests.get("http://geosearch-anandology.rhcloud.com/geosearch", params=request.args)
        data = response.json()
        key = data.get('result', {}).get('pb_key')
        app.logger.info(data)
        place = key and Place.find(key=key)
        if not place:
            d = {'error': 'Sorry, the specified location is not yet covered.'}
            return Response(json.dumps(d), mimetype="application/json")

        if 'within' in request.args:
            parent = Place.find(request.args['within'])
            if parent and not place.has_parent(parent):
                d = {'error': 'Sorry, the specified location is not outside the current region.'}
                return Response(json.dumps(d), mimetype="application/json")

        d = {
            "query": data['query'],
            "result": {
            }
        }
        for p in [place] + place.parents:
            type_name = p.type.short_name.lower()
            d['result'][type_name + "_key"] = p.key
            d['result'][type_name + "_name"] = p.name
    return Response(json.dumps(d, sort_keys=True), mimetype="application/json")

@app.route("/api/place/<place:key>")
def api_place(key):
    place = key and Place.find(key=key)
    if not place:
        d = {"error": "Invalid place"}
        return Response(json.dumps(d), mimetype="application/json")
    else:
        parents = place.parents
        d = {
            "key": key,
            "type": place.type.short_name,
            "name": place.name,
            "parents": [dict(key=p.key, type=p.type.short_name, name=p.name) for p in parents]
        }
        return Response(json.dumps(d), mimetype="application/json")
