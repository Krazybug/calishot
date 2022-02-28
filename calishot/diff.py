from pathlib import Path
from sqlite_utils import Database 
from sqlite_utils.db import NotFoundError
import json

def init_diff_db(dir="."):
    
    path = Path(dir) / "diff.db" 
    
    db_diff = Database(path)
    if not "summary" in db_diff.table_names():
        db_diff["summary"].create({
        "uuid": str,
        "title": str,
        # "cover": str,
        # "source": str
        "authors": str,
        "year": str,
        "series": str,
        "language": str,
        "links": str,
        # "desc": str,
        "publisher": str,
        "tags": str,
        "identifiers": str,
        "formats": str,
        "status": str,
        "old_location":str
        }
        # )
        , pk="uuid")

    return db_diff

def diff(old, new, dir=".", ):
    path = Path(dir) / old 
    db_old = Database(path)

    path = Path(dir) /  new 
    db_new = Database(path)

    path = Path(dir) / "diff.db"
    db_diff =init_diff_db(dir)

    for i, n_book in enumerate(db_new["summary"].rows):
        n_uuid = n_book['uuid']
        print(i, n_uuid)
        try:
            o_book = db_old["summary"].get(n_uuid)
            # print(n_uuid, '=OK')
            o_loc=json.loads(o_book['title'])['href']
            n_loc=json.loads(n_book['title'])['href']
            if o_loc != n_loc :
                print(n_uuid, 'MOVED')
                n_book["status"]="MOVED"
                n_book["old_location"]=o_loc
                n_book.pop ('cover', None)
                db_diff["summary"].insert(n_book, pk='uuid')
                                
        except NotFoundError:
            # print(n_uuid, '=NOK')
            n_book.pop ('cover', None)
            n_book["status"]="NEW"
            db_diff["summary"].insert(n_book, pk='uuid')
