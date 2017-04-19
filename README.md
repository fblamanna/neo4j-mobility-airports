# neo4j-mobility-airports

## Description / Aim of the project
In this project I've been working with geo-localised Twitter data taken from users "overlapping" the [25 busiest european airports](https://en.wikipedia.org/wiki/List_of_the_busiest_airports_in_Europe) in the last three years. The dataset has been built over users that at least once are passing through an airport area, emitting a tweet. The user is then traced in his movements back and forth in time. Aims of the projects are:

* Correlate the sentiment and keywords used by users with strikes, delays etc, and to determinate a sort of quality of service whether airlines and/or routes names are found in the Twitter string;
* Trace the user in time and space, in order to evaluate its most probable place of residence, so to get a potential [O/D Matrix](https://en.wikipedia.org/wiki/Trip_distribution) of its trips.
