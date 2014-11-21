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

        git clone https://github.com/anandology/cleansweep.git
        cd cleansweep

* setup virtualenv

        virtualenv . 
        pip install -r requirements.txt

* activate the virtualenv

        source bin/activate

* load data

        python run.py --load data

* Add yourself as a volunteer
        
        python run.py --add-member DL/AC061/PB0001 "Your Name" email@domain.com  1234567890

    Change the last 3 arguments with your name, email and phone number.

* Add yourself as admin by creating a production.cfg file with the following contents.

        # replace email@domain.com with your email address
        ADMIN_USERS = ["email@domain.com"]

* run the webapp

        python run.py

Visit the website at:
<http://localhost:5000/>

LICENSE
-------

This software is licensed under AGPLv3.

