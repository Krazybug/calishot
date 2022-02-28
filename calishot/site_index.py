import requests
from pathlib import Path
from urllib.parse import *
import uuid
from sqlite_utils import Database
import datetime


import gevent
from gevent import monkey
from gevent import Timeout
from gevent.pool import Pool
monkey.patch_socket()


def init_sites_db(dir="."):
    
    path = Path(dir) / "sites.db" 

    db = Database(path)
    if not "sites" in db.table_names():
        db["sites"].create({
        "uuid": str,
        "url": str,
        "hostnames": str,
        "ports": str,
        "country": int,
        "isp": str,
        "status": str,
        "last_online": str,
        "last_check": str,
        "error": int,
    #     "schema_version": 1
    #     # TODO: add the most common formats
        }, pk="uuid")
        # }, pk="uuid", not_null=True)

    # if not "sites" in db.table_names():
    #     db["sites"].create({
    #     "uuid": str
    #     }, pk="uuid",)

    db.table("sites", pk='uuid', batch_size=100, alter=True)
    return db


def save_site(db: Database, site):
    # # TODO: Check if the site is not alreday present
    # def save_sites(db, sites):
    #     db["sites"].insert_all(sites, alter=True,  batch_size=100)
    if not 'uuid' in site: 
        site['uuid']=str(uuid.uuid4())    
    print(site)
    db["sites"].upsert(site, pk='uuid')


def check_and_save_site(db, site):
        res= check_calibre_site(site)
        print(res)
        save_site(db, res)

# import pysnooper
# @pysnooper.snoop()
def check_calibre_site(site):
    ret={}
    ret['uuid']=site["uuid"]
    now=str(datetime.datetime.now())
    ret['last_check']=now 

    api=site['url']+'/ajax/'
    timeout=15
    library=""
    url=api+'search'+library+'?num=0'
    print()
    print("Getting ebooks count:", site['url'])
    print(url)
    
    try:
        r=requests.get(url, verify=False, timeout=(timeout, 30))
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        r.status_code
        ret['error']=r.status_code
        if (r.status_code == 401):
            ret['status']="unauthorized"
        else:
            ret['status']="down"
        return ret
    except requests.RequestException as e: 
        print("Unable to open site:", url)
        # print (getattr(e, 'message', repr(e)))
        print (e)
        ret['status']="down"
        return ret
    except Exception as e:
        print ("Other issue:", e)
        ret['status']='Unknown Error'
        print (e)
        return ret
    except :
        print("Wazza !!!!")
        ret['status']='Critical Error'
        print (e)
        return ret

    try: 
        print("Total count=",r.json()["total_num"])
    except:
        pass

    status=ret['status']='online'
    if status=="online":
        ret['last_online']=now 

    return ret



def get_site_uuid_from_url(db, url):

    site=urlparse(url)
    hostname=site.hostname
    site=site._replace(path='')
    
    url=urlunparse(site)
    # print (url)

    # print (hostname)
    row=db.conn.execute(f"select * from sites where instr(hostnames, '{hostname}')").fetchone()
    # print(row)
    if row:
        return row

def map_site_from_url(url):
    ret={}

    site=urlparse(url)

    print(site)
    site=site._replace(path='')
    ret['url']=urlunparse(site)
    ret['hostnames']=[site.hostname] 
    ret['ports']=[str(site.port)]

    return ret


def import_urls_from_file(filepath, dir='.'):

    #TODO skip malformed urls
    #TODO use cache instead

    db=init_sites_db(dir)

    with open(filepath) as f:
        for url in f.readlines():
            url=url.rstrip()
            # url='http://'+url
            if get_site_uuid_from_url(db, url):
                print(f"'{url}'' already present")
                continue
            print(f"'{url}'' added")
            save_site(db, map_site_from_url(url))
    


def get_libs_from_site(site):

    server=site.rstrip('/')
    api=server+'/ajax/'
    timeout=30
    
    print()
    print("Server:", server)
    url=api+'library-info'

    print()
    print("Getting libraries from", server)
    # print(url)

    try:
        r=requests.get(url, verify=False, timeout=(timeout, 30))
        r.raise_for_status()
    except requests.RequestException as e: 
        print("Unable to open site:", url)
        # return
    except Exception as e:
        print ("Other issue:", e)
        return
        # pass

    libraries = r.json()["library_map"].keys()
    print("Libraries:", ", ".join(libraries))
    return libraries

def check_calibre_list(dir='.'):    
    db=init_sites_db(dir)
    sites=[]
    for row in db["sites"].rows:
        print(f"Queueing:{row['url']}")
        sites.append(row)
    print(sites)
    pool = Pool(100)
    pool.map(lambda s: check_and_save_site (db, s), sites)

# example of a fts search sqlite-utils index.db "select * from summary_fts where summary_fts  match 'title:fre*'"