"""Script to run the web app and load data.

To run the webapp:

    python run.py

To load data:

    python run.py --load data/KA
"""
import sys

if __name__ == "__main__":
    if "--help" in sys.argv:
        print __doc__
    elif "--load" in sys.argv:
        from cleansweep.loaddata import main
        root_dir = sys.argv[1+sys.argv.index("--load")]
        main(root_dir)
    else:
        from cleansweep.main import main
        main()
