from google.cloud import bigquery
import requests
import json
import logging
import pandas as pd
import csv
from google.cloud import storage

logging.basicConfig(level=logging.DEBUG)

bucket_name = 'facebook_data_task'

access_token = ''

def get_data(access_token):
    """facebook api request"""

    link = 'https://graph.facebook.com/me/posts?access_token={}'.format(access_token)
    r = requests.get(link)
    return json.loads(r.content.decode('utf8'))

def upload_to_bucket(blob_name, path_to_file, bucket_name):
    """ Upload data to a bucket"""

    storage_client = storage.Client()

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(path_to_file)

    #returns a public url
    return blob.public_url

def create_table(client, table_ref):
    """create table in bq"""

    job_config = bigquery.LoadJobConfig()
    job_config.autodetect = True
    job_config.source_format = bigquery.SourceFormat.CSV
    uri = "gs://facebook_data_task/data.csv"
    load_job = client.load_table_from_uri(
        uri, table_ref, job_config=job_config
    )  # API request
    print("Starting job {}".format(load_job.job_id))

    load_job.result()  # Waits for table load to complete.
    print("Job finished.")


def does_table_exist(table_ref):
    try:
        client.get_table(table_ref)
        return True
    except Exception as e:
        return False

def update_bq_table(client, table_ref):
    # Delete existing table with old data
    if does_table_exist(table_ref):
        print('table already exists, deleting table...')
        client.delete_table(table_ref)

    # Create new table with fresh data from google storage
    if not does_table_exist(table_ref):
        print('table deleted, new table creating...')
        create_table(client, table_ref)
        if does_table_exist(table_ref):
            print('table created successful!')
        else:
            raise Exception('Unable to create table!')
    else:
        raise Exception('Unable to delete table!')

def get_facebook_data():

    data = get_data(access_token)['data']
    df = pd.DataFrame(data)
    df['message'] = df['message'].apply(lambda x: x.replace('\n', " ").replace('\'', ''))
    filename = "data.csv"
    blob = filename
    df.to_csv(filename, quoting=csv.QUOTE_NONNUMERIC, index=False)
    upload_to_bucket(blob, filename, bucket_name)

if __name__ == '__main__':

    client = bigquery.Client()
    dataset_id = 'facebook_data'
    table_id = 'facebook_data_table'
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(table_id)

    # Download facebook data and upload to google storage
    get_facebook_data()
    update_bq_table(client, table_ref)












