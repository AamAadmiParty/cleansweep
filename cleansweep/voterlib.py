import requests
import re

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
            return data['response']['docs'][0]
        except (KeyError, IndexError):
            pass

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
    import sys
    print get_voter_info(sys.argv[1])