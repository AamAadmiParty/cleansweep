from .app import app
from .models import db

# load all helpers
from . import helpers

# load all the views 
from . import views

def main():
    db.create_all()
    app.run()

if __name__ == '__main__':
    main()