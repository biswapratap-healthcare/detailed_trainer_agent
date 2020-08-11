import pymongo


class MongoDB:

    def __init__(self,
                 uri='localhost',
                 un='alexbw',
                 pw=None):
        self.__db_handle = pymongo.MongoClient(uri)

    def close(self):
        self.__db_handle.close()

    def to_db(self, payload, db=None, collection=None):
        db = self.__db_handle[db]
        col = db[collection]
        try:
            x = col.insert(payload)
            print("Inserted : " + str(x))
        except Exception as e:
            print(str(e))

    def from_db(self, query, key=None, db=None, collection=None, all=False, skp=0, lmt=100):
        db = self.__db_handle[db]
        col = db[collection]
        try:
            if key is not None and all is True:
                records = col.find({}, {key: 1, "_id": False})
                records = list(records)
                result = [d[key] for d in records]
                return result
            elif key is None and all is True:
                records = col.find({}, {"_id": False})
                records = list(records)
                return records
            elif key is None and all is False:
                records = col.find(query).skip(skp).limit(lmt)
                records = list(records)
                return records
            else:
                records = col.find({}, {key: 1, "_id": False}).skip(skp).limit(lmt)
                records = list(records)
                result = [d[key] for d in records]
                return result
        except Exception as e:
            print(str(e))
