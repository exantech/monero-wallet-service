import peeweedbevolve
import peewee
import peewee_async

from settings import DATABASE

database = peewee_async.PostgresqlDatabase(
    database=DATABASE['database'],
    user=DATABASE['user'],
    password=DATABASE['password'],
    host=DATABASE['host'],
)

database.set_allow_sync(True)

objects = peewee_async.Manager(database)
