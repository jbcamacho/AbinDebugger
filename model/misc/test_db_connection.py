"""
This module checks the `ConnectionStatus`
of a given database's settings.
"""
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from controller.DebugController import ConnectionStatus
import controller.AbinLogging as AbinLogging


def test_db_connection( uri:str = 'mongodb', 
                        host: str = 'localhost', 
                        port: str = '27017', 
                        database_name: str = 'Bugfixes',
                        dbcollection: str = 'BugPatterns',
                        retry_times:int = 3) -> ConnectionStatus:
    """ This function tests the connection status given
    the connection paramaters.
        
    :param uri: The URI used by the MongoDB's engine.
    :type  uri: str
    :param host: The host to which the DB will be connected.
    :type  host: str
    :param port: The port to which the DB will be connected.
    :type  port: str
    :param database_name: The database that will be tested for conectivity.
    :type  database_name: str
    :param dbcollection: The collection that will be tested for conectivity.
    :type  dbcollection: str
    :param retry_times: The number of retries to connect to the DB.
    :type  retry_times: int
    :rtype: ConnectionStatus
    """
    MONGO_URI = f"{uri}://{host}:{port}"
    AbinLogging.dbConnection_logger.info(
        f"<pre>Testing connection on {MONGO_URI}...\n\n</pre>"
    )
    for _ in range(retry_times):
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=1000)
            client.server_info()
        except ServerSelectionTimeoutError as e:
            AbinLogging.dbConnection_logger.info(
                "<pre>Server not available. Retrying connection...\n\n</pre>"
            )
        except Exception as e:
            AbinLogging.dbConnection_logger.info(
                f"<pre>Unable to establish a connection. {e}</pre>"
            )
        else:
            break
    else:
        AbinLogging.dbConnection_logger.info(f"""
            <pre> <span style='color:#f33; font-weight: bold;'>
            Unable to connect to database instance {MONGO_URI} after {retry_times} retries.
            </span> </pre>
            """
        )
        return ConnectionStatus.Undefined
    
    from json import dumps
    db = client[database_name]
    collection_BugPatterns = db[dbcollection]
    AbinLogging.dbConnection_logger.info(
        "<pre>Querying for one pattern...\n\n</pre>"
    )
    test_pattern = collection_BugPatterns.find_one({ })
    if test_pattern is None:
        AbinLogging.dbConnection_logger.info(f"""
            <pre> <span style='color:#ffa500; font-weight: bold;'>
            Unable to retrive data from {database_name}.{dbcollection}\n\n
            </span></pre>
            """
        )
        return ConnectionStatus.Established
    
    test_pattern['_id'] = str(test_pattern['_id'])
    dump_data = dumps(test_pattern, indent=4)
    AbinLogging.dbConnection_logger.info(f"<pre id='json'>{dump_data}\n\n</pre>")
    AbinLogging.dbConnection_logger.info(f"""
        <pre> <span style='color:#008000; font-weight: bold;'>
        Successful conection to {MONGO_URI}
        </span> </pre>
        """
    )
    return ConnectionStatus.Secured


if __name__ == "__main__":
    test_db_connection()