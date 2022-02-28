# CALISHOT Guidelines

## Installation

You need poetry pre installed.
Clone the repository then :


```
poetry install
poetry shell
mkdir output
cd output 
```
Then create a list.txt file with all your calibre urls

## Indexing

```
python ../calishot import list.txt

python ../calishot check

sqlite-utils sites.db 'select url from sites where status="online" ' | jq -r '.[].url' > online.txt

python ../calishot index-site-list online.txt

python ../calishot build-index --english  
mv index.db index-eng.db

python ../calishot build-index --noenglish  
mv index.db index-non-eng.db

# for diplaying global size and total count of formats
python ../calishot get-stats  

python ../calishot index-to-json | jq -r '.  | {title: .title.label, authors, year, language, publisher, series, desc: .title.href, tags, identifiers, formats, format_links: [.links[].href]}' > calibre.json

sqlite-utils index.db 'select uuid, title, authors, year, series, language, formats, publisher, tags, identifiers from summary where instr(formats, "mp3") >0  order by uuid limit 101'



```
## Deployment

1. Install poetry, datasette and it's plugins

```
poetry new calishot
poetry shell
poetry add datasette
poetry add datasette-json-html
poetry add datasette-pretty-json
```

You can eventually install it with virtualenv/pip if you don't want to use poetry: 

```
python -m venv calishot
. ./calishot/bin/activate
pip install datasette
pip install datasette-json-html
pip install datasette-pretty-json
````


2. Prepare the calishot settings:

Download the sqlite db file to the same directory and then


```
cat <<EOF > metadata.json 
{
    "databases": {
      "index": {
        "tables": {
            "summary": {
                "sort": "title",
                "searchmode": "raw"
            }
        }
      }
    }
  }
EOF
```

You can now run a local test:

```
datasette serve index-non-eng.db --config sql_time_limit_ms:50000 --config allow_download:off --config max_returned_rows:2000  --config num_sql_threads:10 --config allow_csv_stream:off  --metadata metadata.json
```

Open your browser to http://localhost:8001/ and check the result.

3. Now you're ready to publish :)

Install [heroku-cli](https://devcenter.heroku.com/articles/heroku-cli) then :

export NODE_EXTRA_CA_CERTS=<your_dir>/calishot/CAall.cer 

```
heroku login -i


datasette publish heroku index-non-eng.db -n calishot-non-eng-1 --install=datasette-json-html --install=datasette-pretty-json --extra-options="--config sql_time_limit_ms:50000 --config allow_download:off --config num_sql_threads:10 --config max_returned_rows:500 --config allow_csv_stream:off" --metadata metadata.json
```
