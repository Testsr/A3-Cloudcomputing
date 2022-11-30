import psycopg
import csv
import httpx
#dynamodb = boto3.resource('dynamodb',region_name='us-east-1')
#table = dynamodb.Table('stocks')
url = "https://www.asx.com.au/asx/research/ASXListedCompanies.csv"
r=httpx.get(url)
r.raise_for_status()
with open('ASXListedCompanies.csv', 'wb') as f:
    f.write(r.content)
with psycopg.connect("postgresql://postgres:CmXKfwocyDjBI7VIM2ub@datastore-asx.cygdlm2jaqpj"
                     ".us-east-1.rds.amazonaws.com:5432/postgres") as conn:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE asx_stocks")
        with open('ASXListedCompanies.csv') as csvfile:
            csvfile.readline()
            csvfile.readline()
            reader=csv.DictReader(csvfile)
            with cur.copy("COPY asx_stocks (stock_code, stock_name) FROM STDIN") as copy:
                for row in reader:
                    copy.write_row((row["ASX code"], row["Company name"]))



