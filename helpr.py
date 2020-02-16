import datetime, re, os

def clean_single_object_for_read(object):
    if not object:
        return object
    if 'tncDate' in object and object['tncDate'] is not None:
        object['tncDate'] = object['tncDate'].strftime('%d/%m/%Y')
    if 'ppmDate' in object and object['ppmDate'] is not None:
        object['ppmDate'] = object['ppmDate'].strftime('%d/%m/%Y')
    if object['dateOfCreation'] is not None:
        object['dateOfCreation'] = object['dateOfCreation'].strftime('%d/%m/%Y %H:%M:%S')
    if object['lastUpdated'] is not None:
        object['lastUpdated'] = object['lastUpdated'].strftime('%d/%m/%Y %H:%M:%S')
    if 'attachment' in object and object['attachment']:
        object['attachment'] = str(object['attachment'])
    if 'workOrderDate' in object and object['workOrderDate'] is not None:
        object['workOrderDate'] = object['workOrderDate'].strftime('%d/%m/%Y')
    if '_id' in object and object['_id'] is not None:
        object['_id'] = str(object['_id'])
    return object


def clean_for_read(objects):
    for object in objects:
        clean_single_object_for_read(object)
    return objects


def clean_for_write(object):
    if 'tncDate' in object and object['tncDate'] is not None:
        date_tokens = re.split('/', object['tncDate'])
        object['tncDate'] = datetime.datetime(int(date_tokens[2]), int(date_tokens[1]), int(date_tokens[0]))
    if 'ppmDate' in object and object['ppmDate'] is not None:
        date_tokens=re.split('/', object['ppmDate'])
        object['ppmDate'] = datetime.datetime(int(date_tokens[2]), int(date_tokens[1]), int(date_tokens[0]))
    if 'workOrderDate' in object and object['workOrderDate'] is not None:
        date_tokens=re.split('/', object['workOrderDate'])
        object['workOrderDate'] = datetime.datetime(int(date_tokens[2]), int(date_tokens[1]), int(date_tokens[0]))
    if 'dateOfCreation' in object and object['dateOfCreation'] is not None:
        date_tokens = re.split('[/: ]', object['dateOfCreation'])
        object['dateOfCreation'] = datetime.datetime(int(date_tokens[2]), int(date_tokens[1]), int(date_tokens[0]), int(date_tokens[3]), int(date_tokens[4]), int(date_tokens[5]))
    if 'dateOfCreation' not in object or object['dateOfCreation'] is None:
        object['dateOfCreation'] = datetime.datetime.now()
    object['lastUpdated'] = datetime.datetime.now()
    del object['_id']
    return object

def convert_string_to_date(date_as_str, add_days=0):
    try:
        date_as_date = datetime.datetime.strptime(date_as_str, '%d-%m-%Y')
    except ValueError:
        return date_as_str
    return date_as_date + datetime.timedelta(days=add_days)

def convert_string_to_datetime(date_as_str, add_days=0):
    try:
        date_as_datetime = datetime.datetime.strptime(date_as_str, '%d-%m-%Y %H:%M:%S')
    except ValueError:
        return date_as_str
    return date_as_datetime + datetime.timedelta(days=add_days)

def like(property):
    return [{'serialNumber': {'$regex': property, '$options': 'i'}},
            {'customer': {'$regex': property, '$options': 'i'}},
            {'state': {'$regex': property, '$options': 'i'}},
            {'district': {'$regex': property, '$options': 'i'}},
            {'accountType': {'$regex': property, '$options': 'i'}},
            {'model': {'$regex': property, '$options': 'i'}},
            {'brand': {'$regex': property, '$options': 'i'}},
            {'status': {'$regex': property, '$options': 'i'}},
            {'tncDate': convert_string_to_date(property)},
            {'tncDateInInt': {'$regex': property, '$options': 'i'}},
            {'ppmDate': convert_string_to_date(property)},
            {'ppmDateInInt': {'$regex': property, '$options': 'i'}},
            {'reportedBy': {'$regex': property, '$options': 'i'}},
            {'personInCharge': {'$regex': property, '$options': 'i'}},
            {'dateOfCreation': convert_string_to_datetime(property)},
            {'dateOfCreationInInt': {'$regex': property, '$options': 'i'}},
            {'lastUpdated': convert_string_to_datetime(property)},
            {'lastUpdatedInInt': {'$regex': property, '$options': 'i'}},
            {'dateOfCreation': convert_string_to_date(property)},
            {'lastUpdated': convert_string_to_date(property)}
            ]

def get_sort_order(raw_order):
    if raw_order is None:
        return 0
    elif raw_order.lower() == 'asc':
        return 1
    elif raw_order.lower() == 'desc':
        return -1
    return 0

def purge_file(dir, filename = None):
    filelist = [f for f in os.listdir(dir) if filename is None or f == filename]
    for f in filelist:
        os.remove(os.path.join(dir, f))

def flatten_list(obj, key):
    return list(o[key] for o in obj)