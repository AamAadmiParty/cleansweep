Cleansweep
==========

[![Build Status](https://travis-ci.org/anandology/cleansweep.svg?branch=master)](https://travis-ci.org/anandology/cleansweep)

Requirements
------------

A Linux (or Mac OS X) node with the following software installed. Ubuntu 14.04 is preferred.

* PostgreSQL 9.3 database server
* Python 2.7
* Git
* python virtualenv

Installing them on Ubuntu/Debian:

    $ sudo apt-get install postgresql-9.3 postgresql-server-dev-9.3 python-dev python-virtualenv git


How to Setup
------------

* Clone the repository

        $ git clone https://github.com/anandology/cleansweep.git
        $ cd cleansweep

* setup virtualenv

        $ virtualenv . 

* activate the virtualenv

        $ source bin/activate

* Install dependent python packages

        $ pip install -r requirements.txt

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

Getting Started with Development
--------------------------------

Look at the [helloworld][] module to learn about how to a component in cleansweep works.

[helloworld]: https://github.com/anandology/cleansweep/tree/master/cleansweep/helloworld

LICENSE
-------

This software is licensed under AGPLv3.

