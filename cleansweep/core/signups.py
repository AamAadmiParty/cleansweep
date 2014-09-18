"""Volunteer signup process.
"""
from ..models import db, Place, PendingMember
from ..voterlib import voterdb

def resolve_voterid(voterid):
    """Takes a voterid and returns a place object.
    """
    voter_info = voterdb.get_voter(voterid=voterid)
    return voter_info and voter_info.get_place()

def signup(name, email, phone, voterid, place_key=None):
    place = resolve_voterid(voterid)
    if not place:
        place = Place.find(place_key)
    pending_member = PendingMember(
        place=place, 
        name=name,
        email=email,
        phone=phone,
        voterid=voterid)
    db.session.add(pending_member)
    db.session.commit()
    return pending_member