"""Role Based Access Control for Cleansweep.

This library provides a generic framwork for implementing role based access control.
It provides core functionality of RBAC, while leaving it to the application to provide
how roles and permssions are stored.

Hooks are provided for the application to specify how to compute roles of a user
and available permissions of given roles.

NOTE: This may later be moved into an independent library with a more liberal license.
"""

import functools
import collections

_role_providers = []
_permisison_providers = []

def _reset():
    """Resets all the global permisison state.

    Used for resetting the state before running each test case.
    """
    global _role_providers, _permisison_providers
    _role_providers = []
    _permisison_providers = []
    MetaPermission.permission_tree.clear()
    MetaPermission.permission_mapping.clear()


def role_provider(func):
    """Decorator to register a role provider.

    Every role provider function takes the user as argument and returns the
    list of roles that person has according to the component where the function
    is written. There could be multiple role providers and the roles of a person
    are computed by combining all these roles.

    Role is represented as a dictionary. For example:

        {"place": "DL/AC001", "role": "volunteer"}
        {"place": "DL/AC001", "role": "Incharge", "committee": "AC-Committee"}
    """
    _role_providers.append(func)
    return func


def permission_provider(func):
    """Decorator to register a permission provider function.

    The permission provier function takes a role as agument and returns
    the permissions he has according to it's knowledge. There could be
    multiple permission provider functions, each provided by different
    compoents.

    The permissions of a user are computed by comibing all the permssions
    returned by the permission prodiver functions.

    Permission is represented by a dictionary. For example:

        {"place": "DL/AC001", "permission": "send-sms"}
        {"place": "DL/AC001", "permission": "all"}
    """
    _permisison_providers.append(func)
    return func


def get_user_roles(user):
    """Returns all roles of a user.
    """
    roles = []
    for func in _role_providers:
        some_roles = func(user)
        roles.extend(some_roles)
    return roles


def get_user_permissions(user):
    """Returns all permissions of given user.
    """
    roles = get_user_roles(user)
    permissions = []

    for func in _permisison_providers:
        for role in roles:
            some_perms = func(role)
            permissions.extend(some_perms)

    return permissions


def match_permission(perm, action):
    """Checks if the given permission matches the specified action.
    """
    # TODO: Handle child permissions
    return perm['permission'] == action


def can(user, action, resource):
    """Tells if the given user can perform the specified action on a resource.

    Currently the resource can only be a place. In future, other types of
    resources may be considered for more fine-grained control.

    @param user: user object
    @param action: action to perform, string
    @param resource: place object at which the action is being tried
    """
    place = resource
    # place and all parents of the place
    place_keys = [place.key] + [p.key for p in place.parents]

    # empty string is used to indicate any place
    place_keys.append("")

    perms = get_user_permissions(user)
    return any(match_permission(p, action)
                for p in perms
                if p['place'] in place_keys)

