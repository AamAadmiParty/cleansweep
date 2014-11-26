"""helloworld component of cleansweep.

The purpose of this module is to demonstrate how components work in cleansweep and how to write a new one.
"""

# The init_app function is the entry point for a component. 
# By convention, it is defined in views.py and imported here.
from .views import init_app