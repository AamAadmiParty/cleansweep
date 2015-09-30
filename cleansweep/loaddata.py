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
import logging
from .models import db, Place, PlaceType, Member

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
            line = line.decode('utf-8')
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
                if place.iparent != parent:
                    logger.info("updating parent of %s to %s", key, parent.key)
                    parent.add_place(place)
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

cache = {}
def find_place(key):
    """Cached implementation of Place.find.
    """
    if key not in cache:
        cache[key] = Place.find(key)
    return cache[key]

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

def main_loadfiles(filenames):
    FORMAT = "%(asctime)-15s [%(levelname)s] %(message)s"
    logging.basicConfig(level=logging.INFO, format=FORMAT)

    db.create_all()
    loader = Loader(None)
    for f in filenames:
        loader.load_file(f)

def xinput(prompt, pattern=None):
    while True:
        value = raw_input(prompt + ": ")
        value = value.strip()
        if not value:
            continue
        if pattern and not re.match(pattern, value):
            print "Invalid ", prompt.lower()
            continue
        return value

def read_user_info():
    print "\nPlease enter your details to add you as an admin.\n"
    name = xinput("Your Name")
    email = xinput("E-mail address", "[a-zA-Z0-9_.-]+@[a-zA-Z0-9_.-]+")
    phone = xinput("Phone number (10 digits)", "^[0-9]+$")
    return name, email, phone

def update_parents(key):
    """Updates parents of all places below the specified key.

    This is used when parents are not in sync for whatever reason.
    This is really a quick fix rather than a utility.
    """
    place = Place.find(key=key)
    place.update_parents_of_all_children()
    db.session.commit()

def init():
    # create database tables
    db.create_all()

    print "=" * 20

    # load places
    print "loading places..."
    Loader("data").load()

    # read user data and add him as member
    name, email, phone = read_user_info()


    if Member.find(email=email):
        print "{} is already added as volunteer.".format(email)
    else:
        add_member("DL/AC061/PB0001", name, email, phone)

    with open("config/development.cfg", "w") as f:
        f.write('ADMIN_USERS = ["{}"]'.format(email))

    print "\nDONE!\n"
    print "{} have been setup as admin".format(email)
    print
    print "Run the app using:"
    print "python run.py"
    print
    print "The website will be accessible at http://localhost:5000/"

if __name__ == '__main__':
    main(sys.argv[1])
