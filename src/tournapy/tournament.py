import pandas as pd

from tournapy.core.model import Player, Team
from tournapy.core.ruleset import RuleSet


class Tournament:

    def __init__(self):
        self.name = None
        self.team_size = None
        self.registration_opened = False
        self.admins: list[str] = []
        self.players_dict: dict[str, Player] = {}
        self.teams_dict: dict[str, Team] = {}
        self.phases: dict[int, RuleSet] = {}
        self.current_phase_idx = 0

    def setup(self, organizer, name, team_size):
        self.name = name
        self.admins.append(organizer)
        self.team_size = team_size

    def add_player(self, name, elo):
        p = Player(name, elo)
        if name not in self.players_dict.keys():
            self.players_dict[name] = p

    def remove_player(self, name):
        if name in self.players_dict.keys():
            del self.players_dict[name]

    def add_to_team(self, team_name, *players_names) -> (bool, str):
        try:
            t = self.teams_dict[team_name]
        except KeyError:
            t = Team(team_name)
            self.teams_dict[team_name] = t
        if t.size < self.team_size:
            for name in players_names:
                try:
                    p = self.players_dict[name]
                    p.set_team(team_name)
                    t.size += 1
                    return True, f'{name} is now in team {t} ({t.size})'
                except KeyError:
                    return False, f'{name} is not subscribed to tournament'
        else:
            return False, f'Cannot add any player to {team_name} because team is already complete'

    def get_team_players(self, team_name: str):
        return list(filter(lambda p: p.team == team_name, self.players_dict.values()))

    def add_phase(self, order: int, ruleset: RuleSet):
        self.phases[order] = ruleset

    def get_current_phase(self) -> RuleSet:
        return self.get_phase(self.current_phase_idx)

    def get_phase(self, phase_number) -> RuleSet:
        return self.phases[phase_number]

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
        for i in range(len(self.phases)):
            d[f'{i}'] = self.phases[i].as_series()
        return pd.DataFrame(d).T
