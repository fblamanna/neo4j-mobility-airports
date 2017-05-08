// Create [:NEXT] Relationships among consecutive locations for each user
MATCH (u:User)-[:VISITED]->(l:Location)
WITH u,l
ORDER BY l.datetime
WITH u, COLLECT(l) as locs
FOREACH(i in RANGE(0, size(locs)-2) | 
	FOREACH(L1 in [locs[i]] | 
		FOREACH(L2 in [locs[i+1]] | 
			CREATE UNIQUE (L1)-[:NEXT]->(L2))))