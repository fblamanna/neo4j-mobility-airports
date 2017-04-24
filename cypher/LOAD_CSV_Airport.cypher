// LOAD CSV Tweets within Airport
USING PERIODIC COMMIT
LOAD CSV WITH HEADERS FROM 'file:///tweets_in_AIRPORT.csv' AS row FIELDTERMINATOR '|'
WITH toInteger(row.tweet_ID) AS t_id
MERGE (airport:Airport {name:'ZRH'})
WITH airport, t_id
MATCH (loc:Loc {tweet_id:t_id})
MERGE (loc)-[:IS_WITHIN]->(airport)