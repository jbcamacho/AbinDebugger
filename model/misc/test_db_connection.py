from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

import logging
from controller.AbinLogging import LOGGER_LEVEL, TEST_DB_HANDLER
logger = logging.getLogger(__name__)
logger.setLevel(LOGGER_LEVEL)
logger.addHandler(TEST_DB_HANDLER)

def test_db_connection( uri:str = 'mongodb', 
                        host: str = 'localhost', 
                        port: str = '27017', 
                        database_name: str = 'Bugfixes',
                        dbcollection: str = 'BugPatterns',
                        retry_times:int = 3) -> bool:

    MONGO_URI = f"{uri}://{host}:{port}"
    logger.info(f"<pre>Testing connection on {MONGO_URI}...\n\n</pre>")
    for _ in range(retry_times):
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)
            client.server_info()
        except ServerSelectionTimeoutError as e:
            logger.info("<pre>Server not available. Retrying connection...\n\n</pre>")
        except Exception as e:
            logger.info(f"<pre>Unable to establish a connection. {e}</pre>")
        else:
            
            break
    else:
        logger.info(f"<pre><span style='color:#f33; font-weight: bold;'>Unable to connect to database instance {MONGO_URI} after {retry_times} retries.</span></pre>")
        return 0
    
    from json import dumps
    db = client[database_name]
    collection_BugPatterns = db[dbcollection]
    logger.info("<pre>Querying for one pattern...\n\n</pre>")
    test_pattern = collection_BugPatterns.find_one({ })
    if test_pattern is None:
        logger.info(f"<pre><span style='color:#ffa500; font-weight: bold;'>Unable to retrive data from {database_name}.{dbcollection}\n\n</span></pre>")
        return 0
    
    test_pattern['_id'] = str(test_pattern['_id'])
    dump_data = dumps(test_pattern, indent=4)
    logger.info(f"<pre id='json'>{dump_data}\n\n</pre>")
    logger.info(f"<pre><span style='color:#008000; font-weight: bold;'>Successful conection to {MONGO_URI}</span></pre>")
    return 1


if __name__ == "__main__":
    test_db_connection()