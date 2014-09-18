import requests
import re
import sys
from .models import Place, PlaceType


# Regular expression for converting AC012 to 12
RE_NOTNUM_PREFIX = re.compile("^[A-Z]*0*")


class Voter(object):
    def __init__(self, data):
        self.data = data
        self.voterid = self.data['voterid']
        self.name = self.data['name']
        self.address = self.data.get('address')

    def __getitem__(self, key):
        return self.data[key]

    def get_place_key(self):
        return "{}/AC{:0>3}/PB{:0>4}".format(self['state'], self['ac'], self['pb'])

    def get_place(self):
        return Place.find(key=self.get_place_key())

    def __repr__(self):
        return "<voter:{}@{}/AC{:0>3}/PB{:0>4}>".format(
            self['voterid'], self['state'], self['ac'], self['pb'])

class VoterDB:
    def __init__(self, base_url=None):
        self.base_url = base_url

    def init_app(self, app):
        self.base_url = app.config['VOTERDB_URL']

    def _get(self, path, **params):
        if self.base_url is None:
            return []
        url = self.base_url.rstrip("/") + "/" + path
        return requests.get(url, params=params).json()

    def get_voter(self, voterid):
        """Returns details of the voter with given voterid.
        """
        result = self._get("voters", voterid=voterid)
        if result:
            return Voter(result[0])

    def tonum(self, value):
        return RE_NOTNUM_PREFIX.sub("", value)

    def get_voters(self, place, offset=0, limit=100):
        """Returns details of all voters from the given place.
        """
        STATE = PlaceType.get("STATE")
        AC = PlaceType.get("AC")
        PB = PlaceType.get("PB")

        if place.type > STATE:
            places = place.get_places(type=STATE)
            states = ",".join(p.code for p in places)
            data = self._get("voters", state=states, offset=offset, limit=limit)
        elif place.type == STATE:
            data = self._get("voters/" + place.code)
        elif place.type > AC:
            state = place.get_parent(STATE).code
            places = place.get_places(type=AC)
            ac = ",".join(self.tonum(p.code) for p in places)
            data = self._get("voters/" + state, ac=ac, offset=offset, limit=limit)
        elif place.type == AC:
            state = place.get_parent(STATE).code
            data = self._get("voters/{}/{}".format(state, self.tonum(place.code)), offset=offset, limit=limit)
        elif place.type > PB:
            state = place.get_parent(STATE).code
            ac = place.get_parent(AC).code
            places = place.get_places(type=PB)
            pb = ",".join(self.tonum(p.code) for p in places)
            data = self._get("voters/{}/{}".format(state, ac), pb=pb, offset=offset, limit=limit)
        else:
            state = place.get_parent(STATE).code
            ac = place.get_parent(AC).code
            data = self._get("voters/{}/{}/{}".format(state, self.tonum(ac), self.tonum(place.code)), offset=offset, limit=limit)
        return [Voter(d) for d in data]

voterdb = VoterDB()

BASE_URL = "http://electoralsearch.in/"

def get_voter_info(voterid):
    """Returns details about the voter with given voterid.

    Makes a search on http://electoralsearch.in/ with that voterid and
    results the response.
    """
    # create a session so that the cookies are retained b/w requests
    s = requests.session()

    # open the home page
    r = s.get(BASE_URL)

    # extract the token hidden in javascript
    token = get_token(r.text)

    # prepare search parameters
    params = {
        'epic_no': voterid,
        'page_no': '1',
        'results_per_page': 5,
        'reureureired': token,
        'search_type': 'epic'
    }

    # The electoralsearch website refuses to give results if it Referer
    # header is not set. 
    headers = {"Referer": BASE_URL}

    # Make the search request
    r = s.get(BASE_URL + "Search", params=params, headers=headers)

    # and read json from it
    data = r.json()
    if data:
        # return the first matching record
        try:
            return _process_voter_info(data['response']['docs'][0])
        except (KeyError, IndexError):
            pass

re_voter_info_id = re.compile("^S(\d\d)(\d\d\d)(\d\d\d\d)\d\d(\d\d\d\d)$")
def _process_voter_info(d):
    """Process the voter info suitable for use in cleansweep.
    """
    m = re_voter_info_id.match(d['id'])
    if m:
        d['state_code'] = m.group(1)
        d['ac_code'] = m.group(2)
        d['pb_code'] = m.group(3)
        d['serial'] = m.group(4)
        return d

re_token = re.compile("function _aquire\(\) *{ *return '([0-9a-f-]+)';")
def get_token(text):
    """The extracts the token burried in some javascript.

    The electoralsearch website keeps a UUID in a javascript function and 
    that is required for searching for voterid. This function extracts that
    using regular expressions.
    """
    text = " ".join(text.splitlines())
    m = re_token.search(text)
    return m and m.group(1)

if __name__ == "__main__":
    import sys, json
    d = get_voter_info(sys.argv[1])
    print json.dumps(d, indent=True)
    