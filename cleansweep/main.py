from .app import app
from .models import db

# load all helpers
from . import helpers

# load all the views 
from . import views

def main(port=5000):
    db.create_all()
    app.run(port=port)

if __name__ == '__main__':
    main()