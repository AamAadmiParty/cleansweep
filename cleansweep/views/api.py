from flask import (request, Response)
import json
import requests
from ..app import app
from ..models import Place


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
