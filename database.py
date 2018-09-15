#This file is part of tryton-task. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import logging
import psycopg2
from invoke import Collection, task

logger = logging.getLogger(__name__)

@task()
def owner(ctx, database, to_owner):
    '''
    Changes the owner of the given database to the given owner username.
    '''
    connection = psycopg2.connect('dbname=%s' % database)
    cursor = connection.cursor()
    cursor.execute('ALTER DATABASE "%s" OWNER TO "%s"' % (database, to_owner))

    cursor.execute("SELECT tablename FROM pg_tables WHERE "
        "schemaname = 'public'")
    tables = set([x[0] for x in cursor.fetchall()])
    cursor.execute("SELECT sequence_name FROM information_schema.sequences "
        "WHERE sequence_schema = 'public'")
    tables |= set([x[0] for x in cursor.fetchall()])
    cursor.execute("SELECT table_name FROM information_schema.views WHERE "
        "table_schema = 'public'")
    tables |= set([x[0] for x in cursor.fetchall()])
    for table in tables:
        cursor.execute('ALTER TABLE public."%s" OWNER TO "%s"' % (table,
                to_owner))
    connection.commit()
    connection.close()
    logger.info('Changed %d tables, sequences and views to %s' % (len(tables),
        to_owner))

# Add Invoke Collections
DatabaseCollection = Collection('database')
DatabaseCollection.add_task(owner)
