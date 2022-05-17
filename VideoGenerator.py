import os, sys

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import numpy as np
from scipy.stats import beta

from manimlib import *

from simulation import Simulator

from visualize_common import *
from common_data import *

from interventions import get_scenario_parameters


class Environment:
    
    margin = 1.5       
    world_pos_offset_x = 0
    world_pos_offset_y = 0

    def __init__(self, sim,
                 width=FRAME_Y_RADIUS, height=FRAME_Y_RADIUS):
        self.sim = sim
        self.w2f_scale = FRAME_Y_RADIUS / sim.height
        self.boundary_box = Rectangle(
           sim.width*self.w2f_scale + self.margin,
           sim.height*self.w2f_scale + self.margin,
           color=LIGHT_BROWN,
           stroke_width=6
        )
        
        # healthcare
        self.h_pos = self.transform2frame(self.sim.healthcare.x,  self.sim.healthcare.y)
        self.h = SVGMobject('svgs/hospital.svg')
        self.hc_scale = 1.
        self.h_nc = Circle(radius=self.h.get_height()/2,
                           stroke_width=1,
                           stroke_color=BLUE_A).next_to(self.h, RIGHT, buff=0.2)
        self.h_ncf = always_redraw(
            lambda: Sector(radius=self.h_nc.get_radius(),
                           fill_color=BLUE_A, fill_opacity=1,
                           n_components=16,
                           angle=np.clip(self.sim.healthcare.size/self.sim.healthcare.limitation, 0.01, 1)*TAU,
                           stroke_width=0).scale(self.hc_scale).move_arc_center_to(self.h_nc.get_center())
        )
        
        self.hc = VGroup(self.h, self.h_nc, self.h_ncf)
        
        
        # government
        self.g_pos = self.transform2frame(self.sim.government.x, self.sim.government.y)
        self.g = SVGMobject('svgs/government.svg')
        self.g_wb = Rectangle(
            self.g.get_width()/3,
            self.g.get_height(),
            fill_color=RED_A,
            stroke_width=1,
            fill_opacity=1).next_to(self.g, RIGHT, buff=0.2)
        
        self.gb = VGroup(self.g, self.g_wb)

    def transform2frame(self, x, y):
        return (
            (x-self.sim.width/2)*self.w2f_scale + self.world_pos_offset_x,
            (y-self.sim.height/2)*self.w2f_scale + self.world_pos_offset_y,
            0)


class Video(Scene):
    def construct(self):
        intervention_dic = {
            'do_nothing': '无干预',
            'eco_baseline': '无疫情的经济',
            'lockdown': '封城',
            'quarantine_zone': '隔离区隔离',
            'home_quarantine': '居家隔离',
            'partial_isolation':'50% 隔离',
            'use_mask':'戴口罩'
        }
        intervention = list(intervention_dic.keys())[0]
        simulation_para = get_scenario_parameters(intervention)
        sim = Simulator(**simulation_para)
        sim.initialize()
        time_out = 1440
    
        env = Environment(sim)
        
        # boundary
        self.play(Write(env.boundary_box))
        
        # government
        self.play(FadeIn(env.g))
        self.wait()
        self.play(Write(env.g_wb))
        # show the meaning of bar
        for t in range(1):
            coin = SVGMobject("svgs/coin.svg").scale(0.4).move_to((-1,1,0))
            self.play(FadeIn(coin), run_time=0.5)
            self.play(coin.animate.move_to(env.g.get_center()))
            self.play(FadeOut(coin),
                      env.g_wb.animate.stretch_about_point(1.2, 1, env.g_wb.get_bottom()),
                      run_time=0.2)
        for t in range(1):
            coin = SVGMobject("svgs/coin.svg").scale(0.4)
            self.play(FadeIn(coin), run_time=0.5)
            self.play(coin.animate.move_to((-1,1,0)))
            self.play(FadeOut(coin),
                      env.g_wb.animate.stretch_about_point(0.8, 1, env.g_wb.get_bottom()),
                      run_time=0.2)

        self.play(env.gb.animate.scale(0.3), run_time=0.5)
        self.play(env.gb.animate.move_to((env.g_pos)),
                  run_time=0.2)
        
        # # move to the left
        env.world_pos_offset_x = -4
        env.world_pos_offset_y = 0
        self.play(
            env.boundary_box.animate.shift((-4, 0, 0)),
            env.gb.animate.shift((-4, 0, 0))
        )
        
        # healthcare
        self.play(FadeIn(env.h))
        self.wait()
        self.play(Write(env.h_nc))
        self.play(Write(env.h_ncf))
        for t in range(1):
            pati = SVGMobject("svgs/patient.svg",
                              stroke_color=RED).scale(0.4).move_to((-1,1,0))
            self.play(FadeIn(pati), run_time=0.5)
            self.play(pati.animate.move_to(env.h.get_center()))
            sim.healthcare.size += 0.2
            self.play(FadeOut(pati))
        
        sim.healthcare.size -= 0.2
        
        env.hc_scale = 0.2
        self.play(env.hc.animate.scale(env.hc_scale), run_time=0.5)
        self.play(env.hc.animate.move_to((env.h_pos)).shift((-4,0,0)),
                  run_time=0.2)
        
        # house
        scene_home = []
        for h in sim.houses:
            pos = env.transform2frame(h.x, h.y)
            scene_home.append(SVGMobject('svgs/house.svg',
                              stoke_color=BLUE_A).scale(0.2).move_to(pos))
            self.play(FadeIn(scene_home[-1]), run_time=0.1)
        home = scene_home[-1]
        # business
        scene_office = []
        for b in sim.business:
            pos = env.transform2frame(b.x, b.y)
            scene_office.append(SVGMobject('svgs/office.svg').scale(0.2).move_to(pos))
            self.play(FadeIn(scene_office[-1]), run_time=0.1)
        office = scene_office[-1]
        # person
        p_child, p, p_old = p_v = VGroup(
            SVGMobject("svgs/child.svg", stroke_color=WHITE).scale(0.8),
            SVGMobject("svgs/man.svg", stroke_color=WHITE),
            SVGMobject("svgs/old-man.svg", stroke_color=WHITE),   
        ).arrange(RIGHT, buff=1).to_edge(UR, buff=0.5).to_edge(RIGHT, buff=1)
        self.play(FadeIn(p_v))
        # age
        p_child_t = Text('age < 16', font=font, font_size=fontsize_s).next_to(p_child, UP, buff=0.2)
        self.play(Write(p_child_t), run_time=0.5)
        p_t = Text('16 < age < 65', font=font, font_size=fontsize_s).next_to(p, UP, buff=0.2)
        self.play(Write(p_t), run_time=0.5)
        p_old_t = Text('age > 65', font=font, font_size=fontsize_s).next_to(p_old, UP, buff=0.2)
        self.play(Write(p_old_t), run_time=0.5)
        age_text = SingleStringTex(r'age \in \beta(2,5)',
                                   font=font,
                                   font_size=fontsize_m,
                                   color=YELLOW_B).next_to(p, BOTTOM, buff=0.1)
        self.play(Write(age_text), run_time=1)
        temp_f = FunctionGraph(lambda x: beta.pdf(x, 2, 5), x_range=(0, 1, 0.1),
                               stroke_color=YELLOW_B).scale((4,1,1))
        arrow_x = Arrow(start=temp_f.get_left(),
                        end=temp_f.get_left() + np.array(
                            [temp_f.get_width()+0.5,0,0])).shift((-0.2, -temp_f.get_height()/2,0 ))
        temp_x_label = Text("年龄", font=font, font_size=fontsize_s).next_to(
            arrow_x, BOTTOM, buff=0.05).shift((arrow_x.get_length()/2, 0, 0))
        arrow_y = Arrow(start=temp_f.get_left(),
                        end=temp_f.get_left() + np.array(
                            [0, temp_f.get_height()+0.6,0])).shift((0, -temp_f.get_height()/2-0.2,0 ))
        temp_y_label = Text("比例", font=font, font_size=fontsize_s).next_to(
            arrow_y, TOP, buff=0.05)
        beta_graph = VGroup(temp_f, arrow_x, arrow_y, temp_x_label, temp_y_label).next_to(age_text, BOTTOM, buff=0.01)
        self.play(Write(VGroup(temp_x_label, arrow_x)))
        self.play(Write(VGroup(temp_y_label, arrow_y)))
        self.play(ShowCreation(temp_f))

        self.play(FadeOut(age_text), FadeOut(beta_graph))
        
        # infection status
        t_s = Text('S', font=font, font_size=fontsize_l,
                   base_color=WHITE)
        t_r = Text('R', font=font, font_size=fontsize_l,
            base_color=GREEN)
        t_i = Text('I', font=font, font_size=fontsize_l,
            base_color=RED)
        t_m = Text('模型', font=font, font_size=fontsize_l,
            base_color=WHITE)
        i = 0
        texts = []
        for tc, te, c, t in zip(['易感者', '移除者（痊愈/免疫）', '感染者'],
                             ['Susceptible', 'Recovering', 'Infected'],
                             [RED, GREEN, WHITE][::-1],
                             [t_s, t_r, t_i]):
            for m in p_v.submobjects:
                m.set_stroke(c)
            textc = Text(tc, font=font, font_size=fontsize_s,
                        base_color=c).next_to(p_v, BOTTOM, buff=0.1)
            texte = Text(te, font=font, font_size=fontsize_s,
                        base_color=c).next_to(textc, BOTTOM, buff=0.02)
            texts.append(VGroup(textc, texte))
            self.play(Write(textc), Write(texte))
            self.play(textc.animate.shift((-2,-i*1,0)), texte.animate.shift((-2,-i*1,0)))
            i += 1
        t_sir = VGroup(t_s, t_r, t_i, t_m).arrange(RIGHT, buff=0.2).shift((5,0,0))
        self.play(Write(t_sir))
        self.play(t_sir.animate.shift((-1.5, -2.5, 0)))
        # # S -> I
        p_s = p.copy().shift((0.5, -2.5, 0))
        p_s.set_stroke(WHITE)
        self.play(FadeIn(p_s))
        p_i = p.copy().next_to(p_s, RIGHT, buff=0.2)
        p_i.set_stroke(RED)
        self.add(p_i)
        arrow_s2i = CurvedArrow(start_point=texts[0].get_left(),
                                end_point=texts[2].get_left(),
                                radius=2, buff=-1).shift((-0.5,0,0))
        self.play(p_i.animate.shift((-0.5, 0, 0)))
        self.wait(0.5)
        p_s.set_stroke(RED)
        self.play(Write(arrow_s2i))
        self.play(FadeOut(p_i))
        # Infected requiring hospotalization
        env.h.scale(4)
        env_pos = env.h.get_center().copy()
        self.play(env.h.animate.move_to(p_i.get_right() + np.array([0.8,0,0])))
        # arrow_i2h = CurvedArrow(start_point=p_s.get_right(),
        #                         end_point=p_i.get_right(),
        #                         radius=2, buff=-1)
        i2h_p_text = Tex('P', color=BLUE_B, font=font, font_size=fontsize_s).next_to(p_s, TOP, buff=0.1).shift((0.6,-0.5,0))
        self.play(Write(i2h_p_text))
        i2h_p_bar = BarChart(age_hospitalization_probs,
                             bar_colors=[WHITE, BLUE_B],
                             max_value=np.max(age_hospitalization_probs)+0.1,
                             ).scale((0.5,0.5,1)).next_to(p_s, BOTTOM, buff=0.1).shift((0.5,0,0))
        i2h_p_bar_x_label = Text("年龄", font=font, font_size=fontsize_s).next_to(i2h_p_bar, BOTTOM, buff=0.01)
        self.play(ShowCreation(i2h_p_bar),
                  Write(i2h_p_bar_x_label),
                  t_sir.animate.shift((-2,0,0)),
                  i2h_p_text.animate.move_to(i2h_p_bar.get_center()))
        self.wait()
        env.h.scale(1/4)
        self.play(FadeOut(i2h_p_bar),
                  FadeOut(i2h_p_text),
                  FadeOut(i2h_p_bar_x_label),
                  t_sir.animate.shift((2,0,0)),
                  env.h.animate.move_to(env_pos))
        
        # # I -> R or Death
        clock = Clock().next_to(p_s, RIGHT, buff=0.2).scale(0.5)
        self.play(FadeIn(clock))
        self.play(ClockPassesTime(clock), run_time=1)
        arrow_i2r = CurvedArrow(start_point=texts[2].get_right(),
                                end_point=texts[1].get_right(),
                                radius=2, buff=0.5)
        p_s.set_stroke(GREEN)
        self.play(Write(arrow_i2r))
        self.wait()
        p_s.set_stroke(RED)
        self.play(ClockPassesTime(clock), run_time=1)
        t_d = Text("死亡（Death）", font=font, font_size=fontsize_s,
                   base_color=GREY).next_to(texts[2], RIGHT, buff=2).shift((0,-0.2,0))
        arrow_i2d = CurvedArrow(start_point=texts[2].get_right(),
                                end_point=t_d.get_left())
        p_s.set_stroke(GREY)
        self.play(Write(arrow_i2d), FadeIn(t_d))

        i2d_p_text = Tex('P', color=GREY, font=font, font_size=fontsize_s).next_to(p_s, TOP, buff=0.1).shift((0.6,-0.5,0))
        self.play(Write(i2d_p_text))
        i2d_p_bar = BarChart(age_death_probs,
                             bar_colors=[WHITE, GREY],
                             max_value=np.max(age_death_probs)+0.1,
                             ).scale((0.5,0.4,1)).next_to(p_s, BOTTOM, buff=0.2).shift((0.5,0,0))
        i2d_p_bar_x_label = Text("年龄", font=font, font_size=fontsize_s).next_to(i2d_p_bar, BOTTOM, buff=0.01)
        self.play(ShowCreation(i2d_p_bar),
                  t_sir.animate.shift((-2,0,0)),
                  Write(i2d_p_bar_x_label),
                  i2d_p_text.animate.move_to(i2d_p_bar.get_center()))
        self.wait()
        self.play(FadeOut(i2d_p_bar),
                  FadeOut(i2d_p_text),
                  FadeOut(i2d_p_bar_x_label),
                  t_sir.animate.shift((2,0,0)))
        self.wait()
        for a in p_v:
            a.set_stroke(WHITE)
        self.play(FadeOut(VGroup(arrow_i2d, arrow_i2r, arrow_s2i,
                                 p_child_t, p_t, p_old_t,
                                 clock, p_s, t_sir, t_d,*texts)))
        
        # economic
        # social stratum
        self.play(p_t.animate.scale(1.2))
        p_social_s = []
        t_social_s = []
        social_s_name = ['贫穷','温饱','小康','富有','土豪']
        for i in range(5):
            p_social_s.append(p.copy().scale(0.5))
            t_social_s.append(Text(social_s_name[i], font=font, font_size=fontsize_s).move_to(
                        p.get_center() + np.array([-3+i*1.2,-1.5,0])))
            
        for i, gv in enumerate(p_social_s):
            self.play(gv.animate.shift((-3+i*1.2,-2.2, 0)),
                      run_time=0.3)
            self.play(Write(t_social_s[i]))
            
        # self.play(ShowCreation(VGroup(*p_social_s)))
        # lorenz_curve
        lorenz_x_line = Line(start=p_social_s[0].get_left(),
                            end=p_social_s[-1].get_right()).next_to(
                                p_social_s[2], BOTTOM
                            ).shift((0, -1, 0)).scale(1.2)
        lorenz_y_text = Text("收入&支出",
                             font=font, font_size=fontsize_s,
                             color=BLUE_A).next_to(
                                 p_social_s[0].get_left()
                             ).shift([-1.2, -1, 0])
        self.play(Write(lorenz_x_line),
                  Write(lorenz_y_text))
        lorenz_bars = []
        for num, vg in zip(lorenz_curve, p_social_s):
            lorenz_bars.append(
                Rectangle(
                    width=0.6,
                    height=num*2,
                    fill_color=BLUE_A,
                    fill_opacity=0.8,
                    stroke_color=BLUE_A,
                ).move_to(vg.submobjects[0].get_center()).shift(
                    (0, lorenz_x_line.get_center()[1] - vg.submobjects[0].get_center()[1] + num, 0)
                )
            )
        lorenz_text = Text("社会财富分配符合洛伦兹曲线",
                           font=font,
                           font_size=fontsize_m,
                           color=BLUE_A).next_to(lorenz_x_line, BOTTOM, buff=0.2)
        
        for lb in lorenz_bars:
            lb.stretch_about_point(0.1, 1, lb.get_bottom())
            self.play(lb.animate.stretch_about_point(10, 1, lb.get_bottom()),
                      run_time=0.5)
        # self.play(Write(VGroup(*lorenz_bars)), run_time=3)
        self.play(Write(lorenz_text))
        self.wait()
        self.play(FadeOut(VGroup(
            *lorenz_bars, lorenz_text,
            lorenz_x_line, lorenz_y_text, *p_social_s, *t_social_s
        )))
        # lorenz_graph = FunctionGraph(
        #     lambda x: np.cumsum(lorenz_curve)[int(x)],
        #     x_range=(0,4,1) 
        # )
        # self.play(ShowCreation(lorenz_graph))
        self.wait()
        
        off_init_pos = office.get_center().copy()
        t_eco = Text("购买产品和服务", font=font,
                     font_size=fontsize_m).to_edge(BOTTOM, buff=0.2).shift((3,0,0))
        self.play(Write(t_eco))
        self.play(office.animate.scale(4), run_time=0.2)
        self.play(office.animate.move_to((2,0,0)))
        for agent in [p, p_child, p_old]:
            p_init = agent.get_center().copy()
            x, y = np.random.normal(0.0, 0.5, 2)
            self.play(agent.animate.move_to(office.get_center() + np.array([x,y,0])))
            product = SVGMobject('svgs/box.svg').scale(0.3).move_to(office.get_center(),
                                                                    aligned_edge=RIGHT)
            money = SVGMobject('svgs/money.svg').scale(0.3).move_to(agent.get_center(),
                                                                    aligned_edge=LEFT)
            self.play(FadeIn(money), FadeIn(product))
            self.play(money.animate.move_to(office.get_center()),
                    product.animate.move_to(agent.get_center()))
            self.play(FadeOut(money),
                      FadeOut(product))
            self.play(agent.animate.move_to(p_init), run_time=0.2)
        self.play(office.animate.scale(1/4), run_time=0.2)
        self.play(office.animate.move_to(off_init_pos), run_time=0.5)

        # routine
        t_sleep = Text("睡觉", font=font,
                      font_size=fontsize_s)
        t_work = Text("搬砖", font=font,
                      font_size=fontsize_s)
        t_walk = Text("自由活动", font=font,
                      font_size=fontsize_s)
        self.play(FadeOut(t_eco))
        t_routine = Text("日常活动（工作日）", font=font,
                          font_size=fontsize_m).to_edge(BOTTOM, buff=0.2).shift((3,0,0))
        self.play(Write(t_routine))
        t_0_8 = Text("00:00~08:00", font=font,
                      font_size=fontsize_s).move_to((0, 1, 0))
        self.play(FadeIn(t_0_8))
        self.play(Write(t_sleep.next_to(t_0_8, RIGHT).shift((2.5,0,0))))
        
        t_8_12 = Text("08:00~12:00", font=font,
                      font_size=fontsize_s).move_to((0, 0.2, 0))
        self.play(FadeIn(t_8_12))
        self.play(Write(t_walk.copy().next_to(t_8_12, RIGHT).shift((0.2,0,0))))
        self.play(Write(t_work.copy().next_to(t_8_12, RIGHT).shift((2.5,0,0))))
        self.play(Write(t_walk.copy().next_to(t_8_12, RIGHT).shift((4.2,0,0))))
        t_12_14 = Text("12:00~14:00", font=font,
                       font_size=fontsize_s).move_to((0, -0.6, 0))
        self.play(FadeIn(t_12_14))
        self.play(Write(t_walk.copy().next_to(t_12_14, RIGHT).shift((2.5,0,0))))
        t_14_18 = Text("14:00~18:00", font=font,
                      font_size=fontsize_s).move_to((0, -1.4, 0))
        self.play(FadeIn(t_14_18))
        self.play(Write(t_walk.copy().next_to(t_14_18, RIGHT).shift((0.2,0,0))))
        self.play(Write(t_work.copy().next_to(t_14_18, RIGHT).shift((2.5,0,0))))
        self.play(Write(t_walk.copy().next_to(t_14_18, RIGHT).shift((4.2,0,0))))

        t_18_24 = Text("18:00~24:00", font=font,
                      font_size=fontsize_s).move_to((0, -2.2, 0))
        self.play(FadeIn(t_18_24))
        self.play(Write(t_walk.copy().next_to(t_18_24, RIGHT).shift((2.5,0,0))))
        t_routine_ = Text("周末除了睡觉就是自由活动", font=font,
                          font_size=fontsize_m).to_edge(BOTTOM, buff=0.2).shift((3,0,0))
        self.play(FadeTransform(t_routine, t_routine_))
        self.play(FadeOut(t_routine_), run_time=2)
        for a in self.mobjects:
            if isinstance(a, Text):
                self.remove(a)
        
        # monthly accounting
        t_month = Text("月结算", font=font,
                       font_size=fontsize_m).to_edge(BOTTOM, buff=0.2).shift((3.5,0,0))
        self.play(Write(t_month))
        home_pos_init = home.get_center().copy()
        self.play(FadeOut(VGroup(p_child, p_old)),
                  p.animate.scale(0.5),
                  env.gb.animate.move_to(np.array([p.get_center()[0], 0, 0])),
                  env.hc.animate.move_to((1, -1, 0)),
                  home.animate.move_to(p.get_center() - np.array([0, 5, 0])),
                  office.animate.move_to((6, 0, 0))
                  )
        arrow_h2g = CurvedArrow(start_point=home.get_top(),
                                end_point=env.gb.get_bottom())
        t_tax = Text("纳税", font=font,
                       font_size=fontsize_s).next_to(arrow_h2g, ORIGIN).shift((-0.2,0,0))
        self.play(Write(VGroup(arrow_h2g, t_tax)))
        
        arrow_b2g = CurvedArrow(start_point=office.get_left(),
                                end_point=env.gb.get_right())
        self.play(Write(VGroup(arrow_b2g,
                               t_tax.copy().next_to(arrow_b2g, ORIGIN).shift((0,0.5,0)))))
        
        arrow_b2a = CurvedArrow(start_point=office.get_top(),
                                end_point=p.get_right())
        t_salary = Text("薪酬", font=font,
                       font_size=fontsize_s).next_to(arrow_b2a, ORIGIN).shift((0.3,0.3,0))
        self.play(Write(VGroup(arrow_b2a,t_salary)))       
        
        arrow_g2a = CurvedArrow(start_point=env.gb.get_top(),
                                end_point=p.get_bottom())
        t_allow = Text("补贴（无工作/无家）", font=font,
                       font_size=fontsize_s).next_to(arrow_g2a, ORIGIN).shift((-1,0.0,0))
        self.play(Write(VGroup(arrow_g2a,t_allow)))
        
        arrow_g2h = CurvedArrow(start_point=env.gb.get_left(),
                                end_point=env.hc.get_top())
        t_allow1 = Text("公共医疗", font=font,
                       font_size=fontsize_s).next_to(arrow_g2h, ORIGIN).shift((0,0.8,0))
        self.play(Write(VGroup(arrow_g2h,t_allow1)))
        
        arrow_g2b = CurvedArrow(start_point=env.gb.get_right(),
                                end_point=office.get_left())
        t_public = Text("公共开销", font=font,
                       font_size=fontsize_s).next_to(arrow_g2b, ORIGIN).shift((0,-0.5,0))
        self.play(Write(VGroup(arrow_g2b,t_public)))
        
        rm = []
        for a in self.mobjects:
            if isinstance(a, VGroup):
                for a_ in a:
                    if (isinstance(a_, Text)) or (isinstance(a_, CurvedArrow)):
                        rm.append(a_)
                
        self.play(FadeOut(VGroup(*rm)))
        
        # move back  all elements to the environment
        self.play(
            home.animate.move_to(home_pos_init),
            env.gb.animate.move_to(env.transform2frame(sim.government.x, sim.government.y)),
            env.hc.animate.move_to(env.transform2frame(sim.healthcare.x, sim.healthcare.y)),
            office.animate.move_to(off_init_pos),
            FadeOut(p),
            FadeOut(t_month)
        )
        
        # add all the person:
        persons = []
        for i, p in enumerate(sim.population):
            if p.age <= 10:
                file = "svgs/child.svg"
                scale = 0.06
            elif p.age <= 65:
                file = "svgs/man.svg"
                scale = 0.1
            else:
                file = "svgs/old-man.svg"
                scale = 0.1
            
            # persons_svg = SVGMobject(
            #     file,
            #     stroke_color=person_status_color[p.status.name]).move_to(
            #         (env.world_pos_offset_x, env.world_pos_offset_y, 0)
            # )
            persons.append(SVGMobject(
                file,
                stroke_color=person_status_color[p.status.name]).move_to(env.boundary_box.get_center()))
            play_time = 1 if i < 1 else 0.1
            self.play(FadeIn(persons[-1]), run_time=play_time)
            self.play(persons[-1].animate.scale(scale), run_time=play_time)
            pos = env.transform2frame(p.x, p.y)
            self.play(persons[-1].animate.move_to(pos), run_time=play_time)
        
        # time label
        _, num_month, _, num_day, _, num_hour, _ = time_label = VGroup(
            Text('第', font=font, font_size=fontsize_m),
            DecimalNumber(10, font_size=fontsize_m-4, num_decimal_places=0,
                          color=BLUE_B, fill_opacity=1),
            Text('月', font=font, font_size=fontsize_m),
            DecimalNumber(10, font_size=fontsize_m-4, num_decimal_places=0,
                          color=BLUE_B, fill_opacity=1),
            Text('日', font=font, font_size=fontsize_m),
            DecimalNumber(10, font_size=fontsize_m-4, num_decimal_places=0,
                          color=BLUE_B, fill_opacity=1),
            Text('小时', font=font, font_size=fontsize_m),
        )
        f_always(num_month.set_value, lambda: sim.num_month)
        f_always(num_day.set_value, lambda: sim.num_day - sim.num_month*30)
        f_always(num_hour.set_value, lambda: sim.iteration - sim.num_day*24)
        time_label.arrange(RIGHT, center=False).to_edge(UP, buff=0.5).to_edge(LEFT, buff=1.0)
        clock.scale(0.5)
        self.play(ShowCreation(time_label),
                  clock.animate.next_to(time_label, RIGHT))
        env.world_pos_offset_y = -1
        
        quarantine_zone = Square(side_length=env.hc.get_height(),
                                 stroke_color=RED,
                                 fill_color=RED,
                                 fill_opacity=0.4,
                                 stroke_width=2).move_to(
                                     env.transform2frame(sim.quarantine_x,
                                                         sim.quarantine_y)
                                 )
        quarantine_text = Text("隔离区", font=font, font_size=fontsize_s,
                               color=RED).next_to(quarantine_zone, BOTTOM, buff=0.01)
        quarantine_zone_shown = False
        # always(clock.hour_hand.set_angle,
        #        np.pi/2 - (sim.iteration - sim.num_day*24)/6*np.pi)
        # dynamic
        for inv_i, inv in enumerate(intervention_dic.keys()):
            if inv == 'eco_baseline':
                t_ = '无疫情时的经济'
            else:
                t_ = '[{}]'.format(intervention_dic[inv])
                    
            if inv_i == 0:
                t_intervention = Text(t_,
                                font=font, font_size=fontsize_m, 
                                base_color=LIGHT_BROWN).next_to(time_label, BOTTOM, buff=0.1).shift((0.2,0,0))
                self.play(Write(t_intervention),
                          VGroup(*persons).animate.shift((0, -1, 0)),
                          VGroup(*scene_office).animate.shift((0, -1, 0)),
                          VGroup(*scene_home).animate.shift((0, -1, 0)),
                          env.gb.animate.shift((0,-1,0)),
                          env.hc.animate.shift((0,-1,0)),
                          env.boundary_box.animate.shift((0,-1,0)),
                          run_time=2)
                # for mob in simulation_scene_mob:
                #     self.remove(mob)
            else:
                # get new intervention text
                t_intervention_n = Text(t_,
                                        font=font, font_size=fontsize_m,
                                        base_color=LIGHT_BROWN).move_to(t_intervention.get_center())
                self.play(ReplacementTransform(t_intervention, t_intervention_n))
                t_intervention = t_intervention_n
            
            if ("quarantine" in inv) and ("home" not in inv):
                if not quarantine_zone_shown:
                    self.play(Write(VGroup(quarantine_zone, quarantine_text)))
                    quarantine_zone_shown = True
            else:
                if quarantine_zone_shown:
                    self.play(FadeOut(VGroup(quarantine_zone, quarantine_text)))
                    quarantine_zone_shown = False
                
            previous_dots_p = []
            previous_dots_p_eco = []
            # g_wb_stretch = 1.0
            plot_mobjects = []
            simulation_para = get_scenario_parameters(inv)
            sim.intervention_initialize(**simulation_para)
            for t in range(time_out):
                sim.run()
                clock.hour_hand.set_angle(np.pi/2 - (sim.iteration - sim.num_day*24)/6*np.pi)
                clock.minute_hand.set_angle(np.pi/2 + np.random.rand(1)[0]*0.05)
                pos = [env.transform2frame(p.x, p.y) for p in sim.population]
                for pg, p in zip(persons, sim.population):
                    pg.set_stroke(color=person_status_color[p.status.name])
                # update plot everyday - every 24 iterations
                if sim.iteration % 24 == 0:
                    if sim.num_day < 1:
                        # draw coordinates
                        axes_sir = Axes(
                            x_range=(0, int(time_out/24), 5),
                            y_range=(0, 1.1, 0.1),
                            height=2,
                            width=7,
                            axis_config={
                                "include_tip": True,
                                "stroke_width": 0.8,
                                "tip_config": {
                                    "width": 0.1,
                                    "length": 0.1,
                                    },
                                "tip_size":0.04
                            }
                        ).to_edge(RIGHT, buff=0.1).to_edge(UP, buff=0.4)
                        axes_sir.add_coordinate_labels(
                            font_size=12,
                            num_decimal_places=1
                        )
                        t_axes_sir = Text("疫情发展",font=font, font_size=fontsize_s).next_to(
                            axes_sir, TOP, buff=0.02)
                        t_sir_x_label = Text("天数",
                        font=font, font_size=12).move_to(
                            axes_sir.c2p(int(time_out/24), -0.05))
                        axes_eco = Axes(
                            x_range=(0, int(time_out/24), 5),
                            y_range=(0, 0.9, 0.1),
                            height=2,
                            width=7,
                            axis_config={
                                "include_tip": True,
                                "stroke_width": 0.8,
                                "tip_config": {
                                    "width": 0.1,
                                    "length": 0.1,
                                    },
                                "tip_size":0.04
                            }
                        ).to_edge(RIGHT, buff=0.1).to_edge(BOTTOM, buff=0.06)
                        t_eco_x_label = Text("天数",
                        font=font, font_size=12).move_to(
                            axes_eco.c2p(int(time_out/24),-0.05))
                        axes_eco.add_coordinate_labels(
                            font_size=12,
                            num_decimal_places=1
                        )
                        t_axes_eco = Text("经济发展",font=font, font_size=fontsize_s).next_to(
                            axes_eco, TOP, buff=0.01)
                        self.play(ShowCreation(VGroup(axes_sir, t_axes_sir, t_sir_x_label)), run_time=0.5)
                        y_label_sir = Text("SIR人口占比", font=font, font_size=14).next_to(
                            axes_sir.get_y_axis(), TOP, buff=0.1
                        ).shift((0, -0.4, 0))
                        self.play(Write(y_label_sir))
                        self.play(ShowCreation(VGroup(axes_eco, t_axes_eco, t_eco_x_label)), run_time=0.5)
                        y_label_eco = Text("财富占比", font=font, font_size=14).next_to(
                            axes_eco.get_y_axis(), TOP, buff=0.1
                        ).shift((0, -0.4, 0))
                        self.play(Write(y_label_eco))
                        
                    data = sim.get_statistics('all').copy()
                    for i, s in enumerate(Status):
                        c = person_status_color[s.name]
                        dot = Dot(radius=0.1, fill_color=c).move_to(
                            axes_sir.c2p(sim.num_day, data[s.name])
                        )
                        self.play(FadeIn(dot), run_time=0.1)
                        self.play(dot.animate.scale(0.2), run_time=0.2)
                        plot_mobjects.append(dot)
                        if sim.num_day < 1:
                            previous_dots_p.append(dot.get_center())
                        else:
                            line = Line(
                                start=previous_dots_p[i],
                                end=dot.get_center(),
                                stroke_width=1,
                                stroke_color=c)
                            self.play(ShowCreation(line),run_time=0.2)
                            plot_mobjects.append(line)
                            previous_dots_p[i] = dot.get_center()
                    for i, s in enumerate(['Person', 'Business', 'Government']):
                        c = wealth_type_color[s]
                        dot = Dot(radius=0.1, fill_color=c).move_to(
                            axes_eco.c2p(sim.num_day, data['W_'+s])
                        )
                        self.play(FadeIn(dot), run_time=0.1)
                        self.play(dot.animate.scale(0.2), run_time=0.2)
                        plot_mobjects.append(dot)
                        if sim.num_day < 1:
                            previous_dots_p_eco.append(dot.get_center())
                        else:
                            line = Line(
                                start=previous_dots_p_eco[i],
                                end=dot.get_center(),
                                stroke_color=c,
                                stroke_width=1)
                            self.play(ShowCreation(line),run_time=0.2)
                            plot_mobjects.append(line)
                            previous_dots_p_eco[i] = dot.get_center()
                    # s_temp = data['W_Government']/(sim.public_gdp_share)
                    # env.g_wb.stretch_about_point(s_temp/g_wb_stretch,
                    #                             1, env.g_wb.get_bottom())
                    env.g_wb.set_height(env.g.get_height()*data['W_Government']/(sim.public_gdp_share),
                                        stretch=True, about_point=env.g_wb.get_bottom())
                    # g_wb_stretch = s_temp/g_wb_stretch
                anim_pos = [ApplyMethod(person.move_to, _pos) for person,
                            _pos in zip(persons, pos)]
                self.play(*anim_pos, run_time=0.2)
            
            # end of simulation
            if inv_i == 0:
                axes_comparison = Axes(
                    x_range=(0.4, 0.6, 0.1),
                    y_range=(0, 0.3, 0.1),
                    height=2,
                    width=7,
                    axis_config={
                        "include_tip": True,
                        "stroke_width": 0.8,
                        "tip_config": {
                            "width": 0.1,
                            "length": 0.1,
                            },
                        "tip_size":0.01
                        }
                    ).to_edge(RIGHT, buff=0.1).to_edge(BOTTOM, buff=0.72)
                axes_comparison.y_axis.move_to(axes_comparison.c2p(0.4, 0), aligned_edge=BOTTOM)
                axes_comparison.add_coordinate_labels(
                    font_size=12,
                    num_decimal_places=1
                )
                t_com_y_label = Text("疫情死亡",
                                     font=font, font_size=12).move_to(
                                      axes_comparison.c2p(0, 0.32))
                t_com_x_label = Text("商业财富占比",
                        font=font, font_size=12).move_to(
                        axes_comparison.c2p(0.48, -0.03))
                
                t_axes_com = Text("防疫措施比较",
                                  font=font, font_size=fontsize_s).next_to(
                                      axes_comparison, TOP, buff=0.01)
                self.play(ShowCreation(axes_comparison), Write(t_axes_com),
                          Write(t_com_x_label),Write(t_com_y_label))
            
            # env.g_wb.stretch_about_point(1/g_wb_stretch,
            #                              1, env.g_wb.get_bottom())
            data = sim.get_statistics('all').copy()

            dot_b = Dot(radius=0.1,
                        fill_color=wealth_type_color[AgentType.Business.name]).move_to(
                axes_eco.c2p(sim.num_day, data['W_Business']))
            self.play(FadeIn(dot_b))
            self.play(dot_b.animate.scale(0.2))
            self.play(dot_b.animate.move_to(
                axes_comparison.c2p(data['W_Business']-0.4, 0)
            ))
            
            if inv == 'eco_baseline':
                eco_basline = DashedLine(start=dot_b.get_center(),
                                         end=dot_b.get_center() + np.array([0, axes_comparison.get_height()*0.8, 0]),
                                         stroke_color=GREY_BROWN)
                eco_basline_e = Text("无疫情经济基线", font=font,
                                     font_size=16, color=GREY_BROWN).next_to(
                                         eco_basline, RIGHT, buff=0.12).shift((0, eco_basline.get_height()/2, 0))
                self.play(Write(eco_basline))
                self.play(Write(eco_basline_e), FadeOut(dot_b))
            else:
                dot_d = Dot(radius=0.1,
                            fill_color=person_status_color[Status.Death.name]).move_to(
                    axes_sir.c2p(sim.num_day, data['Death']))
                self.play(FadeIn(dot_d))
                self.play(dot_d.animate.scale(0.2))
                self.play(dot_d.animate.move_to(
                    axes_comparison.c2p(0, data['Death'])
                ))
                s_ = dot_d.get_center()
                e_ = s_ + np.array([dot_b.get_center()[0] - dot_d.get_center()[0],0,0])
                line_x = DashedLine(start=s_, end=e_,
                                    stroke_color=person_status_color[Status.Death.name],
                                    stroke_width=2)
                s_ = dot_b.get_center()
                e_ = s_ + np.array([0, dot_d.get_center()[1] - dot_b.get_center()[1], 0])
                line_y = DashedLine(start=s_, end=e_,
                                    stroke_color=wealth_type_color[AgentType.Business.name],
                                    stroke_width=2)
                self.play(Write(line_x), Write(line_y))
                dot = Triangle(stroke_color=DARK_BROWN,
                            fill_color=LIGHT_BROWN,
                            fill_opacity=0.8).scale(0.2).move_to(
                                axes_comparison.c2p(data['W_Business']-0.4, data['Death']))
                dot_text = Text(t_[1:-1],
                                font=font,
                                font_size=12,
                                base_color=LIGHT_BROWN).next_to(dot, TOP, buff=0.01)
                self.play(Write(dot))
                self.play(Write(dot_text), FadeOut(VGroup(dot_b, dot_d, line_x, line_y)))
                self.wait(2)
            if inv_i < len(intervention_dic) - 1:
                # clear plot for next simulation
                for mb in plot_mobjects:
                    self.remove(mb)

class Test(Scene):
    def construct(self):
        rec = Rectangle()
        self.play(FadeIn(rec))
        self.wait()
        self.play(rec.animate.set_height(4, stretch=True, about_point=rec.get_bottom()))
        self.wait()
        self.play(rec.animate.set_height(1, stretch=True, about_point=rec.get_bottom()))
        # axes_comparison = Axes(
        #             x_range=(0.3, 0.6, 0.1),
        #             y_range=(0, 0.3, 0.1),
        #             height=2,
        #             width=7,
        #             axis_config={
        #                 "include_tip": True,
        #                 "stroke_width": 0.5
        #                 }
        #             ).to_edge(RIGHT, buff=0.1).to_edge(BOTTOM, buff=0.72)
        # axes_comparison.add_coordinate_labels(
        #     font_size=12,
        #     num_decimal_places=1
        # )
        # axes_comparison.y_axis.move_to(axes_comparison.c2p(0.3, 0), aligned_edge=BOTTOM)
        # t_axes_com = Text("防疫措施比较",
        #                     font=font, font_size=fontsize_s).next_to(
        #                         axes_comparison, TOP, buff=0.01)
        # self.play(ShowCreation(axes_comparison), Write(t_axes_com))
        # dot_b = Dot(radius=0.1)
        # self.play(FadeIn(dot_b))
        # self.play(dot_b.animate.move_to(
        #     axes_comparison.c2p(0, 0)
        # ))
        # temp_axes = Axes(
        #     x_range = (0, 1, 0.1),
        #     y_range=(0, 1, 0.1)
        # )
        # temp_f = temp_axes.get_graph(lambda x: beta.pdf(x, 2, 5), x_range=(0, 1, 0.1))
        # temp_f = FunctionGraph(lambda x: beta.pdf(x, 2, 5), x_range=(0, 1, 0.1)).scale((4,1,1))
        # arrow_x = Arrow(start=temp_f.get_left(),
        #                 end=temp_f.get_left() + np.array(
        #                     [temp_f.get_width()+0.5,0,0])).shift((-0.2, -temp_f.get_height()/2,0 ))
        # temp_x_label = Text("年龄", font=font, font_size=fontsize_s).next_to(
        #     arrow_x, BOTTOM, buff=0.05).shift((arrow_x.get_length()/2, 0, 0))
        # arrow_y = Arrow(start=temp_f.get_left(),
        #                 end=temp_f.get_left() + np.array(
        #                     [0, temp_f.get_height()+0.6,0])).shift((0, -temp_f.get_height()/2-0.2,0 ))
        # temp_y_label = Text("比例", font=font, font_size=fontsize_s).next_to(
        #     arrow_y, TOP, buff=0.05)
        # self.play(Write(VGroup(temp_x_label, arrow_x)))
        # self.play(Write(VGroup(temp_y_label, arrow_y)))
        # self.play(ShowCreation(temp_f))
        

if __name__ == "__main__":
    # os.system("manimgl {} Video".format(__file__))
    os.system('powershell /c "manimgl {} Test'.format(__file__))