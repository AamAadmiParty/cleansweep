"""
A helper class to lookup voter by voter id
"""
import requests


def get_voter(voterid):
    """
    Gets voter details from our API using the voter id provided
    :param voterid: The voter id
    :return: JSON object with contains 'state', 'pb', 'ac' and 'voterid'
    """
    payload = {'voterid': voterid}
    resp = requests.get("http://voter-lookup.missionvistaar.in/search", params=payload)
    voter_data = resp.json()
    if voter_data:
        return voter_data[0]


def voterid_valid(voterid):
    """
    Just a more readable function to check if voter id is valid or not at the time of registration.
    """
    return get_voter(voterid)
