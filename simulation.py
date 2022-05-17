import numpy as np
from agent import InfectionSeverity, Person, Business, Government, House, HealthCare, Status
from common_data import *
from util import *

class Simulator:
    def __init__(self, **kwargs):
        self.population = []
        self.houses = []
        self.total_business = kwargs.get('total_business', 10)
        self.business = []
        # 购买行为的距离阈值
        self.business_distance = kwargs.get('business_distance', 10)
        
        # 社会结构参数
        ## 1.财富层级分布
        self.social_stratum = kwargs.get('social_stratum',
                                         lambda: int(np.random.rand(1) * 100 // 20))
        ## 2.流浪比例
        self.homeless_rate = kwargs.get("homeless_rate", 0.0005)
        ## 3.失业率
        self.unemployment_rate = kwargs.get("unemployment_rate", 0.12)
        ## 4.家庭结构（平均人数和人数标准差）
        self.homemates_avg = kwargs.get("homemates_avg", 3)
        self.homemates_std = kwargs.get("homemates_std", 1)
        ## 5.年龄分布
        self.age_distribution = kwargs.get("age_distribution",
                                           lambda: int(np.random.beta(2, 5, 1) * 100))
        ## 6.人口数量
        self.population_size = kwargs.get("population_size", 20)
        ## 7.政府财政收入比
        self.public_gdp_share = kwargs.get('public_gdp_share', 0.1)
        ## 8.商业经济共享比
        self.business_gdp_share = kwargs.get('business_gdp_share', 0.5)
        ## 9.财富总量
        self.total_wealth = kwargs.get("total_wealth", 10 ** 6)
        ## 10.最低人均日收入
        self.minimum_income = kwargs.get("minimum_income", 1000.0)
        ## 11.最低人均日支出
        self.minimum_expense = kwargs.get("minimum_expense", 600.0)
        ## 12.医疗系统的承载能力 x%的总人口
        self.critical_limit = kwargs.get("critical_limit", 0.05)
        
        # 传染病人群参数
        ## 初始感染率
        self.initial_infected_perc = kwargs.get("initial_infected_perc", 0.05)
        ## 初始免疫人群
        self.initial_immune_perc = kwargs.get("initial_immune_perc", 0.05)
        ## 潜伏期
        self.incubation_time = kwargs.get('incubation_time', 5)
        ## 感染后具备感染能力的持续时间
        self.contagion_time = kwargs.get('contagion_time', 20)
        ## 恢复时间
        self.recovering_time = kwargs.get('recovering_time', 20)
        ## 行动能力
        self.amplitudes = kwargs.get('amplitudes',
                                     {Status.Susceptible: 10,
                                      Status.Recovered_Immune: 10,
                                      Status.Infected: 10})
        ## 安全社交距离
        self.contagion_distance = kwargs.get("contagion_distance", 1.)
        ## 小于安全距离的传染率
        self.contagion_rate = kwargs.get("contagion_rate", 0.9)
        
        
        # 仿真时空参数
        self.width = kwargs.get("width", 10)
        self.height = kwargs.get("height", 10)
        self.iteration = 0
        self.num_month = 0
        self.num_day = 0
        self.statistics = None
        # 回调函数，用于实施干预措施
        self.callbacks = kwargs.get("callbacks", {})
        
        # 政府和医院
        margin = 0.01
        self.healthcare = HealthCare(x=self.width*margin, y=self.height*margin,
                                     limitation=int(self.population_size*self.critical_limit))
        self.government = Government(x=self.width*(1-margin), y=self.height*(1-margin))
        # 隔离区
        self.quarantine_x = self.width*(1 - margin)
        self.quarantine_y = self.height*margin
    
    def create_agent(self, status, infected_time=0):
        age = self.age_distribution()
        social_stratum = self.social_stratum()
        p = Person(
            age=age, status=status, social_stratum=social_stratum,
            infected_time=infected_time,
            environment=self
        )
        self.population.append(p)
        return p
    
    def create_house(self, social_stratum=None):
        x, y = self.random_position()
        if social_stratum is None:
            social_stratum = self.social_stratum()
        self.houses.append(House(x=x, y=y,
                                 social_stratum=social_stratum))

    def create_business(self):
        x, y = self.random_position()
        social_stratum = self.social_stratum()
        self.business.append(Business(x=x, y=y,
                                      social_stratum=social_stratum))

    def intervention_initialize(self, **kwargs):
        self.iteration = 0
        self.num_month = 0
        self.num_day = 0
        self.statistics = None
        
        ## 初始感染率
        self.initial_infected_perc = kwargs.get("initial_infected_perc", 0.05)
        ## 初始免疫人群
        self.initial_immune_perc = kwargs.get("initial_immune_perc", 0.05)
        ## 安全社交距离
        self.contagion_distance = kwargs.get("contagion_distance", 1.)
        ## 小于安全距离的传染率
        self.contagion_rate = kwargs.get("contagion_rate", 0.9)
        
        # 回调函数，用于实施干预措施
        self.callbacks = kwargs.get("callbacks", {})
        
        self.government.wealth = self.total_wealth * self.public_gdp_share
        
        # reset wealth distribution
        for quintile in range(5):
            if self.total_business > 5:
                btotal = lorenz_curve[quintile] * (self.total_wealth * self.business_gdp_share)
                bqty = max(1.0,
                           np.sum([1.0 for a in self.business if a.social_stratum == quintile]))
            else:
                btotal = self.total_wealth * self.business_gdp_share
                bqty = self.total_business
            bshare = btotal / bqty
            for b in filter(lambda x: x.social_stratum == quintile,
                            self.business):
                b.wealth = bshare
                b.expenses = 0
                b.stock = 10
                b.sales = 0
                b.incomes = 0
            ptotal = lorenz_curve[quintile] * self.total_wealth * \
                (1 - (self.public_gdp_share + self.business_gdp_share))
            pqty = max(1.0, np.sum([1 for a in self.population if
                                   a.social_stratum == quintile and a.economical_status == 1]))
            pshare = ptotal / pqty
            for p in filter(lambda x: x.social_stratum == quintile, self.population):
                if p.economical_status == 1:
                    p.wealth = pshare
                    p.incomes = basic_income[p.social_stratum] * self.minimum_income
                p.expenses = basic_income[p.social_stratum] * self.minimum_expense
        
        # reset house
        for h in self.houses:
            h.homemates = []
            h.size = 0
            h.incomes = 0
            h.expenses = 0
            h.wealth = 0
        
        # reset person status
        infect_num = int(self.initial_infected_perc * self.population_size)
        immune_num = int(self.initial_immune_perc * self.population_size)
        for i, p in enumerate(self.population):
            # re-home
            if p.house is not None:
                p.house.append_mate(p)
                p.move_to_home(self.amplitudes)
            if i < infect_num:
                p.status = Status.Infected
                p.infected_time = 5
            elif i < self.population_size - immune_num:
                p.status = Status.Susceptible
                p.infected_time = 0
            else:
                p.status = Status.Recovered_Immune
                p.infected_time = 0
            p.infected_status = InfectionSeverity.Asymptomatic
            p.is_in_quarantine = False

        self.healthcare.size = 0
        self.healthcare.expenses = 0
        self.healthcare.wealth = 0
        
        if 'post_initialize' in self.callbacks.keys():
            self.callbacks['post_initialize'](self)
        
    def initialize(self):    
        # 创建家庭
        for i in range(int(self.population_size / self.homemates_avg)):
            self.create_house(social_stratum=i%5)
        # 创建公司
        for i in range(self.total_business):
            self.create_business()
        
        # 创建 初始感染人群
        for i in range(int(self.population_size * self.initial_infected_perc)):
            self.create_agent(Status.Infected, infected_time=5)
        # 创建 初始免疫人群
        for i in range(int(self.population_size * self.initial_immune_perc)):
            self.create_agent(Status.Recovered_Immune)
        # 创建 易感人群
        for i in range(self.population_size - len(self.population)):
            self.create_agent(Status.Susceptible)
        
        # 分配社会总财富
        ## 1.政府财政
        self.government.wealth = self.total_wealth * self.public_gdp_share
        ## 按财富等级分配
        for quintile in range(5):
            ## 2.分配给公司
            if self.total_business > 5:
                btotal = lorenz_curve[quintile] * (self.total_wealth * self.business_gdp_share)
                bqty = max(1.0,
                           np.sum([1.0 for a in self.business if a.social_stratum == quintile]))
            else:
                btotal = self.total_wealth * self.business_gdp_share
                bqty = self.total_business
            share = btotal / bqty
            for b in filter(lambda x: x.social_stratum == quintile,
                            self.business):
                b.wealth = share
            ## 3.分配给个人
            ptotal = lorenz_curve[quintile] * self.total_wealth * \
                (1 - (self.public_gdp_share + self.business_gdp_share))
            pqty = max(1.0, np.sum([1 for a in self.population if
                                   a.social_stratum == quintile and a.economical_status == 1]))
            share = ptotal / pqty
            # （都遍历每个人了，顺便设置这个人的各个状态吧）
            ## 先筛选出这个quintile的家庭，方便后面分配
            _houses = [x for x in filter(lambda x: x.social_stratum == quintile, self.houses)]
            nhouses = len(_houses)
            ## 要保证每个财富级别至少有一个家庭
            if nhouses == 0:
                self.create_house(social_stratum=quintile)
                _houses = [self.houses[np.random.randint(0, len(self.houses))]]
                nhouses = 1
                
            for p in filter(lambda x: x.social_stratum == quintile, self.population):
                if p.economical_status == 1:
                    p.wealth = share
                    p.incomes = basic_income[p.social_stratum] * self.minimum_income
                    ## 随机指定为某公司员工
                    unemployed_test = np.random.rand()
                    if unemployed_test >= self.unemployment_rate:
                        ix = np.random.randint(0, self.total_business)
                        self.business[ix].hire(p)
                ## 日开销
                p.expenses = basic_income[p.social_stratum] * self.minimum_expense
                
                ## 给他一个家
                homeless_test = np.random.rand()
                if not (quintile == 0 and homeless_test <= self.homeless_rate):
                    for kp in range(6):
                        # 先尝试塞进去
                        ix = np.random.randint(0, nhouses)
                        if _houses[ix].size < self.homemates_avg + self.homemates_std:
                            _houses[ix].append_mate(p)
                            continue
                    # 如果人满了 就随便塞吧
                    if p.house is None:
                        ix = np.random.randint(0, len(self.houses))
                        self.houses[ix].append_mate(p)
        
        if 'post_initialize' in self.callbacks.keys():
            self.callbacks['post_initialize'](self)

    def run(self):
        if new_day(self.iteration):
            if self.iteration > 1:
                self.num_day += 1
            new_d = True
        else:
            new_d = False
        
        if new_month(self.iteration):
            if self.iteration > 1:
                self.num_month += 1
            new_m = True
        else:
            new_m = False
            
        # 个人活动
        for p in filter(lambda x: x.status != Status.Death, self.population):
            
            if not self.callbacks['on_person_move'](p):
                if bed_time(self.iteration):
                    # 睡觉
                    p.move_to_home(self.amplitudes)
                elif lunch_time(self.iteration) or free_time(self.iteration) or \
                    (not work_day(self.iteration)):
                        # 散步
                        p.move_freely(self.amplitudes)
                elif work_day(self.iteration) and work_time(self.iteration):
                    # 搬砖
                    p.move_to_work(self.amplitudes)
            
            # 消费 (可能包含满足基本生活的消费，lockdown下满足距离的个体依然会有经济活动)
            if p.infected_status == InfectionSeverity.Asymptomatic:
                for b in filter(lambda x: x != p.employer, self.business):
                    if distance(p, b) <= self.business_distance:
                        b.supply(p)

            # 状态更新daily
            if new_d:
                p.update(self)
        
        # 公司活动
        for bus in filter(lambda b: b.open, self.business):
            if new_d:
                bus.update(self)

            if self.iteration > 1 and new_m:
                bus.accounting(self)
        
        # 政府活动
        if new_d:
            self.government.update(self)
        if self.iteration > 1 and new_m:
            self.government.accounting(self)
        
        # 医院活动
        if new_d:
            self.healthcare.update(self)
        # 家庭活动
        if new_d:
            for h in self.houses:
                h.update(self)
        if self.iteration > 1 and new_m:
            for h in self.houses:
                h.accounting(self)
        
        for i in range(self.population_size):
            for j in range(i + 1, self.population_size):
                pi = self.population[i]
                pj = self.population[j]
                if pi.status == Status.Death or pj.status == Status.Death:
                    continue
                if distance(pi, pj) <= self.contagion_distance:
                    self.contact(pi, pj)
                    self.contact(pj, pi)
        
        self.iteration += 1
        
    def contact(self, agent1, agent2):
        if (agent1.status == Status.Susceptible) and (agent2.status == Status.Infected):
            low = np.random.randint(-1, 1)
            up = np.random.randint(-1, 1)
            if agent2.infected_time >= self.incubation_time + low \
                    and agent2.infected_time <= self.contagion_time + up:
                contagion_test = np.random.random()
                if contagion_test <= self.contagion_rate:
                    agent1.status = Status.Infected
                    agent1.infection_status = InfectionSeverity.Asymptomatic
 
    def get_statistics(self, type='info'):
        if self.statistics is None:
            self.statistics = {}
        # SIR 各个人群的占比
        for s in Status:
            self.statistics[s.name] = np.sum(
                [1 for p in self.population if p.status == s]
            ) / self.population_size
        # 感染人群的各情况占比
        for s in filter(lambda x: x!= InfectionSeverity.Exposed, InfectionSeverity):
            self.statistics[s.name] = np.sum(
                [1 for p in self.population if p.infected_status == s and \
                    p.status != Status.Death]
            ) / self.population_size
        # 分财富等级的财富总量
        for q in range(5):
            self.statistics['Q{}'.format(q + 1)] = np.sum(
                [p.wealth for p in self.population if p.social_stratum == q and p.age >= 18 \
                    and p.status != Status.Death]
            )
        
        # 各类型财富占社会财富之比
        self.statistics['W_Business'] = np.sum([b.wealth for b in self.business])/self.total_wealth
        self.statistics['W_Person'] = np.sum([p.wealth for p in self.population])/self.total_wealth
        self.statistics['W_Government'] = self.government.wealth/self.total_wealth
        
        # 医院
        self.statistics['Hospital'] = np.clip(self.healthcare.size/self.healthcare.limitation,0.01,1)

        if type == 'info':
            return {k: v for k, v in self.statistics.items() if not k.startswith('Q') \
                    and not k.startswith('W')}
        elif type == 'ecom':
            return {k: v for k, v in self.statistics.items() if k.startswith('Q') \
                    or k.startswith('W')}
        elif type == 'all':
            return self.statistics
        elif type == 'visualize':
            return {k: v for k, v in self.statistics.items() if not k.startswith('Q')}
    
    def get_unemployed(self):
        return [p for p in self.population if (p.employer is None)
                and p.status != Status.Death and p.infected_status == InfectionSeverity.Asymptomatic]

    def get_homeless(self):
        return [p for p in self.population if (p.house is None)
                and p.status != Status.Death and p.infected_status == InfectionSeverity.Asymptomatic]
            
    def _xclip(self, x):
        return np.clip(int(x), 0, self.width)

    def _yclip(self, y):
        return np.clip(int(y), 0, self.height)
    
    def random_position(self):
        x = self._xclip(self.width / 2 + (np.random.randn(1) * (self.width / 3)))
        y = self._yclip(self.height / 2 + (np.random.randn(1) * (self.height / 3)))
        return x, y