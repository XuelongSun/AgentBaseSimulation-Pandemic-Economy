from agent import Status
import numpy as np


global_parameters = dict(

    # General Parameters
    width=200,
    height=200,

    # Demographic
    population_size=100,
    homemates_avg=3,
    homeless_rate=0.0005,
    amplitudes={
        Status.Susceptible: 10,
        Status.Recovered_Immune: 10,
        Status.Infected: 10
    },

    # Epidemiological
    critical_limit=0.02,
    contagion_rate=.9,
    incubation_time=5,
    contagion_time=10,
    recovering_time=20,
    initial_infected_perc=0.03,
    initial_immune_perc=0.0,

    # Economical
    total_wealth=10000000,
    total_business=25,
    minimum_income=900.0,
    minimum_expense=600.0,
    public_gdp_share=0.1,
    business_gdp_share=0.5,
    unemployment_rate=0.08,
    business_distance=12
)


def lockdown_with_quarantine_zone(a):
    if a.status == Status.Infected:
        if not a.is_in_quarantine:
            a.move_to_quarantine()
        return True
    else:
        return lockdown(a)


def quarantine_zone(a):
    if a.status == Status.Infected:
        if not a.is_in_quarantine:
            a.move_to_quarantine()
        return True
    else:
        return False
    

def quarantine_zone_rate(a):
    rate = 0.6
    test = np.random.random()
    if (a.status == Status.Infected) and (test < rate):
        if not a.is_in_quarantine:
            a.move_to_quarantine()
        return True
    else:
        return False


def home_quarantine(a):
    if a.status == Status.Infected:
        if not a.is_in_quarantine:
            a.move_to_home(a.environment.amplitudes)
        return True
    else:
        return False

def home_quarantine_rate(a):
    rate = 0.6
    test = np.random.random()
    if (a.status == Status.Infected) and (test < rate):
        if not a.is_in_quarantine:
            a.move_to_home(a.environment.amplitudes)
        return True
    else:
        return False
    
def lockdown(a):
    if a.house is not None:
        a.house.checkin(a)
    return True


def conditional_lockdown(a):
    if a.environment.get_statistics()['Infected'] > .05:
        return lockdown(a)
    else:
        return False


def vertical_isolation(a):
    if a.economical_status == 0:
        if a.house is not None:
            a.house.checkin(a)
            return True
    return False


isolated = []


def sample_isolated(environment, isolation_rate=.5, list_isolated=isolated):
    for a in environment.population:
        test = np.random.rand()
        if test <= isolation_rate:
            list_isolated.append(a.id)


def check_isolation(list_isolated, agent):
    if agent.id in list_isolated:
        agent.move_to_home(agent.environment.amplitudes)
        return True
    return False


def no_strict(a):
    return False


def get_scenario_parameters(name, **kwargs):
    simulation_para = global_parameters.copy()
    if name == 'eco_baseline':
        simulation_para.update(
            {
                'initial_infected_perc': 0,
                'initial_immune_perc': 1,
                'callbacks': {
                    'on_person_move': lambda x: no_strict(x)
                }
            }
        )
    elif name == 'do_nothing':
        simulation_para.update(
            {
                'callbacks': {
                    'on_person_move': lambda x: no_strict(x)
                }
            }
        )
    elif name == 'lockdown':
        simulation_para.update(
            {
                'callbacks': {
                    'on_person_move': lambda x: lockdown(x)
                }
            }
        )
    elif name == 'vertical_isolation':
        simulation_para.update(
            {
                'callbacks': {
                    'on_person_move': lambda x: vertical_isolation(x)
                }
            }
        )
    elif name == 'partial_isolation':
        rate = kwargs.get('isolation_rate', 0.5)
        simulation_para.update(
            {
                'contagion_distance': 1.,
                'callbacks': {
                    'post_initialize': lambda x: sample_isolated(x,
                                                                 isolation_rate=rate,
                                                                 list_isolated=isolated),
                    'on_person_move': lambda x: check_isolation(isolated, x)
                }
            }
        )
    elif name == 'use_mask':
        simulation_para.update(
            {
                'contagion_distance': 0.2,
                'contagion_rate': 0.3,
                'callbacks': {
                    'on_person_move': lambda x: no_strict(x)
                }
            }
        )
    elif name == 'mask_half_isolation':
        simulation_para.update(
            {
                'contagion_distance': 0.05,
                'contagion_rate': 0.1,
                'callbacks': {
                    'post_initialize': lambda x: sample_isolated(x,
                                                                 isolation_rate=.5,
                                                                 list_isolated=isolated),
                    'on_person_move': lambda x: check_isolation(isolated, x)
                }
            }
        )
    elif name == 'quarantine_zone':
        simulation_para.update(
            {
                'callbacks': {
                    'on_person_move': lambda x: quarantine_zone(x)
                }
            }
        )
    elif name == 'quarantine_zone_lockdown':
        simulation_para.update(
            {
                'callbacks': {
                    'on_person_move': lambda x: lockdown_with_quarantine_zone(x)
                }
            }
        )
    elif name == 'home_quarantine':
        simulation_para.update(
            {
                'callbacks': {
                    'on_person_move': lambda x: home_quarantine(x)
                }
            }
        )
    elif name == 'quarantine_zone_rate':
        simulation_para.update(
            {
                'callbacks': {
                    'on_person_move': lambda x: quarantine_zone_rate(x)
                }
            }
        )
    return simulation_para
