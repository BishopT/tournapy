# Tournament Package

This is a package to handle tournament creation and management. This is the core package of a discord bot designed to
manage tournaments inside a guild.

## How to use

Create Tournament Manager:

`manager = tournament.manager.TournamentsManager()`

then create your tournament, giving:

- a name ; shall be unique as it's the key for the manager to retrieve tournaments afterwards
- a team size ; the number of players per team ; the tournament will generate bracket for teams but players can retrieve
  their matches.
- an administrator name ; the manager provides function accessible only to tournament administrators. The list of
  administrators can be extended after creation

`manager.create_tournament('simple tourney', 1, 'administrator')`