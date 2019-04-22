import json
import functools

import hetio.neo4j

from dj_hetmech_app.utils import (
    metapath_from_abbrev,
    get_neo4j_driver,
)


def get_paths(metagraph, metapath, source_identifier, target_identifier, limit=None):
    """
    Work in progress
    """
    metapath = metagraph.get_metapath(metapath)
    query = hetio.neo4j.construct_pdp_query(metapath, property='identifier', path_style='id_lists')
    if limit is not None:
        query += f'\nLIMIT {limit}'
    driver = get_neo4j_driver()
    neo4j_params = {
        'source': source_identifier, 
        'target': target_identifier,
        'w': 0.5,
    }
    with driver.session() as session:
        results = session.run(query, neo4j_params)
        results = [dict(record) for record in results]
    neo4j_node_ids = set()
    neo4j_rel_ids = set()
    paths_obj = []
    for record in results:
        row = {
            'metapath': metapath.abbrev,
        }
        row.update(record)
        neo4j_node_ids.update(row['node_ids'])
        neo4j_rel_ids.update(row['rel_ids'])
        paths_obj.append(row)
    
    node_id_to_info = get_neo4j_node_info(neo4j_node_ids)
    rel_id_to_info = get_neo4j_rel_info(neo4j_rel_ids)
    json_obj = {
        'query': {
            'source': source_identifier,
            'target': target_identifier,
            'metapath': metapath.abbrev,
            'metapath_id': [edge.get_id() for edge in metapath],
            'limit': limit,
        },
        'paths': paths_obj,
        'nodes': node_id_to_info,
        'relationships': rel_id_to_info,
    }
    return json_obj


cypher_node_query = '''\
MATCH (node)
WHERE id(node) IN $node_ids
RETURN
  id(node) AS neo4j_id,
  node.identifier AS identifier,
  head(labels(node)) AS node_label,
  properties(node) AS data
ORDER BY neo4j_id
'''


def get_neo4j_node_info(node_ids):
    node_ids = sorted(node_ids)
    driver = get_neo4j_driver()
    with driver.session() as session:
        results = session.run(cypher_node_query, node_ids=node_ids)
        results = [dict(record) for record in results]
    id_to_info = {x['neo4j_id']: x for x in results}
    return id_to_info


cypher_rel_query = '''\
MATCH ()-[rel]-()
WHERE id(rel) in $rel_ids
RETURN
  id(rel) AS neo4j_id,
  type(rel) AS rel_type,
  id(startNode(rel)) AS source_neo4j_id,
  id(endNode(rel)) AS target_neo4j_id,
  properties(rel) AS data
ORDER BY neo4j_id
'''


def get_neo4j_rel_info(rel_ids):
    rel_ids = sorted(rel_ids)
    driver = get_neo4j_driver()
    with driver.session() as session:
        results = session.run(cypher_rel_query, rel_ids=rel_ids)
        results = [dict(record) for record in results]
    id_to_info = {x['neo4j_id']: x for x in results}
    return id_to_info
