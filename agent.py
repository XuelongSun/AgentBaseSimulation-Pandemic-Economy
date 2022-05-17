from enum import Enum
import uuid

import numpy as np

from common_data import *


class Status(Enum):
    """
    Agent status, following the SIR model
    """
    Susceptible = 's'
    Infected = 'i'
    Recovered_Immune = 'c'
    Death = 'm'


class InfectionSeverity(Enum):
    """
    The Severity of the Infected agents
    """
    Exposed = 'e'
    Asymptomatic = 'a'
    Hospitalization = 'h'
    Severe = 'g'


class AgentType(Enum):
    """
    The type of the agent, or the node at the Graph
    """
    Person = 'p'
    Business = 'b'
    House = 'h'
    Government = 'g'
    Healthcare = 'c'


class Agent:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', int(uuid.uuid4()))
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 0)
        self.wealth = kwargs.get('wealth', 0.0)


class HealthCare(Agent):
    def __init__(self, **kwargs):
        super(HealthCare, self).__init__(**kwargs)
        self.type = AgentType.Healthcare
        self.expenses = 0.0
        self.fixed_expenses = kwargs.get('fixed_expenses', 0.0)
        self.size = 0
        self.limitation = kwargs.get('limitation', 5)
        
    def checkin(self, person):
        self.size += 1
        self.expenses += person.expenses

    def update(self, env):
        env.government.wealth += self.fixed_expenses / 3
        self.wealth -= self.fixed_expenses


class Person(Agent):
    def __init__(self, **kwargs):
        super(Person, self).__init__(**kwargs)
        self.type = AgentType.Person
        self.age = kwargs.get('age', 0)
        
        ## 传染病
        self.status = kwargs.get('status', Status.Susceptible)
        self.infected_status = InfectionSeverity.Asymptomatic
        self.infected_time = kwargs.get('infected_time', 0)
        self.is_in_quarantine = False
        # 经济活动
        self.social_stratum = kwargs.get('social_stratum', 0)
        if self.age > 16 and self.age <= 65:
            self.economical_status = 1
        else:
            self.economical_status = 0
        # 收入
        self.incomes = kwargs.get("income", 0.0)
        # 支出
        self.expenses = kwargs.get("expense", 0.0)
        self.employer = None
        
        # 家庭活动
        self.house = None
        
        self.environment = kwargs.get("environment", None)
    
    def move_freely(self, amplitudes):
        if self.infected_status != InfectionSeverity.Asymptomatic:
            return
        x,y = np.random.normal(0,
                               amplitudes[self.status],
                               2)
        self.x = int(self.x + x)
        self.y = int(self.y + y)
        
    def move_to_work(self, amplitudes):
        if self.infected_status != InfectionSeverity.Asymptomatic:
            return
        if self.economical_status == 1:
            if self.employer is not None and self.employer.open:
                x, y = np.random.normal(0.0, 0.25, 2)
                self.x = int(self.employer.x + x)
                self.y = int(self.employer.y + y)
                self.employer.checkin(self)
            elif self.employer is None:
                self.move_freely(amplitudes)
    
    def move_to_home(self, amplitudes):
        if self.infected_status != InfectionSeverity.Asymptomatic:
            return
        
        if self.house is not None:
            x, y = np.random.normal(0.0, 0.25, 2)
            self.x = int(self.house.x + x)
            self.y = int(self.house.y + y)
            self.house.checkin(self)
        else:
            self.wealth -= self.incomes / 720
            self.move_freely(amplitudes)
    
    def move_to_healthcare(self, healthcare:HealthCare):
        x, y = np.random.normal(0.0, 0.5, 2)
        self.x = int(healthcare.x + x)
        self.y = int(healthcare.y + y)
        healthcare.checkin(self)
    
    def move_to_quarantine(self):
        x, y = np.random.normal(0.0, 0.5, 2)
        self.x = self.environment.quarantine_x + x
        self.y = self.environment.quarantine_y + y
        self.is_in_quarantine = True
        
    def demand(self, value=0.0):
        """Expense for product/services"""
        if self.house is not None:
            self.house.demand(value)
        self.wealth -= value
    
    def supply(self, value=0.0):
        """Income for work"""
        if self.house is not None:
            self.house.supply(value)
        else:
            self.wealth += value

    def after_death(self):
        if self.infected_status == InfectionSeverity.Hospitalization or \
            (self.infected_status == InfectionSeverity.Severe):
                self.environment.healthcare.size -= 1
            
        self.status = Status.Death
        self.infected_status = InfectionSeverity.Asymptomatic
        # 移出家庭
        if self.house is not None:
            self.move_to_home(self.environment.amplitudes)
            self.house.remove_mate(self)
        else:
            # ? 社会财富减少？
            self.environment.government.wealth -= self.expenses
        # 公司解雇
        if self.employer is not None:
            self.employer.fire(self)
        else:
            # ? 社会财富减少？
            self.environment.government.wealth -= self.expenses
        
    
    def update(self, env):
        recovering_time = env.recovering_time
        healthcare = env.healthcare
        statistics = env.get_statistics()
        critical_limit = env.critical_limit
        
        if self.status == Status.Death:
            return
        
        if self.status == Status.Infected:
            self.infected_time += 1
            ix = self.age // 10 - 1 if self.age > 10 else 0
            test_sub = np.random.random()
            if self.infected_status == InfectionSeverity.Asymptomatic:
                if age_hospitalization_probs[ix] > test_sub:
                    # 住院
                    self.infected_status = InfectionSeverity.Hospitalization
                    self.move_to_healthcare(healthcare)
            elif self.infected_status == InfectionSeverity.Hospitalization:
                if age_severe_probs[ix] > test_sub:
                    # 转为重症
                    self.infected_status = InfectionSeverity.Severe
                    # 医院超出承载能力
                    if statistics[InfectionSeverity.Severe.name]\
                        + statistics[InfectionSeverity.Hospitalization.name] >= \
                            critical_limit:
                                # 死亡
                                self.after_death()

            death_test = np.random.random()
            if age_death_probs[ix] > death_test:
                # ? 死亡之后的操作呢？
                self.after_death()
                return

            if self.infected_time > recovering_time:
                self.infected_time = 0
                if self.infected_status == InfectionSeverity.Hospitalization:
                    self.environment.healthcare.size -= 1
                self.status = Status.Recovered_Immune
                self.infected_status = InfectionSeverity.Asymptomatic


class Business(Agent):
    def __init__(self, **kwargs):
        super(Business, self).__init__(**kwargs)
        self.type = AgentType.Business
        self.employees = []
        self.num_employees = 0
        self.incomes = 0.0
        self.expenses = 0.0
        self.social_stratum = kwargs.get('social_stratum', 0)
        self.fixed_expense = kwargs.get('fixed_expenses', 0.0)

        # 经营情况
        self.open = True
        # 库存
        self.stocks = 10
        # 价格
        self.price = kwargs.get("price", (self.social_stratum+1) * 4.0)
        # 销量
        self.sales = 0
        
    def check_person(self, person:Person):
        v = person.status != Status.Death 
        v = (v and (person.infected_status == InfectionSeverity.Asymptomatic))
        return v
    
    def hire(self, person:Person):
        if self.check_person(person):
            self.employees.append(person)
            person.employer = self
            self.num_employees += 1
            # ? 个人开销和公司开销一致？
            self.fixed_expense += (person.expenses / 720) * 24
    
    def fire(self, person:Person):
        self.employees.remove(person)
        person.employer = None
        # ? 支付一个月工资？
        self.wealth -= person.incomes
        person.supply(person.incomes)
        self.num_employees -= 1
        # ? 个人开销和公司开销一致？
        self.fixed_expense -= (person.expenses / 720) * 24
    
    def checkin(self, person):
        """Employee is working"""
        self.stocks += 1
        self.wealth -= person.expenses / 720
    
    def supply(self, agent):
        """Incomes due to selling product/service"""
        qty = np.random.randint(1, 10)
        if qty > self.stocks:
            qty = self.stocks
        if agent.type == AgentType.Person:
            value = self.price * agent.social_stratum * qty
            agent.demand(value)
        else:
            # sell products to government
            value = self.price * 4 * qty
            agent.wealth -= value
        self.wealth += value
        self.incomes += value
        self.stocks -= qty
        self.sales += qty
    
    def demand(self, person):
        """Expenses due to employee payments"""
        labor = 0
        if person in self.employees:
            #labor = self.labor_expenses[agent.id]
            if person.status != Status.Death and person.infected_status == InfectionSeverity.Asymptomatic:
                labor = person.incomes
                person.supply(labor)

        self.wealth -= labor
        return labor
    
    def taxes(self, env):
        """Expenses due to taxes"""
        tax = env.government.tax * self.num_employees + self.incomes/20
        env.government.wealth += tax
        self.wealth -= tax
        return tax
    
    def update(self, env):
        # daily
        # ? 经济效益？
        env.government.wealth += self.fixed_expense / 3
        # ? 外部成本？
        self.wealth -= self.fixed_expense
    
    def accounting(self, env):
        # monthly
        labor = 0.0
        for person in self.employees:
            labor += self.demand(person)
        tax = self.taxes(env)

        # if 2 * (labor + tax) < self.incomes:
        #     # 扩招
        #     unemployed = env.get_unemployed()
        #     if len(unemployed) > 0:
        #         ix = np.random.randint(0, len(unemployed))
        #         self.hire(unemployed[ix])
        # elif (labor + tax) > self.incomes:
        #     # 裁员
        #     ix = np.random.randint(0, self.num_employees)
        #     self.fire(self.employees[ix])
        
        self.incomes = 0
        self.sales = 0


class Government(Agent):
    def __init__(self, **kwargs):
        super(Government, self).__init__(**kwargs)
        self.type = AgentType.Government
        self.tax = kwargs.get("tax", 2.0)
    
    def demand(self, agent):
        self.wealth -= agent.expenses
        agent.wealth += agent.expenses
        
    def update(self, env):
        # daily
        # 政府向企业购买产品/服务，public spending
        ix = np.random.randint(0, env.total_business)
        env.business[ix].supply(self)
    
    def accounting(self, env):
        # monthly
        # 政府向医疗的支出
        self.demand(env.healthcare)
        # 政府向homeless的补贴
        for p in env.get_homeless():
            self.demand(p)
        # 政府向无工作人员的补贴
        for p in env.get_unemployed():
            self.demand(p)


class House(Agent):
    def __init__(self, **kwargs):
        super(House, self).__init__(**kwargs)
        self.type = AgentType.House
        self.homemates = []
        self.size = 0
        self.incomes = 0
        self.expenses = 0
        self.fixed_expenses = kwargs.get('fixed_expenses',
                                         0.0)
        self.social_stratum = kwargs.get('social_stratum', 0)
        
    def append_mate(self, person:Person):
        self.homemates.append(person)
        self.wealth += person.wealth
        self.size += 1
        person.house = self
        # 回到家里来吧
        x, y = np.random.normal(0.0, 0.25, 2)
        person.x = int(self.x + x)
        person.y = int(self.y + y)
        self.fixed_expenses += (person.expenses / 720) * 24
    
    def demand(self, value=0.0):
        """Expense of consuming product/services"""
        self.wealth -= value
        self.expenses += value
        
    def supply(self, value=0.0):
        """Income of work of homemates"""
        self.wealth += value
        self.incomes += value
        
    def checkin(self, person):
        self.demand(person.expenses / 720)
    
    def remove_mate(self, person):
        self.homemates.remove(person)
        # 还留有遗产在家
        self.wealth -= person.wealth / 2
        self.size -= 1
        self.fixed_expenses -= (person.expenses / 720) * 24
    
    def accounting(self, env):
        # taxes
        taxes = self.incomes/10
        taxes += env.government.tax*self.size
        self.wealth -= taxes
        env.government.wealth += taxes
        # 月收入清零
        self.incomes = 0
        self.expenses = 0
    
    def update(self, env):
        self.wealth -= self.fixed_expenses
        # 日常收税
        env.government.wealth += self.fixed_expenses/10

