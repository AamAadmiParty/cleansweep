Cleansweep
==========

[![Build Status](https://travis-ci.org/anandology/cleansweep.svg?branch=master)](https://travis-ci.org/anandology/cleansweep)

Requirements
------------

* PostgreSQL 9.3 database server
* Python 2.7

Preferably a UNIX box (Linux/Mac OS X). 

How to Setup
------------

* Clone the repository

        $ git clone https://github.com/anandology/cleansweep.git
        $ cd cleansweep

* setup virtualenv

        $ virtualenv . 
        $ pip install -r requirements.txt

* activate the virtualenv

        $ source bin/activate

* Init the app by adding you as admin. It'll prompt you for your name, email 
  and phone number.

        $ python run.py --init
        ...
        Your Name: ______
        E-mail address: ______
        Phone: ______
    
* run the webapp

        python run.py

Visit the website at:
<http://localhost:5000/>

LICENSE
-------

This software is licensed under AGPLv3.

