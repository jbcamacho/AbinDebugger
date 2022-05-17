"""
This module gets the stats from the database.
"""
from typing import Any, Dict, List, Tuple
from pymongo import MongoClient, CursorType
from pymongo.database import Collection
import controller.DebugController as DebugController

ASTRanking = Tuple[List[str], List[int]]

def get_stats() -> Dict[str, Any]:
    """ This function obtains the stats from the DB collection.
    
    :rtype: Dict[str, Any]
    """
    config = DebugController.APP_SETTINGS
    MONGO_URI = f"{config['DB_URI']}://{config['DB_HOST']}:{config['DB_PORT']}"
    client = MongoClient(MONGO_URI)
    db_connection = client[config['DEBUG_DB_NAME']]
    collection_BugPatterns = db_connection[config['DEBUG_DB_PATTERNS_COLLECTION']]
    
    total_bugfixes = stats_total_bugfixes(collection_BugPatterns)
    unique_bugfixes = stats_unique_bugfixes(collection_BugPatterns)
    unique_fixes = stats_unique_fixes(collection_BugPatterns)
    ranking_fixes = stats_ast_types_fixes(collection_BugPatterns)
    unique_bugs = stats_unique_bugs(collection_BugPatterns)
    ranking_bugs = stats_ast_types_bugs(collection_BugPatterns)
    
    stats_data = {
        'total_bugfixes': total_bugfixes,
        'unique_bugfixes': unique_bugfixes,
        'unique_fixes': unique_fixes,
        'ranking_fixes': ranking_fixes,
        'unique_bugs': unique_bugs,
        'ranking_bugs': ranking_bugs
    }
    return stats_data

def stats_total_bugfixes(db_collection: Collection) -> int:
    """ This function counts the total bug-fixes in the database.

    :param db_collection: the instance of the collection's connection.
    :type  db_collection: Collection
    :rtype: int
    """
    QUERY_COUNT_PATTERNS = [
        { 
            '$group': { '_id': 'null', 
                    'total_bugfixes': { '$count': { } } 
            } 
        }
    ]
    cursor_total_bugfixes = db_collection.aggregate(QUERY_COUNT_PATTERNS)
    total_bugfixes = next(cursor_total_bugfixes)['total_bugfixes']
    # print(f"Number of Matching Patterns found in the database: {total_patterns}")
    return total_bugfixes

def stats_unique_bugfixes(db_collection: Collection) -> int:
    """ This function counts the unique bug-fixes in the database.

    :param db_collection: the instance of the collection's connection.
    :type  db_collection: Collection
    :rtype: int
    """
    QUERY_UNIQUE_BUGFIXES = [                  
            {
                '$group': { 
                    '_id': {
                        'fix_hexdigest':'$fix_metadata.hexdigest',
                        'bug_hexdigest':'$bug_metadata.hexdigest',
                },
                'count':{'$sum':1}
                } 
            },
            { '$sort': { 'count': -1 } },
            { '$group': { '_id': 'null', 
                         'unique_bugfixes': { '$count': { } } 
                         }
            },
    ]
    cursor_unique_bugfixes = db_collection.aggregate(QUERY_UNIQUE_BUGFIXES)
    unique_bugfixes = next(cursor_unique_bugfixes)['unique_bugfixes']
    # print(f"Number of Unique Bugfixes found in the database: {unique_bugfixes}")
    return unique_bugfixes

def stats_unique_fixes(db_collection: Collection) -> int:
    """ This function counts the unique fixes in the database.

    :param db_collection: the instance of the collection's connection.
    :type  db_collection: Collection
    :rtype: int
    """
    QUERY_UNIQUE_FIXES = [                  
            {
                '$group': { 
                    '_id': {
                        'fix_hexdigest':'$fix_metadata.hexdigest',
                },
                'count':{'$sum':1}
                } 
            },
            { '$sort': { 'count': -1 } },
            { '$group': { '_id': 'null', 
                         'unique_fixes': { '$count': { } } 
                         }
            },
    ]
    cursor_unique_fixes = db_collection.aggregate(QUERY_UNIQUE_FIXES)
    total_unique_fixes = next(cursor_unique_fixes)['unique_fixes']
    # print(f"Number of Unique Fixes found in the database: {total_unique_fixes}")
    return total_unique_fixes

def stats_unique_bugs(db_collection: Collection) -> int:
    """ This function counts the unique bugs in the database.

    :param db_collection: the instance of the collection's connection.
    :type  db_collection: Collection
    :rtype: int
    """
    QUERY_UNIQUE_BUGS = [                  
            {
                '$group': { 
                    '_id': {
                        'bug_hexdigest':'$bug_metadata.hexdigest',
                },
                'count':{'$sum':1}
                } 
            },
            { '$sort': { 'count': -1 } },
            { '$group': { '_id': 'null', 
                         'unique_bugs': { '$count': { } } 
                         }
            },
            #{ '$limit': 10 }
    ]
    cursor_unique_bugs = db_collection.aggregate(QUERY_UNIQUE_BUGS)
    total_unique_bugs = next(cursor_unique_bugs)['unique_bugs']
    # print(f"Number of Unique Bugs found in the database: {total_unique_bugs}")
    return total_unique_bugs

def parse_ast_types(query_result: CursorType) -> ASTRanking:
    """ This function parses a query result.
    The query result is parsed to obtain the ranking.

    :param query_result: the query result.
    :type  query_result: CursorType
    :rtype: ASTRanking
    """
    ast_ranking = list(query_result)
    ast_types = []
    ast_freqs = []
    for item in ast_ranking:
        ast_types.append(item['_id']['ast_type'])
        ast_freqs.append(item['freq'])
    return (ast_types, ast_freqs)

def stats_ast_types_fixes(db_collection: Collection) -> ASTRanking:
    """ This function queries the database in order to obtain a ranking.

    :param db_collection: the instance of the collection's connection.
    :type  db_collection: Collection
    :rtype: ASTRanking
    """
    QUERY_FIXES_TYPES = [                  
            {
                '$group': { 
                    '_id': {
                        'ast_type':'$fix_metadata.ast_type',
                },
                'freq':{'$sum':1}
                } 
            },
            { '$sort': { 'freq': -1 } },
    ]
    cursor_ast_types = db_collection.aggregate(QUERY_FIXES_TYPES)
    (ast_types, ast_freqs) = parse_ast_types(cursor_ast_types)
    return (ast_types, ast_freqs)

def stats_ast_types_bugs(db_collection: Collection) -> ASTRanking:
    """ This function queries the database in order to obtain a ranking.

    :param db_collection: the instance of the collection's connection.
    :type  db_collection: Collection
    :rtype: ASTRanking
    """
    QUERY_BUGS_TYPES = [                  
            {
                '$group': { 
                    '_id': {
                        'ast_type':'$bug_metadata.ast_type',
                },
                'freq':{'$sum':1}
                } 
            },
            { '$sort': { 'freq': -1 } },
    ]
    cursor_ast_types = db_collection.aggregate(QUERY_BUGS_TYPES)
    (ast_types, ast_freqs) = parse_ast_types(cursor_ast_types)
    return (ast_types, ast_freqs)

if __name__ == "__main__":
    get_stats()