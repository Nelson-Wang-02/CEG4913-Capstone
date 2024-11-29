#imports
import os
import glob
from Website import init_application

snapshots_folder = os.path.join(os.getcwd(),'Website','static', 'Snapshots')

files=  glob.glob(snapshots_folder+"/*") #cleanse the snapshots folder. 
print(f"removing {len(files)} snapshots.")

try:
    for f in files:
        os.remove(f)
except Exception as e:
    print(f"Failed to remove the lingering snapshots. Please remove them manually.{e}")

web_app = init_application()
if __name__ == '__main__':
    web_app.run(debug=True)