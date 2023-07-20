import psycopg2


def remove_versions():

    connection = psycopg2.connect(
        dbname="test_db", user="postgres", password="postgres", host="localhost")  # connection_factory=LoggingConnection)

    curs = connection.cursor()
    curs.execute('SELECT * FROM core_version;')
    curs.execute('DELETE FROM core_version;')
    curs.execute('DELETE FROM docs;')
    # print(curs.fetchall())
    print("REMOVED")
    curs.close()
