import os
import sys
import json
from pathlib import Path
from sqlite_utils import Database
from humanize import naturalsize as hsize

from calistat import get_desc_url, get_format_url


def init_index_db(dir="."):
    
    path = Path(dir) / "index.db" 
    
    db_index = Database(path)
    if not "summary" in db_index.table_names():
        db_index["summary"].create({
        "uuid": str,
        "cover": str,
        "title": str,
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
        "formats": str
        }
        # )
        , pk="uuid")

        # db_index.table("index", pk="uuid")
        # db_index.table("summary").enable_fts(["title"])
        # db_index["summary"].enable_fts(["title", "authors", "series", "uuid", "language", "identifiers", "tags", "publisher", "formats", "pubdate"])
        db_index["summary"].enable_fts(["title", "authors", "series", "language", "identifiers", "tags", "publisher", "formats", "year"])

    return db_index


def get_img_url(db, book):
    url = json.loads(list(db['site'].rows)[0]["urls"])[0]

    library=book['library']
    id_=str(book['id'])

    f_urls=[]

    major=  list(db['site'].rows)[0]["major"]

    if major >= 3:
        d_url =url+"/get/thumb/"+id_+"/"+library+ "?sz=600x800"
    else:
        # d_url =url+"/get/thumb/"+id_
        d_url =url+"/get/thumb_90_120/"+id_

    return d_url


def build_index (dir='.', english=True):

    dbs=[]
    for f in os.listdir(dir):
        if not f.endswith(".db"):
            continue
        if f in ("index.db", "sites.db"):
            continue
        p = Path(dir) / f 
        print(f)
        try:
            db = Database(p.resolve())
        except:
            print ("Pb with:", f)
        dbs.append(db)
    
    db_index = init_index_db(dir=dir)
    index_t=db_index["summary"]

    batch_size=10000
    count=0
    summaries=[]

    for db in dbs:
        for i, ebook in enumerate(db["ebooks"].rows):
            if english and (not ebook['language'] or ebook['language'] != "eng"):
                continue
            elif not english and ebook['language'] == "eng":
                continue
            
            
            if ebook['authors']: 
                ebook['authors']=formats=json.loads(ebook['authors'])
            # if ebook['series']:    
            #     ebook['series']=formats=json.loads(ebook['series'])
            if ebook['identifiers']:
                ebook['identifiers']=formats=json.loads(ebook['identifiers'])
            if ebook['tags']: 
                ebook['tags']=formats=json.loads(ebook['tags'])
            ebook['formats']=formats=json.loads(ebook['formats'])
            ebook['links']=""
            summary = {k: v for k, v in ebook.items() if k in ("uuid","title", "authors", "series", "language", "formats", "tags", "publisher", "identifiers")}
            # summary = {k: v for k, v in ebook.items() if k in ("uuid","title", "authors", "series", "identifiers", "language", "tags", "publisher", "formats")}
            summary['title']={'href': get_desc_url(db, ebook), 'label': ebook['title']}

            summary["cover"]= {"img_src": get_img_url(db, ebook), "width": 90}

            formats=[]
            for f in ebook['formats']:
                formats.append({'href': get_format_url(db, ebook, f), 'label': f"{f} ({hsize(ebook[f])})"})
            summary['links']=formats
            
            pubdate=ebook['pubdate'] 
            summary['year']=pubdate[0:4] if pubdate else "" 
            summaries.append(summary)
            # print(summary)
            count+=1
            print (f"\r{count} - ebook handled: {ebook['uuid']}", end='')

            if not count % batch_size:
                # print()
                # print(f"Saving summary by batch: {len(summaries)}")    
                # print(summaries)
                # index_t.upsert_all(summaries, batch_size=1000, pk='uuid')
                # index_t.insert_all(summaries, batch_size=1000, pk='uuid')
                try:
                    index_t.insert_all(summaries, batch_size=batch_size)
                except Exception as e:
                    # dump = [(s['uuid'],s['links']) for s in summaries]
                    # print(dump)
                    print()
                    print("UUID collisions. Probalbly a site duplicate")
                    print(e)
                    print()

                    # index_t.upsert_all(summaries, batch_size=batch_size, pk='uuid')
                    # TODO Some ebooks could be missed. We need to compute the batch list, insert new ebooks and update the site index

                # print("Saved")
                # print()
                summaries=[]

    # print()
    # print("saving summary")    
    # index_t.upsert_all(summaries, batch_size=1000, pk='uuid')
    # index_t.insert_all(summaries, batch_size=1000, pk='uuid')
    try:
        index_t.insert_all(summaries, batch_size=batch_size)
    except:
        print("sqlite3.IntegrityError: UNIQUE constraint failed: summary.uuid")

    # print("summary done")
    # print()
    
    print()
    print("fts")
    index_t.populate_fts(["title", "authors", "series", "identifiers", "language", "tags", "publisher", "formats", "year"])
    print("fts done")


def search(query_str, dir=".", links_only=False):
    path = Path(dir) / "index.db" 
    db_index = Database(path)
    # table=db_index["summary"]
    # rows=table.search(query_str)
    # print(rows)
    sites=set()
    ebook_ids=[]
    for ebook in db_index["summary"].search(query_str):
        sites.add(ebook[-1])
        ebook_ids.append((ebook[3], ebook[-1]))
        # print (ebook)
    # print("sites:", sites) 
    # print("ebooks:", ebook_ids) 

    site_dbs={}
    for s in sites:
        f_uuid=s+".db"
        path = Path(dir) / f_uuid 
        site_dbs[s]=Database(path)
        # print(site_dbs[s].tables)
    
    for e in ebook_ids:
        # ebook=site_dbs[e[1]]["ebooks"].get(e[0])
        # print("ebook:", ebook)
        db=site_dbs[e[1]] 
        # ebooks=db.conn.execute("select * from ebooks").fetchone()
        ebook=db.conn.execute(f'select * from ebooks where uuid="{e[0]}"').fetchone()
        url=json.loads(db['site'].get(1)['urls'])[0]
        library=db['site'].get(1)['library']
        formats=json.loads(ebook[14])
        id_=str(ebook[0])

        if not links_only:
            print()
            print("Title:", ebook[2])
            print("Author:", ebook[3])
            print("Serie:", ebook[4])
            print("Formats:", formats)

        for f in formats:
            print(url+"get/"+f+"/"+id_+"/"+library)


# https://stackoverflow.com/questions/26692284/how-to-prevent-brokenpipeerror-when-doing-a-flush-in-python

def index_to_json(dir='.'):
    path = Path(dir) / "index.db" 
    db = Database(path)

    # sys.stdout.flush()

    try: 
        for row in db["summary"].rows:
            if row['title']:
                row['title']=json.loads(row['title'])
            if row['authors']:
                row['authors']=json.loads(row['authors'])
            if row['series']:
                row['series']=json.loads(row['series']) 
            if row['links']:
                row['links']=json.loads(row['links'])
            if row['tags']:
                row['tags']=json.loads(row['tags'])
            if row['identifiers']:
                row['identifiers']=json.loads(row['identifiers'])
            if row['formats']:
                row['formats']=json.loads(row['formats'])

            json.dump(row, sys.stdout)
            sys.stdout.flush()
            # return
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1) 
