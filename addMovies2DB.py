# TODO: Create DB, New Table, Show columns
from pathlib import Path
from requests import get
import mysql.connector
import traceback
import datetime
import json
import os

PostgreSQL = '''
CREATE TABLE api_movie (
id VARCHAR(20) PRIMARY KEY,
imdb_id VARCHAR(10),
title VARCHAR(255),
year VARCHAR(4),
slug VARCHAR(150),
synopsis TEXT,
runtime VARCHAR(4),
country VARCHAR(4),
last_updated NUMERIC(16,1),
released INT,
certification VARCHAR(255),
torrents TEXT,
trailer VARCHAR(255),
genres VARCHAR(255),
images TEXT,
rating VARCHAR(255),
_v SMALLINTadd
);
'''



# Create Databse and Table if it does not exist
def db_tool(cursor, db_name, table_name):
    try:
        cursor.execute(f"CREATE DATABASE {db_name}")
        print(f'Successfully created {db_name} Database!')
    except Exception as e:
        print(
            f'Something went wrong creating the database {db_name}:\n\t{e}')
        # traceback.print_exc()
    cursor.execute(f'use {db_name};')
    sql = f'''CREATE TABLE {table_name} (
                            id VARCHAR(20),
                            imdb_id VARCHAR(10),
                            title VARCHAR(255),
                            year VARCHAR(4),
                            slug VARCHAR(150),
                            synopsis TEXT,
                            runtime VARCHAR(4),
                            country VARCHAR(4),
                            last_updated FLOAT(16,1),
                            released INT,
                            certification VARCHAR(255),
                            torrents TEXT,
                            trailer VARCHAR(255),
                            genres VARCHAR(255),
                            images TEXT,
                            rating VARCHAR(255),
                            _v TINYINT,
                            PRIMARY KEY(id)
                            )'''
    try:
        cursor.execute(sql)
        print(f'Successfully created {table_name} table in {db_name} Database!')
    except Exception as e:
        print(f'Something went wrong trying to add the {table_name} table:\n\t{e}')
        traceback.print_exc()
    cursor.execute(f"SHOW COLUMNS FROM {table_name};")
    results = cursor.fetchall()
    for col in results:
        print(col)


# TODO: Update New Table w/movies

def get_movies(cursor, db_name, table_name):
    film_type = "movie"  # Can only be Anime, Movie, or Show
    url = "https://tv-v2.api-fetch.website/exports/" + film_type
    data = get(url)
    if data.status_code == 200:
        movie_list = []
        for bytes_line in data.iter_lines():
            string_line = bytes_line.decode()
            json_movie = json.loads(string_line)
            movie_list.append(json_movie)
        print(f"\tAdding movies to {db_name}.{table_name} now..")
        for movie in movie_list:
            add_movie2tbl(cursor, db_name, table_name, movie)

def add_movie2tbl(cursor, db_name, table_name, movie):
    try:
        for key, val in zip(movie.keys(), movie.values()):
            if key == '__v':
                movie['_v'] = movie.pop(f'{key}')
            elif key == '_id':
                movie['id'] = movie.pop(f'{key}')
            elif type(val) is dict:
                movie[key] = json.dumps(movie[key])
            else:
                pass
        value_placeholders = ', '.join(['%s'] * len(movie))
        cols = ', '.join(movie.keys())
        sql = f" INSERT IGNORE INTO {table_name} ( {cols} ) VALUES ( {value_placeholders} ); "
        values = tuple(str(val) for val in movie.values())
        cursor.execute(sql, values)
        db.commit()
    except Exception as e:
        print(f"[!] Something went wrong while attempting the insert: {e}")
        traceback.print_exc()


# TODO: Main Execution

if __name__ == '__main__':
    db_name = input('Enter database name: ')
    table_name = input('Enter table name: ')
    db = mysql.connector.connect(
        host='localhost',
        user='root',
        passwd=os.environ['DJANGO_DATABASE_PWD'],
    )
    cursor = db.cursor()
    try: 

        db_tool(cursor, db_name, table_name)
        get_movies(cursor, db_name, table_name)
        
    except Exception as e: traceback.print_exc()