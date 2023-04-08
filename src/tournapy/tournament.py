import math
import random

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
        self.current_phase_idx: int = 0
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
            return int(sum(list(map(lambda p: p.elo, players))) / len(players))
        else:
            return 0

    def clear_teams(self):
        teams_list = list(self.teams_dict.keys())
        for team_name in teams_list:
            success, feedback = self.remove_team(team_name)
            if not success:
                return False, feedback
        return True, 'All teams removed'

    def generate_teams(self) -> (bool, str):

        players_num = len(self.players_dict.values())
        team_num = math.floor(players_num / self.team_size)
        ideal_team_elo = sum(list(map(lambda p: p.elo, self.players_dict.values()))) / players_num
        print(f'ideal_team_elo={ideal_team_elo}')
        try:
            with open('resources/team_names.txt', 'r') as f:
                names_list = [line.strip() for line in f.readlines()]
                print(f'team_num={team_num}')
                team_names = random.sample(names_list, team_num)
                for team_name in team_names:
                    print(f'New team={team_name}')
                    # chatGPT
                    self.teams_dict[team_name] = Team(team_name)
                sorted_players = sorted(
                    list(filter(lambda p: p.team is None, self.players_dict.values())),
                    key=lambda p: p.elo, reverse=True)
                for player in sorted_players:
                    print(f'player={player}')
                    sorted_teams = list(map(lambda t: t.name,
                                            filter(lambda t: t.size < self.team_size,
                                                   sorted(self.teams_dict.values(),
                                                          key=lambda t: sum(
                                                              list(map(lambda p: p.elo,
                                                                       self.get_team_players(t.name))))))))
                    lowest_team = sorted_teams[0]
                    print(f'sorted_teams={sorted_teams}')
                    success, feedback = self.add_to_team(lowest_team, player.name)
                    print(f'success={success}')
                    print(f'feedback={feedback}')
                    print(f'player={player}')
                    print(f'team elo={self.teams_dict[lowest_team]}')
                    # MY WAY
                    # sorted_players = sorted(
                    #     list(filter(lambda p: p.team is None, self.players_dict.values())),
                    #     key=lambda p: p.elo, reverse=True)
                    # # print(f'sorted_players={sorted_players}')
                    # self.add_to_team(team_name, sorted_players[0].name)
                    # if self.teams_dict[team_name].size < self.team_size:
                    #     self.add_to_team(team_name, sorted_players[len(sorted_players) - 1].name)
                    # if self.teams_dict[team_name].size < self.team_size:
                    #     current_team = self.get_team_players(team_name)
                    #     # print(f'current_team={current_team}')
                    #     current_team_elo_tot = sum(
                    #         list(map(lambda p: p.elo, self.get_team_players(team_name))))
                    #     # print(f'current_team_elo_tot={current_team_elo_tot}')
                    #     next_player_limit = (ideal_team_elo + 15) * self.team_size - current_team_elo_tot
                    #     # print(f'next_player_limit={next_player_limit}')
                    #     next_players = sorted(
                    #         list(filter(lambda p: p.elo < next_player_limit and p.team is None, sorted_players)),
                    #         key=lambda p: p.elo, reverse=True)
                    #     if len(next_players) == 0:
                    #         next_players = sorted_players = sorted(
                    #             list(filter(lambda p: p.team is None, self.players_dict.values())),
                    #             key=lambda p: p.elo, reverse=False)
                    #     # print(f'next_players={next_players}')
                    #     self.add_to_team(team_name, next_players[0].name)
                    # print(f'final team={team_name}: {self.get_team_players(team_name)}')
            return True, 'Teams successfully generated'
        except FileNotFoundError:
            return False, 'Name generator cannot open resource file (FileNotFound)'

    def add_phase(self, order: int, ruleset: Ruleset):
        self.stages_dict[order] = ruleset

    def get_current_phase(self) -> Ruleset:
        return self.get_phase(self.current_phase_idx)

    def get_phase(self, phase_number: int) -> Ruleset:
        # print(f'self.stages_dict={self.stages_dict}')
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
        return pd.DataFrame(d).T.sort_values(['elo'], ascending=False, ignore_index=True)

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
