import peewee

db = peewee.SqliteDatabase("database.db")


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(BaseModel):
    uid = peewee.IntegerField(unique=True, primary_key=True)
    access = peewee.BooleanField(default=False)

    @classmethod
    def set_status(cls, uid: int):
        res = cls.get(cls.uid == uid)
        res.access = True
        res.save()

    @classmethod
    def get_status(cls, uid: int):
        cls.get_or_create(uid=uid)
        res = cls.get(cls.uid == uid)
        return res.access


class AdminList(BaseModel):
    uid = peewee.IntegerField(unique=True, primary_key=True)


class ChannelList(BaseModel):
    channel_url = peewee.TextField()
    channel_id = peewee.IntegerField()
    channel_name = peewee.TextField()


db.create_tables([User, AdminList, ChannelList])
