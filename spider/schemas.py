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
                        'upload_time': {
                            'bsonType': 'date'
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
                        'netloc': {
                            'bsonType': 'string'
                        },
                        'path': {
                            'bsonType': 'string',
                            'description': 'Set to default value'
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