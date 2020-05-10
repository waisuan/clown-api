import datetime, re, os
import hashlib, binascii
from DatabaseManager import DatabaseManager
import jwt


def get_db_mgr():
    if DatabaseManager._instance is None:
        DatabaseManager._instance = DatabaseManager(
            os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/'),
            os.environ.get('DB_NAME', 'emblem_2'))
    return DatabaseManager._instance


def clean_single_object_for_read(object):
    if not object:
        return object
    if 'tncDate' in object and object['tncDate']:
        object['tncDate'] = object['tncDate'].strftime('%d/%m/%Y')
    if 'ppmDate' in object and object['ppmDate']:
        object['ppmDate'] = object['ppmDate'].strftime('%d/%m/%Y')
    if object['dateOfCreation']:
        object['dateOfCreation'] = object['dateOfCreation'].strftime(
            '%d/%m/%Y %H:%M:%S')
    if object['lastUpdated']:
        object['lastUpdated'] = object['lastUpdated'].strftime(
            '%d/%m/%Y %H:%M:%S')
    if 'attachment' in object and object['attachment']:
        object['attachment'] = str(object['attachment'])
    if 'workOrderDate' in object and object['workOrderDate']:
        object['workOrderDate'] = object['workOrderDate'].strftime('%d/%m/%Y')
    if '_id' in object and object['_id']:
        object['_id'] = str(object['_id'])
    return object


def clean_for_read(objects):
    for object in objects:
        clean_single_object_for_read(object)
    return objects


def clean_for_write(object):
    if 'tncDate' in object and object['tncDate']:
        date_tokens = re.split('/', object['tncDate'])
        object['tncDate'] = datetime.datetime(int(date_tokens[2]),
                                              int(date_tokens[1]),
                                              int(date_tokens[0]))
        object['tncDateInInt'] = str(object['tncDate'].strftime('%Y%m%d'))
    if 'ppmDate' in object and object['ppmDate']:
        date_tokens = re.split('/', object['ppmDate'])
        object['ppmDate'] = datetime.datetime(int(date_tokens[2]),
                                              int(date_tokens[1]),
                                              int(date_tokens[0]))
        object['ppmDateInInt'] = str(object['ppmDate'].strftime('%Y%m%d'))
    if 'workOrderDate' in object and object['workOrderDate']:
        date_tokens = re.split('/', object['workOrderDate'])
        object['workOrderDate'] = datetime.datetime(int(date_tokens[2]),
                                                    int(date_tokens[1]),
                                                    int(date_tokens[0]))
        object['workOrderDateInInt'] = str(
            object['workOrderDate'].strftime('%Y%m%d'))
    if 'dateOfCreation' in object and object['dateOfCreation']:
        date_tokens = re.split('[/: ]', object['dateOfCreation'])
        object['dateOfCreation'] = datetime.datetime(int(date_tokens[2]),
                                                     int(date_tokens[1]),
                                                     int(date_tokens[0]),
                                                     int(date_tokens[3]),
                                                     int(date_tokens[4]),
                                                     int(date_tokens[5]))
    if 'dateOfCreation' not in object or not object['dateOfCreation']:
        object['dateOfCreation'] = datetime.datetime.now()
    object['dateOfCreationInInt'] = str(
        object['dateOfCreation'].strftime('%Y%m%d%H%M%S'))
    object['lastUpdated'] = datetime.datetime.now()
    object['lastUpdatedInInt'] = str(
        object['lastUpdated'].strftime('%Y%m%d%H%M%S'))
    object.pop('_id', None)
    return object


def convert_string_to_date(date_as_str, add_days=0):
    try:
        date_as_date = datetime.datetime.strptime(date_as_str, '%d-%m-%Y')
    except ValueError:
        return date_as_str
    return date_as_date + datetime.timedelta(days=add_days)


def convert_string_to_datetime(date_as_str, add_days=0):
    try:
        date_as_datetime = datetime.datetime.strptime(date_as_str,
                                                      '%d-%m-%Y %H:%M:%S')
    except ValueError:
        return date_as_str
    return date_as_datetime + datetime.timedelta(days=add_days)


def like(property):
    return [{
        'serialNumber': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'customer': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'state': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'district': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'accountType': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'model': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'brand': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'status': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'tncDate': convert_string_to_date(property)
    }, {
        'tncDateInInt': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'ppmDate': convert_string_to_date(property)
    }, {
        'ppmDateInInt': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'reportedBy': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'personInCharge': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'dateOfCreation': convert_string_to_datetime(property)
    }, {
        'dateOfCreationInInt': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'lastUpdated': convert_string_to_datetime(property)
    }, {
        'lastUpdatedInInt': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'lastUpdated': convert_string_to_date(property)
    }, {
        'workOrderNumber': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'workOrderDate': convert_string_to_date(property)
    }, {
        'workOrderDateInInt': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'actionTaken': {
            '$regex': property,
            '$options': 'i'
        }
    }, {
        'workOrderType': {
            '$regex': property,
            '$options': 'i'
        }
    }]


def get_sort_order(raw_order):
    if raw_order is None:
        return 0
    elif raw_order.lower() == 'asc':
        return 1
    elif raw_order.lower() == 'desc':
        return -1
    return 0


def purge_file(dir, filename=None):
    filelist = [
        f for f in os.listdir(dir) if filename is None or f == filename
    ]
    for f in filelist:
        os.remove(os.path.join(dir, f))


def flatten_list(obj, key):
    return list(o[key] for o in obj)


def hash(value, salt):
    dk = hashlib.pbkdf2_hmac('sha256', value.encode('ascii'), salt, 100000)
    return binascii.hexlify(dk)


def create_jwt_token(data):
    return jwt.encode(
        {
            'data': data,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(weeks=1)
        },
        os.environ.get('SECRET', 'secret'),
        algorithm='HS256')


def validate_jwt_token(token):
    try:
        jwt.decode(token,
                   os.environ.get('SECRET', 'secret'),
                   algorithm='HS256')
    except:
        return False
    return True
