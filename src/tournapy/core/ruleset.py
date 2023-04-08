import itertools
import math
from abc import ABC, abstractmethod
from enum import Enum

import pandas as pd

from tournapy.core.model import Match, Team

WINNING_POINTS = 3
LOSING_POINTS = 0
DRAW_POINTS = 1


class RulesetEnum(Enum):
    SIMPLE_ELIMINATION = 'Simple-Elimination'
    DOUBLE_ELIMINATION = 'Double-Elimination'
    ROUND_ROBIN = 'Round-Robin'
    SWISS_SYSTEM = 'Swiss-System'

    @classmethod
    def as_list(cls):
        return [e.value for e in cls]

    def get_ruleset(self, name: str, pool_size: int, bo: int):
        if self is RulesetEnum.SIMPLE_ELIMINATION:
            return SimpleElimination(name, self, pool_size, bo)
        if self is RulesetEnum.DOUBLE_ELIMINATION:
            pass  # TODO: implement double elimination bracket
        if self is RulesetEnum.ROUND_ROBIN:
            pass  # TODO: implement round robin bracket
        if self is RulesetEnum.SWISS_SYSTEM:
            return SwissSystem(name, self, pool_size, bo)

    def __str__(self):
        return self.value


class Ruleset(ABC):
    @abstractmethod
    def init_bracket(self):
        pass

    @abstractmethod
    def report_match_result(self, match: Match, blue_score: int, red_score: int):
        pass

    @abstractmethod
    def next_match(self, team):
        pass

    def __init__(self, name: str, rules_type: RulesetEnum, size: int, bo: int):
        self.name = name
        self.rules_type = rules_type
        self.pool: list[Team] = []
        self.pool_max_size = size
        self.bo = bo
        self.match_history: list[Match] = []
        self.bracket_depth = 0
        self.bracket = {}
        self.match_queue: list[str] = []
        self.running = False

    def add_team(self, team) -> bool:
        if len(self.pool) < self.pool_max_size:
            self.pool.append(team)
            return True
        else:
            return False

    def get_teams(self):
        return self.pool

    def get_team(self, team_name):
        for t in self.pool:
            if t.name == team_name:
                return t

    def get_match(self, match_id: str) -> Match:
        return self.bracket[match_id]

    def get_history(self):
        d = {}
        for i in range(len(self.match_history)):
            d[f'{i}'] = pd.Series(self.match_history[i].get_result(), index=[
                "blue team", "blue score",
                "red team", "red score",
                "winner"])
        return pd.DataFrame(d).T

    def start(self):
        self.running = True

    def get_bracket(self) -> pd.DataFrame:
        return pd.DataFrame(self.bracket, index=["matches"]).T.sort_index(ascending=False)

    # @abstractmethod
    def get_standings(self):
        for t in self.pool:
            t.points = 0
            t.goals_scored = 0
            t.goals_taken = 0
        # print('standings>>>>')
        for m in list(filter(lambda x: x.ended is True, self.match_history)):
            # print(f'm.get_winner()={m.get_winner()}')
            blue_team = self.get_team(m.blue_team)
            red_team = self.get_team(m.red_team)
            if red_team is None:
                red_team = Team('forfeit')
            blue_team.goals_scored += sum(m.blue_score)
            blue_team.goals_taken += sum(m.red_score)
            red_team.goals_scored += sum(m.red_score)
            red_team.goals_taken += sum(m.blue_score)
            if m.get_winner() == m.blue_team:
                blue_team.points += WINNING_POINTS
                red_team.points += LOSING_POINTS
            elif m.get_winner() == m.red_team:
                red_team.points += WINNING_POINTS
                blue_team.points += LOSING_POINTS
            else:
                blue_team.points += DRAW_POINTS
                red_team.points += DRAW_POINTS
        # d = {}
        # for i in range(len(self.pool)):
        #     d[f'{i}'] = self.pool[i].as_series()
        # return pd.DataFrame(d).T.sort_values(['points', 'goals diff'], ascending=[False, False], ignore_index=True)

    def as_series(self):
        return pd.Series(
            [self.name, self.pool_max_size, self.rules_type.value, self.running],
            index=["name", "size", "type", "running"]
        )


class SimpleElimination(Ruleset):

    def next_match(self, team):
        for m in list(map(self.get_match, self.match_queue)):
            # m = self.get_match(m_id)
            # print(f'team={team}')
            if team == m.blue_team or team == m.red_team:
                return m
        return None

    # def get_standings(self) -> pd.DataFrame:
    #     pass

    def report_match_result(self, match: Match, blue_score: int, red_score: int):
        if self.running:
            match.add_game_result(blue_score, red_score)
            match.compute_bo()
            if match.ended:
                print(f'match ended: {match}')
                self.match_queue.remove(match.id)
                self.match_history.append(match)
                winner = match.get_winner()
                next_match_team = f'winner({match.id})'
                next_match = self.next_match(next_match_team)  # get next match for the winner
                if next_match is not None:  # It was not the last match of the bracket
                    m: Match = self.bracket[next_match.id]
                    if next_match_team == next_match.blue_team:  # winner will play as blue team
                        # self.bracket[next_match.id] = Match(
                        #     next_match.id, next_match.bo, winner, next_match.red_team)
                        m.blue_team = winner
                    elif next_match_team == next_match.red_team:  # winner will play as red team
                        # self.bracket[next_match.id] = Match(
                        #     next_match.id, next_match.bo, next_match.blue_team, winner)
                        m.red_team = winner
                    else:
                        raise Exception(
                            f"Cannot program next match for {winner}")
                else:  # no more match in phase
                    self.running = False
            return f'match {match} updated.'
        else:
            return f'Cannot report match {match} from {self.name} stage. Stage not started.'

    def init_bracket(self) -> dict:
        no_of_teams = len(self.pool)
        print(f'pool={self.pool}, {no_of_teams} teams')

        self.bracket_depth = int(math.ceil(math.log(no_of_teams, 2)))
        self.bracket = {}
        for local_round in range(self.bracket_depth):
            matches_count = int(math.pow(2, local_round))
            teams_in_round = matches_count * 2
            for i in range(matches_count):
                match_id = f'{local_round}-{i + 1}'
                if local_round != self.bracket_depth - 1:
                    blue_team = f'winner({(local_round + 1)}-{i + 1})'
                    red_team = f'winner({(local_round + 1)}-{teams_in_round - i})'
                else:  # "first" round to be played, we know the teams
                    blue_seed = i + 1
                    blue_team = self.pool[blue_seed - 1].name
                    red_seed = teams_in_round - i
                    print(f'red_seed={red_seed}')
                    try:
                        red_team = self.pool[red_seed - 1].name
                    except IndexError:  # there is no team to compete
                        red_team = 'forfeit'
                self.match_queue.append(match_id)
                self.bracket[match_id] = Match(
                    match_id, self.bo, blue_team, red_team)

        return self.bracket


class DoubleElimination(Ruleset):

    def init_bracket(self):
        pass

    def report_match_result(self, match: Match, blue_score: int, red_score: int):
        pass

    def next_match(self, team):
        pass


class RoundRobin(Ruleset):

    def init_bracket(self):
        # TODO: use itertools.combinations
        pass

    def report_match_result(self, match: Match, blue_score: int, red_score: int):
        pass

    def next_match(self, team):
        pass


class SwissSystem(Ruleset):

    def __init__(self, name: str, rules_type: RulesetEnum, size: int, bo: int):
        Ruleset.__init__(self, name, rules_type, size, bo)
        self.round = 0
        self.max_rounds = 5

    @staticmethod
    def grouper(iterable, n):
        # coming from https://docs.python.org/fr/3/library/itertools.html#itertools-recipes
        args = [iter(iterable)] * n
        print(f'args={args}')
        return list(itertools.zip_longest(*args, fillvalue='forfeit'))

    def init_bracket(self):
        self.round = 1
        no_of_teams = len(self.pool)
        print(f'pool={self.pool}, {no_of_teams} teams')

        self.bracket = {}
        groups: list[tuple[str]] = SwissSystem.grouper(list(map(lambda t: t.name, self.pool)), 2)
        for group in groups:
            print(f'group={group}')
            match_id = f'{self.round}-{groups.index(group)}'
            m = Match(match_id, self.bo, blue_team=group[0], red_team=group[1])
            self.bracket[match_id] = m
            self.match_queue.append(match_id)

    def report_match_result(self, match: Match, blue_score: int, red_score: int):
        if self.running:
            match.add_game_result(blue_score, red_score)
            match.compute_bo()
            if match.ended:
                print(f'match ended: {match}')
                self.match_queue.remove(match.id)
                self.match_history.append(match)
                self.update_bracket()
            return f'match {match} updated.'
        else:
            return f'Cannot report match {match} from {self.name} stage. Stage not started.'

    def next_match(self, team):
        for m in list(map(self.get_match, self.match_queue)):
            # m = self.get_match(m_id)
            # print(f'team={team}')
            if team == m.blue_team or team == m.red_team:
                return m
        return None

    def update_bracket(self):
        if len(self.match_queue):
            print(f'round {self.round} not yet finished.')
        else:
            print(f'round {self.round} finished.')
            self.round += 1
            if self.round > self.max_rounds:
                print('All rounds finished. Stage is over')
                self.running = False

            else:
                print(f'Computing bracket for round {self.round}')
                self.get_standings()
                filtered_teams = list(filter(lambda t: t.points < 9, self.pool))
                teams_sorted_ga = sorted(filtered_teams,
                                         key=lambda team: (team.goals_scored - team.goals_taken),
                                         reverse=True)
                teams_sorted = sorted(teams_sorted_ga, key=lambda team: team.points, reverse=True)
                print(f'teams_sorted={teams_sorted}')
                groups: list[tuple[str]] = SwissSystem.grouper(list(map(lambda t: t.name, teams_sorted)), 2)
                for group in groups:
                    print(f'group={group}')
                    match_id = f'{self.round}-{groups.index(group)}'
                    m = Match(match_id, self.bo, blue_team=group[0], red_team=group[1])
                    self.bracket[match_id] = m
                    self.match_queue.append(match_id)
