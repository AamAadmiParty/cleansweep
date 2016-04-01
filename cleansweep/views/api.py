from flask import (request, Response, jsonify)
import json
import requests
from .. import helpers as h
from ..app import app
from ..models import Place, Member, db
from ..core import rbac, smslib
from ..plugins.audit import record_audit
from admin import get_sms_config
from flask_cors import CORS
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired

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


@app.route("/api/send-sms", methods=['POST'])
def send_sms():
    token = request.form['token']
    place_key = request.form['place']
    message = request.form['message']

    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        return jsonify(error="Token expired: %s" % token), 400
    except BadSignature:
        return jsonify(error="Invalid token: %s" % token), 400
    scope_in_list = data['scope']  # Get scope from token

    if 'send-sms' not in scope_in_list:  # TODO Implement a better way to handle this?
        return jsonify(error="This token can not be used to send sms."), 403

    place = Place.find(key=place_key)
    if not place:
        return jsonify(error="Invalid place: '%s'" % place_key), 400

    phone = data['phone']  # Get phone number of the user who sent the sms to init this request.
    user = Member.find(phone=phone)
    if user is None:  # This is never going to happen. We already checked this in authorize. But still.
        return jsonify(error="No user found with %s." % phone), 404

    has_permission = rbac.can(user, "write", place)  # TODO Change the action to 'send-sms' when its added.
    if not has_permission:
        return jsonify(error="User does not have permission on '%s'" % place_key)

    config = get_sms_config(place)
    sms_provider = config and smslib.get_sms_provider(**config)
    if sms_provider is None:
        return jsonify(error="SMS is not configured for place '%s'" % place_key), 404

    people = place.get_all_members_iter()
    phone_numbers = [p.phone for p in people]
    sms_provider.send_sms_async(phone_numbers, message)
    record_audit(
        action="send-sms",
        timestamp=None,
        place=place,
        data=dict(message=message, place=place_key)
    )
    db.session.commit()
    return jsonify({'feedback': "Your message has been sent to all the volunteers of '%s'." % place_key})


@app.route("/api/user", methods=['GET'])
def api_user():
    user = h.get_current_user()
    if not user:
        d = dict(message="Bad credentials")
        return jsonify(d), 401

    return jsonify(user.dict(include_place=True))
