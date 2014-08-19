"""Script to load data in the database.

This loads all places in a state. It expects path to a directory with the 
following files as input.

* state.json - JSON file containing key and name of the state.
* lc.txt - TSV file containing LC code and LC name of each Loksabha Constituency in the state.
* ac.txt - TSV file containing LC code, AC code and AC name of each Assembly Constituency in the state.
* pb.txt - TSV file containing AC code, PB code and PB name for each Polling Booth in the state.
"""
import os, sys
import re
import csv
import json
import logging
from .models import Place, PlaceType, db

logger = logging.getLogger("cleansweep.loaddata")


class Loader:
    """Utility to load places from cleansweep data dir.
    """
    def __init__(self, root):
        self.root = root
        self.place_cache = {}

    def is_valid_file(self, filename):
        return "-" in filename and filename.endswith(".txt")

    def load(self):
        """Loads all places specified in the data.
        """
        self.load_levels()
        self.load_dir(self.root)

    def load_levels(self):
        """Loads the levels from level.txt file.
        """
        path = os.path.join(self.root, "level.txt")
        for i, line in enumerate(open(path)):
            short_name, name = line.strip().split(None, 1)
            t = PlaceType.query.filter_by(short_name=short_name).first()
            if not t:
                t = PlaceType(name=name, short_name=short_name, level=i)
            elif t.level != i or t.name != name:
                t.level = i
                t.name = name
            db.session.add(t)
        db.session.commit()

    def load_dir(self, dir):
        """Loads all files from the given dir.
        """
        logger.info("loading dir %s", dir)

        files = sorted(f for f in os.listdir(dir) if self.is_valid_file(f))
        for f in files:
            self.load_file(os.path.join(dir, f))

        dirs = sorted(f for f in os.listdir(dir) if os.path.isdir(os.path.join(dir, f)))
        for d in dirs:
            self.load_dir(os.path.join(dir, d))

    def find_place_type(self, path):
        """Finds place type from path.
        """
        basename = os.path.basename(path)
        m = re.match("\d+-(.*).txt", basename)
        if m:
            short_name = m.group(1).upper()
            return PlaceType.get(short_name)

    def group(self, it, n):
        def take(it, n):
            return list(it.next() for i in range(n))
        it = iter(it)            
        while True:
            x = take(it, n)
            if not x:
                break
            yield x

    def get_places(self, keys):
        places = Place.query.filter(Place.key.in_(keys)).all()
        return dict((p.key, p) for p in places)

    def read_file(self, path):
        for line in open(path):
            # ignore comment and empty lines
            if line.startswith("#") or not line.strip():
                continue
            parent_key, key, name = line.strip().split(None, 2)
            yield parent_key, key, name

    def load_file(self, path):
        logger.info("load_file %s", path)
        self.place_cache.clear()
        place_type = self.find_place_type(path)

        for rows in self.group(self.read_file(path), 1000):
            self.load_places(place_type, rows)

    def load_places(self, place_type, rows):
        parent_keys = set(row[0] for row in rows)
        parents = self.get_places(parent_keys)
        places = self.get_places([row[1] for row in rows])

        for parent_key, key, name in rows:
            if parent_key == "-":
                parent = None
            else:
                parent = parents[parent_key]
            place = places.get(key)
            if place:
                logger.info("updating %r %r - %r", place_type.short_name, key, name)
                if place.name != name:
                    place.name = name
            else:
                logger.info("adding %r %r - %r", place_type.short_name, key, name)
                place = Place(key=key, name=name, type=place_type)
            db.session.add(place)
            if parent:
                parent.add_place(place)
        db.session.commit()

    def get_parent_place(self, key):
        if key == "-":
            return None
        if key not in self.place_cache:
            place = Place.find(key=key)
            if place is None:
                raise ValueError("Place not found: %s", key)
            self.place_cache[key] = place
        return self.place_cache[key]

    def load_place(self, place_type, parent_key, key, name):
        logger.info("adding %r %r - %r", place_type.short_name, key, name)
        sys.stdout.flush()
        parent = self.get_parent_place(parent_key)
        place = Place.find(key=key)
        if not place:
            place = Place(key=key, name=name, type=place_type)
        else:
            if place.name != name:
                place.name = name
        db.session.add(place)
        if parent:
            parent.add_place(place)

def create_place_types():
    def ensure_place_type(name, short_name, level):
        t = PlaceType.query.filter_by(short_name=short_name).first()
        if not t:
            print "adding", name, short_name, level
            t = PlaceType(name=name, short_name=short_name, level=level)
            db.session.add(t)

    ensure_place_type('Country', 'COUNTRY', 10)
    ensure_place_type('Region', 'REGION', 20)
    ensure_place_type('State', 'STATE', 30)
    ensure_place_type('Zone', 'ZONE', 40)
    ensure_place_type('District', 'DT', 50)
    ensure_place_type('Assembly Constituency', 'AC', 60)
    ensure_place_type('Ward', 'WARD', 70)
    ensure_place_type('Polling Center', 'PC', 80)
    ensure_place_type('Polling Booth', 'PB', 90)
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

cache = {}
def find_place(key):
    """Cached implementation of Place.find.
    """
    if key not in cache:
        cache[key] = Place.find(key)
    return cache[key]

def load_state(root_dir):
    path = os.path.join(root_dir, "state.json")
    d = json.loads(open(path).read())
    state = ensure_place(key=d['key'], name=d['name'], type=PlaceType.get("STATE"))

    for code, name in read_tsv(os.path.join(root_dir, "lc.txt")):
        key = "{}/{}".format(d['key'], code)
        name = "{} - {}".format(code, name)
        ensure_place(key=key, name=name, type=PlaceType.get("LC"), parent=state)
    db.session.commit()

    i = 0
    for lc_code, ac_code, ac_name in read_tsv(os.path.join(root_dir, "ac.txt")):
        lc_key = "{}/{}".format(d['key'], lc_code)
        lc = find_place(lc_key)
        ac_key = "{}/{}".format(d['key'], ac_code)
        ac_name = "{} - {}".format(ac_code, ac_name)
        ensure_place(key=ac_key, name=ac_name, type=PlaceType.get("AC"), parent=lc)
        if i and i % 100 == 0:
            db.session.commit()
        i += 1
            
    db.session.commit()

    i = 0
    for ac_code, pb_code, pb_name in read_tsv(os.path.join(root_dir, "pb.txt")):
        ac_key = "{}/{}".format(d['key'], ac_code)
        ac = find_place(ac_key)
        pb_key = "{}/{}".format(ac_key, pb_code)
        pb_name = "{} - {}".format(pb_code, pb_name)
        ensure_place(key=pb_key, name=pb_name, type=PlaceType.get("PB"), parent=ac)
        if i and i % 100 == 0:
            db.session.commit()
        i += 1
    db.session.commit()

def add_member(place_key, name, email, phone):
    place = find_place(place_key)
    if not place:
        print >> sys.stderr, "Unable to find place with key:", repr(place_key)
        sys.exit(1)

    place.add_member(name, email, phone)
    db.session.commit()

def main(root_dir):
    FORMAT = "%(asctime)-15s [%(levelname)s] %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT)

    db.create_all()
    loader = Loader(root_dir)
    loader.load()

if __name__ == '__main__':
    main(sys.argv[1])
