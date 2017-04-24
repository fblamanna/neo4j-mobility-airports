# encoding: utf-8

"""
LOAD_CSV data into Neo4j
Required Packages: Neo4j Driver

Execution:
>> python Load_CSV.py [username] [password] [cypher file to load]

"""

__author__ = """ Fabio Lamanna (fabio@fabiolamanna.it) """

# Import Modules
import sys

try:
    from neo4j.v1 import GraphDatabase, basic_auth
except ImportError:
    raise ImportError("You need to install the Neo4j Python Driver in order to properly run the script")

def LOAD_Data(username, passw, filename):

    # Open cypher file
    cypher = open(filename, 'r')

    # Set Database
    uri = 'bolt://localhost:7687'
    driver = GraphDatabase.driver(uri, auth=basic_auth(username, passw))

    # Begin Session
    session = driver.session()

    # Create Indices and Constraints
    session.run("CREATE CONSTRAINT ON (airport:Airport) ASSERT airport.name IS UNIQUE")
    session.run("CREATE CONSTRAINT ON (user:User) ASSERT user.user_id IS UNIQUE")
    session.run("CREATE CONSTRAINT ON (loc:Loc) ASSERT loc.tweet_id IS UNIQUE")
    session.run("CREATE INDEX ON :Loc(loc_id)")
    session.run("CREATE INDEX ON :Loc(datetime)")
    session.run("CREATE INDEX ON :Tweet(twitter_string)")

    # Import Green Data File into Neo4j
    session.run(cypher.read())
    session.close()

    # Building -[:NEXT]-> relation among consecutive locations

    # Get Number of unique User ids
    numberids = session.run("MATCH (user:User) RETURN user.user_id AS ids")

    # Loop through subgraphs
    for a in numberids:

        # Connect consecutive locations
        session.run("MATCH (loc:Loc) " +
                    "WHERE loc.loc_id = " + str(a['ids']) + " " +
                    "WITH loc ORDER BY loc.datetime WITH collect(loc) as locs " +
                    "FOREACH(i in RANGE(0, size(locs)-2) | " +
                    "FOREACH(L1 in [locs[i]] | " +
                    "FOREACH(L2 in [locs[i+1]] | " +
                    "CREATE UNIQUE (L1)-[:NEXT]->(L2))))"
                    )

    session.close()

if __name__ == "__main__":

    LOAD_Data(sys.argv[1], sys.argv[2], sys.argv[3])

