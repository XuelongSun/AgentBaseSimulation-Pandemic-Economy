from manimlib import *

from agent import Status, AgentType

fontsize_s = 20
fontsize_m = 36
fontsize_l = 52

font = 'KaiTi'

social_stratum_color = [RED_A, RED_B, RED_C, RED_D, RED_E]

_colors = [WHITE, RED, GREEN, GREY]
person_status_color = {}
for s, c in zip(Status, _colors):
    person_status_color.update({s.name: c})

person_status_color_data = [WHITE, RED, GREEN, GREY]

wealth_type_color = {}
_colors = [PURPLE_C, ORANGE, PINK, RED, MAROON_A]
for s, c in zip(AgentType, _colors):
    wealth_type_color.update({s.name: c})
