from flask import (request, Response, jsonify)
import json
import requests
from ..app import app
from ..models import Place, Member
from flask_cors import CORS
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

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


@app.route("/api/authorize", methods=['POST'])
def authorize():
    client_id = request.form['client-id']
    client_secret = request.form['client-secret']

    for trusted_app in app.config['TRUSTED_APPS']:
        if trusted_app['client-id'] == client_id and trusted_app['client-secret'] == client_secret:

            scope_as_str = request.form['scope']  # String of scope(s) separated by space. Ex:'send-sms view-volunteers'
            scope_in_list = scope_as_str.split()

            for scope in scope_in_list:
                if scope not in trusted_app['scope']:
                    # Scope values are same as permissions.
                    # if scope in app.config['SCOPES']:  # TODO Check if scope is a valid.
                    #     return jsonify(error="This app does not have permission for %s." % scope), 403
                    # else:
                    return jsonify(error="Invalid scope: %s" % scope), 400

            # If its cleansweep-sms-bridge do some additional checks.
            # 1. Get phone number of the user who sent the message.
            # 2. Find user with that phone number. If the number is not registered with any user, return 404.
            # 3. Check if the user has permission for the scope. If not, return 403.
            if trusted_app['app-name'] == "cleansweep-sms-bridge":
                phone = request.form['phone']
                user = Member.find(phone=phone)
                if user is None:
                    return jsonify(error="No user found with %s." % phone), 404

                # TODO Check if user has permission or not
                # return jsonify(error="The user does not have permission for %s." % scope), 403

                signed_data = {'phone': phone}  # Encode phone number in token
            else:
                signed_data = {}

            # Create a signed message using app's secret key. Expires in 5 minutes (300 seconds)
            s = Serializer(app.config['SECRET_KEY'], expires_in=300)

            signed_data['scope'] = scope_in_list
            token = s.dumps(signed_data)

            return jsonify(token=token, scope=scope_as_str), 200, {'Cache-Control': 'no-store'}
