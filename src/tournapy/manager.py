from tournapy.core.ruleset import RulesetEnum
from tournapy.tournament import Tournament


class TournamentManager:

    def __init__(self):
        self.tourneys_dict: dict[str, Tournament] = {}

    def is_admin(self, tournament_name: str, user_id: str) -> bool:
        if self.exists(tournament_name):
            return self.get_tournament(tournament_name).is_admin(user_id)

    def exists(self, tournament_name: str):
        return tournament_name in self.tourneys_dict.keys()

    def create_tournament(self, tournament_name: str, team_size: int, user_id: str) -> bool:
        if not self.exists(tournament_name):
            tourney = Tournament()
            tourney.setup(user_id, tournament_name, team_size)
            self.tourneys_dict[tournament_name] = tourney
            return True
        else:
            return False

    def delete_tournament(self, tournament_name: str, user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            if self.is_admin(tournament_name, user_id):
                del self.tourneys_dict[tournament_name]
                return True, f'Tournament {tournament_name} deleted.'
            else:
                return False, f'Cannot delete tournament {tournament_name}. Missing admin rights.'
        else:
            return False, f'No tournament {tournament_name} existing.'

    def add_phase(self, tournament_name: str, phase_name: str, rules_name: str, pool_size: int, bo: int,
                  user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            if self.is_admin(tournament_name, user_id):
                ruleset = RulesetEnum(rules_name).get_ruleset(
                    phase_name, pool_size, bo)
                t: Tournament = self.tourneys_dict[tournament_name]
                t.add_phase(len(t.phases), ruleset)
                return True, f'{phase_name} phase added to {tournament_name} tournament.'
            else:
                return False, f'{phase_name} phase cannot be added to {tournament_name}. Missing admin rights.'
        else:
            return False, f'{tournament_name} does not exist.'

    def start_next_phase(self, tournament_name: str, user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            if self.is_admin(tournament_name, user_id):
                t: Tournament = self.tourneys_dict[tournament_name]
                # Retrieve list of teams eligible for next phase:
                # 1st case: no phase performed yet, every team should be added
                if t.current_phase_idx == 0:
                    teams_names = t.df_teams()['name']
                # 2nd case: get list of teams sorted by their rankings.
                else:
                    previous_phase = t.get_phase(t.current_phase_idx - 1)
                    teams_names = previous_phase.get_standings()['name']
                next_phase = t.get_current_phase()
                # adding previously retrieved list of teams. Will be added following team rank from previous phase.
                # will not accept team if next phase pool is complete.
                for team_name in teams_names:
                    # next_phase.add_team(t.get_team(team_name))
                    next_phase.add_team(t.teams_dict[team_name])
                if not next_phase.running:
                    next_phase.init_bracket()
                    next_phase.start()
                    return True, f'{next_phase.name} phase started.'
                else:
                    return False, f'{next_phase.name} already running.'
            else:
                return False, f'Cannot start next phase of {tournament_name}. Missing admin rights.'
        else:
            return False, f'{tournament_name} does not exist.'

    def add_player(self, tournament_name: str, player_name: str, user_id: str) -> (bool, str):
        # user_id = user.id of admin or user.name of player
        if self.exists(tournament_name):
            # players can self register. Admins can register anyone
            if self.is_admin(tournament_name, user_id) or player_name == user_id:
                t: Tournament = self.tourneys_dict[tournament_name]
                t.add_player(player_name, 0)
                return True, f'{player_name} player registered to {tournament_name}'
            else:
                return False, f'{player_name} player cannot be registered to {tournament_name}. Missing admin rights'
        else:
            return (
                False, f'{player_name} player cannot be registered to {tournament_name}. Tournament does not exists')

    def remove_player(self, tournament_name: str, player_name: str, user_id: str) -> (bool, str):
        # user_id = user.id of admin or user.name of player
        if self.exists(tournament_name):
            # players can self unregister. Admins can unregister anyone
            if self.is_admin(tournament_name, user_id) or player_name == user_id:
                t: Tournament = self.tourneys_dict[tournament_name]
                t.remove_player(player_name)
                return True, f'{player_name} player unregistered from {tournament_name}'
            else:
                return (
                    False, f'{player_name} player cannot be unregistered from {tournament_name}. Missing admin rights')
        else:
            return (
                False,
                f'{player_name} player cannot be unregistered from {tournament_name}. Tournament does not exists')

    def add_team(self, tournament_name: str, team_name: str, players_name: str, user_id: str) -> (bool, str):
        if self.exists(tournament_name):
            if self.is_admin(tournament_name, user_id) or user_id in players_name:
                t: Tournament = self.tourneys_dict[tournament_name]
                success, feedback = t.add_to_team(team_name, players_name)
                return success, feedback
            else:
                return False, f'Cannot form a team. Missing admin rights'
        else:
            return False, f'Tournament {tournament_name} does not exists'

    def get_tournaments_list(self) -> []:
        return self.tourneys_dict.keys()

    def get_tournament(self, tournament_name: str) -> Tournament:
        return self.tourneys_dict[tournament_name]
