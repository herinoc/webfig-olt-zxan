#import mysql.connector

#def get_db_connection():
#    conn = mysql.connector.connect(
#        host='db',
#        user='root',
#        password='tux',
#        database='nms_db'
#    )
#    return conn

import os
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'db'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'tux'),
        database=os.getenv('DB_NAME', 'nms_db'),
        port=int(os.getenv('DB_PORT', 3306))
    )
