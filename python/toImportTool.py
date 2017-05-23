# encoding: utf-8

"""
Pre-processing Data in order to use the neo4j-import command.
The input file is expected to be compressed (.gzip).
Required Packages: pandas, numpy.

Execution:
>> python toImport.py [airport code to load]

"""

__author__ = """ Fabio Lamanna (fabio@fabiolamanna.it) """

# Import Modules
import pandas as pd
import numpy as np
import itertools
import os
import sys

def toImport(airportcode):

	# Read Tweets
	df = pd.read_csv('tweets_' + airportcode + '.csv.gz',
			sep='|',
			compression='gzip',
			usecols=['User_ID', 'tweet_ID', 'Datetime', 'Longitude', 'Latitude','Tweet'],
			dtype={'User_ID':np.int, 'tweet_ID':np.int, 'Datetime':np.int, 'Longitude':np.float64, 'Latitude':np.float64, 'Tweet':str})

	# Read Tweets within Airport
	df_in = pd.read_csv('tweets_in_' + airportcode + '.csv', sep='|')

	# Nodes - Airport
	airport = pd.DataFrame({'Airport:ID(Airport-ID)': 0, 'airport_name': airportcode, ':LABEL': 'Airport'}, index=[0])
	airport.to_csv('airport.csv', sep='|', index=False)

	# Nodes - Users
	users = pd.DataFrame()
	users['User_ID:ID(Users-ID)'] = df[['User_ID']]
	users[':LABEL'] = 'User'
	u = users.drop_duplicates()
	u.to_csv('users.csv', sep='|', index=False)

	# Nodes - Locations
	locations = pd.DataFrame()
	locations['Loc_ID:ID(Loc-ID)'] = df.index
	locations['user_id'] = df[['User_ID']]
	locations['Datetime'] = df['Datetime']
	locations['Latitude'] = df[['Latitude']]
	locations['Longitude'] = df[['Longitude']]
	locations['tweet_ID'] = df[['tweet_ID']]
	locations[':LABEL'] = 'Loc'
	locations.to_csv('locations.csv', sep='|', index=False)

	# Nodes - Tweets
	tweets = pd.DataFrame()
	tweets['Tweet_ID:ID(tweet-ID)'] = df[['tweet_ID']]
	tweets['twitter_string'] = df[['Tweet']]
	tweets[':LABEL'] = 'Tweet'
	tweets.to_csv('tweets.csv', sep='|', index=False)

	# Relationships - :WRITES
	rels = pd.DataFrame()
	rels[':START_ID(Users-ID)'] = locations['user_id']
	rels[':END_ID(tweet-ID)'] = locations['tweet_ID']
	rels.to_csv('rels-writes.csv', sep='|', index=False)

	# Relationships - :EMITTED_IN
	rels = pd.DataFrame()
	rels[':START_ID(tweet-ID)'] = locations['tweet_ID']
	rels[':END_ID(Loc-ID)'] = locations['Loc_ID:ID(Loc-ID)']
	rels.to_csv('rels-emitted_in.csv', sep='|', index=False)

	# Relationships - :VISITED
	rels = pd.DataFrame()
	locations = locations.sort_values(by=['user_id','Datetime'])
	rels[':START_ID(Users-ID)'] = locations['user_id']
	rels[':END_ID(Loc-ID)'] = locations['Loc_ID:ID(Loc-ID)']
	rels.to_csv('rels-visited.csv', sep='|', index=False)

	# Relationships - :IS_WITHIN
	rels = pd.DataFrame()
	locations = locations[locations['tweet_ID'].isin(df_in['tweet_ID'])]
	rels[':START_ID(Loc-ID)'] = locations['Loc_ID:ID(Loc-ID)']
	rels[':END_ID(Airport-ID)'] = 0
	rels.to_csv('rels-is_within.csv', sep='|', index=False)

	# Relationships - :NEXT
	d = pd.read_csv('rels-visited.csv', sep='|')

	# Open temp archive
	archive = open('rels-next-temp.csv', 'w')

	# Reshape data
	for i, group in d.groupby(':START_ID(Users-ID)')[':END_IN(Loc-ID)']:
		for u,v in itertools.combinations(group,2):
			print >> archive, u, v

	# Close temp archive
	archive.close()

	# Read temp file
	d = pd.read_csv('rels-next-temp.csv', header=None, names=[':START_ID(Loc-ID)', ':END_IN(Loc-ID)'], sep=' ')

	# Drop Duplicates on starting node
	d.drop_duplicates(subset=[':START_ID(Loc-ID)'], inplace=True)

	# Write back the file
	d.to_csv('rels-next.csv', index=False, sep='|')

	# Delete temp file
	os.remove('rels-next-temp.csv')

if __name__ == "__main__":

    toImport(sys.argv[1])


