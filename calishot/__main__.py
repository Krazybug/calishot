import fire

from site_index import import_urls_from_file, check_calibre_list, check_calibre_site
from calistat import index_site_list, get_stats, index_site_list_seq  
from ebooks_index import build_index, index_to_json  
from  diff import diff

if __name__ == "__main__":
    fire.Fire({
        "import": import_urls_from_file,
        "check":check_calibre_list,
        "check-site":check_calibre_site,
        "index-site-list": index_site_list,
        "index-site-list-seq": index_site_list_seq,
        "build-index": build_index, 
        "get-stats": get_stats,
        "index-to-json": index_to_json,  
        "diff": diff
       })
