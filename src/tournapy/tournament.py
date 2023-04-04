import pandas as pd

from tournapy.core.model import Player, Team
from tournapy.core.ruleset import Ruleset


class Tournament:

    def __init__(self):
        self.name = None
        self.team_size = None
        self.registration_opened = False
        self.admins: list[str] = []
        self.players_dict: dict[str, Player] = {}
        self.teams_dict: dict[str, Team] = {}
        self.stages_dict: dict[int, Ruleset] = {}
        self.current_phase_idx = 0
        self.logo_url: str = ""

    def setup(self, organizer, name, team_size):
        self.name = name
        self.admins.append(organizer)
        self.team_size = team_size

    def add_player(self, name, elo) -> bool:
        p = Player(name, elo)
        if name not in self.players_dict.keys():
            self.players_dict[name] = p
            return True
        return False

    def remove_player(self, name):
        if name in self.players_dict.keys():
            team_name = self.players_dict[name].team
            if team_name is not None:
                self.remove_from_team(team_name, name)
            del self.players_dict[name]

    def add_to_team(self, team_name, player_name) -> (bool, str):
        try:
            t = self.teams_dict[team_name]
        except KeyError:
            t = Team(team_name)
            self.teams_dict[team_name] = t
        if t.size < self.team_size:
            try:
                p = self.players_dict[player_name]
                p.set_team(team_name)
                t.size += 1
                t.elo = self.get_team_elo(team_name)
                return True, f'{player_name} is now in team {t} ({t.size})'
            except KeyError:
                return False, f'{player_name} is not subscribed to tournament'
        else:
            return False, f'Cannot add any player to {team_name} because team is already complete'

    def remove_from_team(self, team_name, player_name) -> (bool, str):
        if team_name in self.teams_dict.keys() and player_name in self.players_dict.keys():
            players_names = list(map(lambda p: p.name, self.get_team_players(team_name)))
            if player_name in players_names:
                player = self.players_dict[player_name]
                player.team = None
                team = self.teams_dict[team_name]
                team.size += -1
                team.elo = self.get_team_elo(team_name)
            else:
                print(f'Player {player_name} is not in team {team_name}')
        else:
            print(f'Player {player_name} or team {team_name} does not exist in tournament {self.name}')

    def remove_team(self, team_name) -> (bool, str):
        try:
            for player in self.get_team_players(team_name):
                self.remove_from_team(team_name, player.name)
            del self.teams_dict[team_name]
            return True, f'team {team_name} successfully removed from {self.name} tournament'
        except KeyError:
            return False, f'team {team_name} does not exist.'

    def get_team_players(self, team_name: str) -> list[Player]:
        return list(filter(lambda p: p.team == team_name, self.players_dict.values()))

    def get_team_elo(self, team_name: str) -> int:
        players = self.get_team_players(team_name)
        if len(players) != 0:
            return sum(list(map(lambda p: p.elo, players))) / len(players)
        else:
            return 0

    def add_phase(self, order: int, ruleset: Ruleset):
        self.stages_dict[order] = ruleset

    def get_current_phase(self) -> Ruleset:
        return self.get_phase(self.current_phase_idx)

    def get_phase(self, phase_number) -> Ruleset:
        return self.stages_dict[phase_number]

    def get_stage(self, stage_name) -> Ruleset:
        for stage in self.stages_dict.values():
            if stage.name == stage_name:
                return stage
        return None

    def is_admin(self, user_id: str) -> bool:
        return user_id in self.admins

    def df_players(self):
        d = {}
        for k, v in self.players_dict.items():
            d[f'{k}'] = v.as_series()
        return pd.DataFrame(d).T

    def df_teams(self):
        d = {}
        for k, v in self.teams_dict.items():
            d[f'{k}'] = v.as_series()
        # TODO: sort by seeding
        return pd.DataFrame(d).T.sort_values(['elo'], ascending=False, ignore_index=True)

    def df_phases(self):
        d = {}
        for i in range(len(self.stages_dict)):
            d[f'{i}'] = self.stages_dict[i].as_series()
        return pd.DataFrame(d).T
