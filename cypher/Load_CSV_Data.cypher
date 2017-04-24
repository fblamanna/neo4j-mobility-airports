// LOAD CSV - Full Dataset
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
