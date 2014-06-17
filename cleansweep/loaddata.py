"""Script to load data in the database.

This loads all places in a state. It expects path to a directory with the 
following files as input.

* state.json - JSON file containing key and name of the state.
* lc.txt - TSV file containing LC code and LC name of each Loksabha Constituency in the state.
* ac.txt - TSV file containing LC code, AC code and AC name of each Assembly Constituency in the state.
* pb.txt - TSV file containing AC code, PB code and PB name for each Polling Booth in the state.
"""
import os, sys
import csv
import json

from .models import Place, PlaceType, db

def create_place_types():
    def ensure_place_type(name, short_name, level):
        t = PlaceType.query.filter_by(short_name=short_name).first()
        if not t:
            print "adding", name, short_name, level
            t = PlaceType(name=name, short_name=short_name, level=level)
            db.session.add(t)

    ensure_place_type('Country', 'COUNTRY', 10)
    ensure_place_type('State', 'STATE', 20)
    ensure_place_type('Region', 'REGION', 30)
    ensure_place_type('Loksabha Constituency', 'LC', 40)
    ensure_place_type('Assembly Constituency', 'AC', 50)
    ensure_place_type('Ward', 'WARD', 60)
    ensure_place_type('Polling Center', 'PC', 70)
    ensure_place_type('Polling Booth', 'PB', 80)
    db.session.commit()

def ensure_place_type(name, short_name, level):
    t = PlaceType.query.filter_by(short_name=short_name).first()
    if not t:
        print "adding", name, short_name, level
        t = PlaceType(name=name, short_name=short_name, level=level)
        db.session.add(t)

def ensure_place(key, name, type, parent=None):
    p = Place.find(key)
    if not p:
        p = Place(key=key, name=name, type=type)
        if parent:
            parent.add_place(p)
        else:
            db.session.add(p)
    return p

def read_tsv(path):
    return [[c.strip() for c in row] for row in csv.reader(open(path), delimiter='\t')]    

def load_state(root_dir):
    path = os.path.join(root_dir, "state.json")
    d = json.loads(open(path).read())
    state = ensure_place(key=d['key'], name=d['name'], type=PlaceType.get("STATE"))

    for code, name in read_tsv(os.path.join(root_dir, "lc.txt")):
        key = "{}/{}".format(d['key'], code)
        name = "{} - {}".format(code, name)
        ensure_place(key=key, name=name, type=PlaceType.get("LC"), parent=state)
    db.session.commit()

    for lc_code, ac_code, ac_name in read_tsv(os.path.join(root_dir, "ac.txt")):
        lc_key = "{}/{}".format(d['key'], lc_code)
        lc = Place.find(lc_key)
        ac_key = "{}/{}".format(d['key'], ac_code)
        ac_name = "{} - {}".format(code, ac_name)
        ensure_place(key=ac_key, name=ac_name, type=PlaceType.get("AC"), parent=lc)
    db.session.commit()

    # TODO: Load polling booths

def main(root_dir):
    db.create_all()
    create_place_types()
    load_state(root_dir)

if __name__ == '__main__':
    main(sys.argv[1])