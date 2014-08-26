"""Volunteer signup process.
"""
from ..voterlib import get_voter_info
from ..models import db, Place, PendingMember

def resolve_voterid(voterid):
    """Takes a voterid and returns a place object.
    """
    if not voterid:
        return None
    
    info = get_voter_info(voterid)
    if 'pb_key' in info:
        return Place.find(key=info['pb_key'])

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