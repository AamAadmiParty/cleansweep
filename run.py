"""Script to run the web app and load data.

To run the webapp:

    python run.py

To load data:

    python run.py --load data/KA
"""
import sys

# importing app so that it is be used in Procfile (for Heroku)
from cleansweep.main import main, app

if __name__ == "__main__":
    if "--help" in sys.argv:
        print __doc__
    elif "--load" in sys.argv:
        from cleansweep.loaddata import main
        root_dir = sys.argv[1+sys.argv.index("--load")]
        main(root_dir)
    elif "--load-files" in sys.argv:
        from cleansweep.loaddata import main_loadfiles
        sys.argv.remove("--load-files")
        filenames = sys.argv[1:]
        main_loadfiles(filenames)
    elif "--add-member" in sys.argv:
        from cleansweep.loaddata import add_member
        index = sys.argv.index("--add-member")
        place = sys.argv[index+1]
        name = sys.argv[index+2]
        email = sys.argv[index+3]
        phone = sys.argv[index+4]
        add_member(place, name, email, phone)
    elif "--worker" in sys.argv:
        from cleansweep.core.mailer import run_worker
        run_worker()
    elif "--init" in sys.argv:
        from cleansweep.loaddata import init
        init()
    else:
        try:
            port = int(sys.argv[1])
        except IndexError:
            port = 5000
        main(port=port)
