
from model.states.state import State
from model.states.ctf.ctf_main import ctf_main
from butils.utils import *

class ctf_def(ctf_main):
    def __init__(self, state_machine):
        super().__init__(state_machine)
        self.reached_start = False
        self.def_coord = [0,0,0]

    def enter(self, msg:dict):
        super().enter(msg)

        # Get a random point from the def area
        team = self.state_machine.game_state.player.team
        self.def_coord = self.state_machine.game_state.map.get_area_coord('def', team)

    def update(self):
        # Get whether to rush/def/mid 
        state = self.state_machine.game_state.ctf_get_objective()
        if state != 'def':
            self.state_machine.transition_state('ctf_initial', {})


        if calculate_distance(self.state_machine.game_state.player.coord, self.def_coord) < 400:
            self.reached_start = True

        if self.reached_start == False:
            # Move toward start coord
            new_coord = self.state_machine.game_state.map.path(self.state_machine.game_state.player.coord, self.def_coord, chargeboot=True)
            self.state_machine.update_joystick_input_and_angle(self.state_machine.game_state.player.coord, new_coord)
            self.state_machine.game_state.player.set_coord(new_coord)
        else:
            self.engage()

        