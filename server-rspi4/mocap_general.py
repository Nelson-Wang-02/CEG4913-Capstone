
import argparse

class Mocap_General():
    def fetch_arguments(self) -> tuple:
        parser = argparse.ArgumentParser()
        parser.add_argument("--time", help="define the time that camera will be on")
        parser.add_argument("--a", action="store_true", help= "Include to run the unity animator exe")
        parser.add_argument("--delay", help="define the time before camera starts")
        parser.add_argument("--setnum", help= "define the set number within a split", default= None)
        args = parser.parse_args()
        if not args.time:
            time  = 10
        else:
            time = int(args.time)
        if not args.a:
            a = False
        else:
            a = True
        if not args.delay:
            delay = 3 #seconds
        else:
            delay = int(args.delay)
        if not args.setnum:
            setnum = None
        else:
            setnum = int(args.setnum)
        return (time , a, delay, setnum)