import numpy as np

def distance(a, b):
    return np.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

def number_of_days(iteration):
    """
    Transform the iteration number in number of days
    As iteration runs hourly
    :param iteration: int
    :return: number of days
    """
    return iteration // 24

def check_time(iteration, start, end):
    """
    Test if the iteration falls between a range of hours

    :param iteration:
    :param start: [0, 24]
    :param end: [0, 24]
    :return: boolean
    """
    return start <= iteration % 24 < end

def day_of_week(iteration):
    return (iteration // 24) % 7 + 1

def new_day(iteration):
    return iteration % 24 == 0

def work_day(iteration):
    wd = day_of_week(iteration)
    return wd not in [6, 7]

def day_of_month(iteration):
    return (iteration // 24) % 30 + 1

def new_month(iteration):
    return day_of_month(iteration) == 1 and iteration % 24 == 0


def bed_time(iteration):
    return check_time(iteration, 0, 8)


def work_time(iteration):
    return check_time(iteration,8,16)


def lunch_time(iteration):
    return iteration % 24 == 12


def free_time(iteration):
    return check_time(iteration,17,24)


def sleep(a):
    if not new_day(a.iteration) and bed_time(a.iteration):
        return True
    return False