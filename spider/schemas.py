from pymongo import ASCENDING,DESCENDING

urls_to_crawl_schema = {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'additionalProperties': True,
                    'required': ['url', 'upload_time'],
                    'properties': {
                        'url': {
                            'bsonType': 'string'
                        },
                        'netloc':{'bsonType':'string'},
                        'status':{
                            'bsonType':'int',
                            'description':'0 : uncrawled, 1:crawling, 2:crawled'
                        },
                        'upload_time': {
                            'bsonType': 'int'
                        }
                    }
                }
            }
urls_to_crawl_index = "url"

crawled_urls_schema = {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'additionalProperties': True,
                    'required': ['netloc', 'path'],
                    'properties': {
                        'url':{
                            'bsonType':'string'
                        },
                        'netloc': {
                            'bsonType': 'string'
                        },
                        'path': {
                            'bsonType': 'string',
                            'description': 'Set to default value'
                        },
                        'status':{
                            'bsonType':'int',
                            'description':'0 : unindexed, 1:indexing, 2:indexed'
                        }
                    }
                }
            }
crawled_urls_index = {"netloc": ASCENDING, "path": ASCENDING}

robots_schema = {
                '$jsonSchema': {
                    'bsonType': 'object',
                    'additionalProperties': True,
                    'required': ['netloc', 'file_content'],
                    'properties': {
                        'netloc': {
                            'bsonType': 'string'
                        },
                        'file_content': {
                            'bsonType': 'string',
                            'description': 'Set to default value'
                        }
                    }
                }
            }
robots_index = "netloc"