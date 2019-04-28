import datetime, re

def clean_for_read(machines):
    for machine in machines:
        if machine['tncDate'] is not None:
            machine['tncDate'] = machine['tncDate'].strftime('%d/%m/%Y')
        if machine['ppmDate'] is not None:
            machine['ppmDate'] = machine['ppmDate'].strftime('%d/%m/%Y')
        if machine['dateOfCreation'] is not None:
            machine['dateOfCreation'] = machine['dateOfCreation'].strftime('%d/%m/%Y %H:%M:%S')
        if machine['lastUpdated'] is not None:
            machine['lastUpdated'] = machine['lastUpdated'].strftime('%d/%m/%Y %H:%M:%S')
    return machines


def clean_for_write(machine):
    if machine['tncDate'] is not None:
        date_tokens = re.split('/', machine['tncDate'])
        machine['tncDate'] = datetime.datetime(int(date_tokens[2]), int(date_tokens[1]), int(date_tokens[0]))
    if machine['ppmDate'] is not None:
        date_tokens=re.split('/', machine['ppmDate'])
        machine['ppmDate'] = datetime.datetime(int(date_tokens[2]), int(date_tokens[1]), int(date_tokens[0]))
    if machine['dateOfCreation'] is None:
        machine['dateOfCreation'] = datetime.datetime.now()
    else:
        date_tokens = re.split('[/: ]', machine['dateOfCreation'])
        machine['dateOfCreation'] = datetime.datetime(int(date_tokens[2]), int(date_tokens[1]), int(date_tokens[0]), int(date_tokens[3]), int(date_tokens[4]), int(date_tokens[5]))
    machine['lastUpdated'] = datetime.datetime.now()
    return machine

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
            {'ppmDate': convert_string_to_date(property)},
            {'reportedBy': {'$regex': property, '$options': 'i'}},
            {'personInCharge': {'$regex': property, '$options': 'i'}},
            {'dateOfCreation': convert_string_to_datetime(property)},
            {'lastUpdated': convert_string_to_datetime(property)},
            {'dateOfCreation': {'$gte': convert_string_to_date(property), '$lt': convert_string_to_date(property, 1)}},
            {'lastUpdated': {'$gte': convert_string_to_date(property), '$lt': convert_string_to_date(property, 1)}}
            ]
