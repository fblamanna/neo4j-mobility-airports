# neo4j-mobility-airports

## Description
In this project I'm showing how to manage huge amount of geo-localised Twitter data within [Neo4j](https://neo4j.com). Data are taken from users "overlapping" the [25 busiest european airports](https://en.wikipedia.org/wiki/List_of_the_busiest_airports_in_Europe) in the last three years. The dataset has been built over users that at least once are passing through an airport area, emitting a tweet. Users are then traced in their movements through consecutive locations back and forth in time.

### Credits
Twitter data have been collected by [IFISC](https://ifisc.uib-csic.es/en/) for research purposes. Thanks to [LARUS](http://www.larus-ba.it) for the support in the graph database procedures and management.

## Dataset
The original data stream from the Twitter API provides a ***.json*** file with desired fields; in this case, we are working with the following data format, where each record represents a single tweet:

```json
{"id":tweet_id,"user":{"id":user_id},"text":"twitter_string","created_at":datetime,"coordinates":{"type":"Point","coordinates":[latitude,longitude]}}
```

It has been reduced to a ***.csv*** file containing the following fields/types:

* user_ID - *int*: user id;
* tweet_ID - *int*: tweet id;
* datetime - *datetime*: date and time of the tweet;
* longitude - *float*: longitude;
* latitude - *float*: latitude;
* twitter_string - *str*: string of the tweet.

Another {key: value} pair file provides information about users who emitted tweets in the airport area only, in the form {user_id: tweet_id}. This information may be available after post-processing of geographical data or directly within the API by means od geographical constraints when querying for the data.

## Neo4j
The Neo4j graph database went into the light of being the “right” place to store data, thanks to its capacity of direct modelling relations among data, its high availability and its easy, fast and clean query language Cypher. Data are suitable to be imported in Neo4j since at each user are associated one or more locations in functions of its Twitter activity. The database design steps are:

* Database Modelling (Neo4j);
* Data Import (Python, Java).

### Modelling
The data model may follow the scheme provided in [this](/images/datamodel.png) picture. This is a single-based user scheme; the full model will cover the whole set di users in the dataset. Nodes may be modelled in the following way:

* **(:User {user_id:'value'})** contains information about the User, in this case *user_id*;
* **(:Loc {loc_id:'location id', datetime:'value', longitude:'value', latitude:'value'})** is the Location node visited by the users;
* **(:Tweet {twitter_string:'value'})** is the node containing the information about the tweet written by each user;
* **(:Airport {airportcode:'value'})** is the node representing the geographical location of the airport area.

**(:Loc)** nodes are then connected with the [:NEXT] relation, which links consecutive Locations paths of single users. In order to identify locations that belong to each user, the **loc_id** property has been set equal of the **user_id**.

Relations among nodes may be represented by:

```cypher
(:User)-[:VISITED]->(:Loc)
(:User)-[:WRITES]->(:Tweet)
(:Tweet)-[:EMITTED]->(:Loc)
(:Loc)-[:IS_WITHIN]->(:Airport)
```

### Indices and Constraints
Before importing the data, indices and constraints have to be set up in the environment, in order to allow Neo4j to look-up nodes through an index-based search to speed-up all the importing phase (and later queries as well). If you run the Cypher script, you have to set constraints and indices one by one in the browser:

```cypher
// Create Indices and Constraints
CREATE CONSTRAINT ON (airport:Airport) ASSERT airport.name IS UNIQUE
CREATE CONSTRAINT ON (user:User) ASSERT user.user_id IS UNIQUE
CREATE CONSTRAINT ON (loc:Loc) ASSERT loc.tweet_id IS UNIQUE
CREATE INDEX ON :Loc(loc_id)
CREATE INDEX ON :Loc(datetime)
CREATE INDEX ON :Tweet(twitter_string)
```

Here we define constraints for uniqueness of the names of Airports, on User IDs and Tweet IDs (this automatically creates indices on those nodes properties). We then create indices for faster lookups on Location ID, Datetime and the string of the tweet.


### Importing Data into Neo4j
Loading data into Neo4j can be done in two different ways: through the batch *Load CSV* importer or faster (but after some data preprocessing) with the *neo4j-import* tool shell command. We're reviewing the following procedures:

1. Directly from Cypher with the ```LOAD CSV``` function;
2. Using a Python script with the [Neo4j Python driver](https://neo4j.com/developer/python/);
3. Using the neo4j-import tool.

#### Cypher (LOAD CSV)
You can run directly the following cypher scripts within the Neo4j browser window or command line to import the full dataset:

```cypher
// LOAD CSV - /cypher/LOAD_CSV_Data.cypher
USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM 'file:///tweets_AIRPORT.csv' AS row FIELDTERMINATOR '|'
WITH coalesce(toInteger(row.User_ID), "") AS u_id, toInteger(row.Datetime) AS dt, coalesce(row.Tweet, "") AS tw, toInteger(row.tweet_ID) AS t_id, toFloat(row.Latitude) AS lat, toFloat(row.Longitude) AS lon

// Node creation
MERGE (user:User {user_id: u_id})
MERGE (tweet:Tweet {twitter_string:tw})
MERGE (user)-[:WRITES]->(tweet)

// Create a new Location at each step, with coordinates and link it with the corresponding tweet emitted and user
CREATE (loc:Loc {loc_id: u_id})
SET loc.datetime = dt, loc.tweet_id = t_id, loc.latitude = lat, loc.longitude = lon
CREATE UNIQUE (user)-[:VISITED]->(loc)
CREATE UNIQUE (tweet)-[:EMITTED_IN]->(loc)
```

Since we are dealing with possible incomplete data, the following script allows to delete nodes having *null* values for **tweet_id** and **user_id**:

```cypher
MATCH (user:User {user_id:''}), (t:Tweet {twitter_string:''})
DETACH DELETE user, t
```

We can then proceed importing relationships of Locations within the airport area:

```cypher
// LOAD CSV Tweets within Airport - /cypher/LOAD_CSV_Airport.cypher
USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM 'file:///tweets_in_AIRPORT.csv' AS row FIELDTERMINATOR '|'
WITH toInteger(row.tweet_ID) AS t_id

// Create the node for the airport
MERGE (airport:Airport {name:'ZRH'})
WITH airport, t_id

// Find locations within the airport area
MATCH (loc:Loc {tweet_id:t_id})
MERGE (loc)-[:IS_WITHIN]->(airport)
```

#### Python (LOAD CSV)
The **/python/Load_CSV.py** script can be used to manage all the indices and importing phase of the data into Neo4j. The script can be execute by running:

    $ python Load_CSV.py [username] [password] [cypher file to load]

This will provide to set all constraints and indices, read the ***.cypher*** files and import them into the database.

##### [:NEXT] Relationship
The trickiest part here is to connect consecutive locations visited by each user with the [:NEXT] relation. To do so, we have to loop within each subgraph made by each user and all the locations that belong to him. The loop has to run within the Python script because here we can extract a list of all users ids with:

```python
numberids = session.run("MATCH (user:User) RETURN user.user_id AS ids")
```

and loop through them, extracting each subgraph with the WHERE statement at each loop:

```python
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
```
#### neo4j-import

When you have very big files, it is worth to spent some time in data pre-processing in order to use the neo4j-import command line tool; it writes directly the files in the Neo4j format and it is significally faster than other approaches. However, files have to follow some syntax and format constraints that require some data pre-processing.

##### Data Preprocessing

The **/python/toImportTool.py** script get as input the ***.csv*** file to load and return as output a series of reduced ***.csv*** files as follows:

1. **users.csv** to build the :User nodes;
2. **locations.csv** to build the :Loc nodes;
3. **tweets.csv** to build the :Tweet nodes;
4. **rels-visited.csv** to build the [:VISITED] relationship;
5. **rels-emitted_in.csv** to build the [:EMITTED_IN] relationship;
6. **rels-writes.csv** to build the [:WRITES] relationship;
7. **rels-next.csv** to build the [:NEXT] relationship;

##### Running the Tool

The tool can be run [according to your Neo4j installation](https://neo4j.com/docs/operations-manual/current/tools/import/command-line-usage/), basically following:

```
.bin/neo4j-import   --into [folder] \
                    --nodes users.csv \
                    --nodes locations.csv \
                    --nodes tweets.csv \
                    --relationships:VISITED rels-visited.csv \
                    --relationships:EMITTED_IN rels-emitted_in.csv \
                    --relationships:WRITES rels-writes.csv \
                    --relationships:NEXT rels-next.csv\
                    --delimiter "|"
```

## Analysis

We can then perform several statistical analysis over the dataset thanks to cypher and [py2neo](http://py2neo.org/v3/).

### Bot Detection

Here we investigate potential 'bot' users, characterized by a very high number of tweets containing similar messages. We ask the dataset for the number of users and the number of tweets they emitted:

```cypher
MATCH (u:User)-[:WRITES]->(t:Tweet)-[:EMITTED_IN]->(l:Loc)-[:IS_WITHIN]->(a:Airport)
RETURN u AS user, count(t) AS nTweets, t AS tweet, count(u) AS nUsers
ORDER BY nTweets DESC
```

Results allow to identify potential automatic users. We select the first in the ranking the the contents of its messages:

```cypher
MATCH (u:User {user_id:520225342})-[:WRITES]->(t:Tweet)
return t.twitter_string AS string
```

The **/python/HammingDistance.py** script uses **py2neo** in order to collect information from Neo4j directly through a Python, where we can perform statistical analysis over the content of the messages. Here we plot the so called [Hamming Distance](https://en.wikipedia.org/wiki/Hamming_distance) among strings. This returns a bloxplot with the distribution of the distance among each pair of messages.
