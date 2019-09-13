#!/usr/bin/env python
# coding=utf-8
# author: Charles Zheng
# create date: 2019/9/13
"""
欧冠小组抽签的几个回避原则：
（1）同联赛球队之间不同组
（2）俄罗斯与乌克兰球队不同组
（3）特定匹配的球队，为了安排在不同比赛日，不能被分到同一半区
2018-2019赛季小组赛被匹配的球队包括：

Real Madrid & Barcelona
Atlético Madrid & Valencia
Bayern & Dortmund
Man. City & Tottenham
Juventus & Internazionale Milano
Paris & Lyon
Lokomotiv Moskva & CSKA Moskva
Porto & Benfica
Man. United & Liverpool
Napoli & Roma
Schalke & Hoffenheim
Ajax & PSV Eindhoven


ESP：Barcelona（1），Real Madrid（1），Atletico Madrid（1），Valencia（3），共4只
GER：Bayern（1），Dortmund（2），Schalke（3），Hoffenheim（4），共4只
ENG：Man City（1），Man United（2），Tottenham（2），Liverpool（3），共4只
ITA：Juventus（1），Napoli（2），Roma（2），Inter Milano（4），共4只
FRA：Paris（1），Lyon（3），Monaco（3），共3只
RUS：Lokomotiv（1），CSKA（3），共2只
POR：Porto（2），Benfica（2），共2只
UKR：Donetsk（2），共1只
NED：Ajax（3），PSV（3），共2只
CZE：Plzen（4），共1只
BEL：Brugge（4），共1只
TUR：Galatasaray（4），共1只
SUI：Young Boys（4），共1只
SRB：Crvena zvezda（4），共1只
GRE：AEK Athens（4），共1只
"""
import random
import pandas as pd
from copy import deepcopy
from itertools import combinations
import os


class TeamList(object):
    """
    Read a config file and initialize teams information.
    """

    def __init__(self, config_file=None):
        """

        :param config_file: team information file
        """
        self.path = config_file
        self.file_data = pd.read_excel(config_file, header=0)

    @property
    def teams_info(self):
        """
        read the config file and return dict data of teams
        :return: dict data of teams
        """
        fileData = self.file_data
        teams_dict = fileData.set_index('clubs').T.to_dict()
        return teams_dict

    @property
    def all_leagues(self):
        """
        leagues that the participant teams belong to
        :return:
        """
        teams = self.file_data
        return set(list(teams['league']))

    @property
    def ranks(self):
        """

        :return:
        """
        teams = self.file_data
        return set(list(teams['rank']))

    @property
    def all_team_names(self):
        """

        :return:
        """
        return list(self.file_data['clubs'])

    def rank_teams(self, rank):
        """
        某一档次的所有球队名称
        :param rank: 所属档次
        :return:某一档次的所有球队名称
        """
        df = self.file_data
        return list(df[df['rank'] == rank]['clubs'].values)

    # @staticmethod
    # def initialize_all_team_objs(teamNames):
    #     team_obj_dict = {}
    #     for name in teamNames:
    #         team_obj_dict[name] = Team(name)
    #     return team_obj_dict


DATA_FILE = os.path.join(os.getcwd(), 'teams.xlsx')
teamList = TeamList(config_file=DATA_FILE)
teamDataFrame = teamList.file_data
RANKS = teamList.ranks
teamsInfo = teamList.teams_info
groupPart = {'up': ['A', 'B', 'C', 'D'], 'down': ['E', 'F', 'G', 'H']}
allGroups = {'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'}


class Team(object):
    """
    Present a team. Check valid group when drawn and pick up one.
    """

    def __init__(self, name=None):
        """

        :param name: team name
        """
        self.name = name
        self.league = teamsInfo[name]['league']
        self.rank = teamsInfo[name]['rank']
        self.status = 'candidate'
        self.group_assigned = None
        self.group_part = None
        self.paired = teamsInfo[name]['paired']
        self.candidate_groups = []

    def take_group(self, group_name):
        """
        确定分组后，修改部分属性值
        :param group_name: 取得的分组group名称
        :return:
        """
        self.status = 'drawn'  # 修改抽签状态为已抽中drawn
        self.group_assigned = group_name
        if group_name in groupPart['up']:
            self.group_part = 'up'
        else:
            self.group_part = 'down'


class Group(object):
    """
    某一小组抽签后的结果
    """

    def __init__(self, group_name=None):
        """
        分配组别名
        """
        self.group_name = group_name
        self.group_part = self.part
        self.teams = []  # teams may fall in this group
        self.leagues = []  # leagues that the teams in this group belong to
        self.ranks = []  # team ranks that the teams in this group belong

    def add_a_team(self, teamObj=None):
        """
        pick a team and add it to this group
        :param teamObj: 被抽出的Team对象
        :return:
        """
        self.teams.append(teamObj.name)
        self.leagues.append(teamObj.league)
        self.ranks.append(teamObj.rank)

    def del_a_team(self, teamObj=None):
        """

        :param teamObj: delete a team object from a groupObj
        :return:
        """
        self.teams.remove(teamObj.name)
        self.leagues.remove(teamObj.league)
        self.ranks.remove(teamObj.rank)

    @property
    def part(self):
        if self.group_name in groupPart['up']:
            return 'up'
        else:
            return 'down'


class Groups(object):
    """
    全部分组的当前抽签结果
    """

    def __init__(self):
        self.group_names = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
        self.group_obj_dict = self.initialize_group_objs(self.group_names)

    @staticmethod
    def initialize_group_objs(groupName):
        group_obj_dict = {}
        for g in groupName:
            group_obj_dict[g] = Group(g)
        return group_obj_dict


class Pick(object):
    """
    pick a team and a responding group.
    """

    @staticmethod
    def cal_valid_groups(teamObj, groups_drawn):
        """
        根据球队teamObj计算有效可选的组
        :param teamObj:
        :param groups_drawn: 已经抽签的分组结果, group_obj_dict
        :return:
        """
        valid_groups = []
        for groupName, groupObj in groups_drawn.items():
            if teamObj.rank in groupObj.ranks:
                continue  # 排除已有本档次球队的组
            if teamObj.league in groupObj.leagues:
                continue  # 同联赛球队回避
            if ['RUS', 'UKR'] <= groupObj.leagues + [teamObj.league]:
                continue  # 俄罗斯和乌克兰球队回避
            else:
                valid_groups.append(groupName)

        return sorted(list(valid_groups))

    @staticmethod
    def reverse_cal(result: dict):
        # 反向计算
        group_teams = {}
        sub_groups = []
        for lst in result.values():
            sub_groups += lst
        sub_groups = set(sub_groups)
        for g in sub_groups:
            group_teams[g] = []
        for (t, gs) in result.items():
            for g in sub_groups:
                if g in gs:
                    group_teams[g].append(t)
        return group_teams

    @staticmethod
    def cal_left_groups(drawn, stage):
        leftGroups = []
        for (key, value) in drawn.items():
            if len(value.teams) < stage:
                leftGroups.append(key)
        return leftGroups

    @staticmethod
    def check1(sub_result: dict):
        """
        如果sub_result中没有成对的匹配球队，检验组是否足够分配。
        检验方法：从sub_result中任意抽取r(r>2)只球队，以及分组的并集，取并集元素个数k。
        若r>k,则不通过检验；反之，通过检验。
        注：算法存在问题，暂不使用。
        :param sub_result:
        :return:
        """
        # sub_teams = sub_result.keys()
        # for teamName in sub_teams:
        #     if Team(teamName).paired in sub_teams:
        #         raise ValueError('There are matched teams in the argument, this check is not suitable.')
        if len(list(sub_result.keys())) <= 1:
            return True
        else:
            values_list = []
            for v1 in sub_result.values():
                for v2 in v1:
                    values_list.append(v2)
            for r in range(2, len(list(sub_result.keys())) + 1):
                comb = combinations(sub_result.values(), r)
                temp = []
                for item in comb:
                    for element in item:
                        temp = temp + list(element)
                temp = set(temp)
                if len(temp) < r:
                    return False
                else:
                    continue
            return True

    @staticmethod
    def cal_pair_teams(teams):
        """
        计算teams列表中成对对球队
        :param teams: 球队名称列表
        :return: 成对球队元组组成对列表，对数
        """
        if len(teams) <= 1:
            return [], 0
        else:
            pair_count = 0
            pair_teams = []
            for teamName in teams:
                if Team(teamName).paired in teams:
                    if sorted([teamName, Team(teamName).paired]) not in pair_teams:
                        pair_teams.append(sorted([teamName, Team(teamName).paired]))
                        pair_count += 1
        return pair_teams, pair_count

    @staticmethod
    def check2(sub_result: dict):
        """
        如果sub_result中存在成对的匹配球队，先检验这些匹配的球队是否有足够的分组；待给匹配球队分配组后，再检验剩余球队是否有组可分配。
        :param sub_result: dict. key值为球队名称，value值为该球队可选择的分组列表
        :return:
        注：算法存在问题，暂不使用。
        """
        sub_teams = sub_result.keys()
        if len(sub_teams) <= 1:
            return True
        pair_teams, pair_count = Pick.cal_pair_teams(sub_teams)
        if pair_count == 0:
            return Pick.check1(sub_result)
        pair_teams_list = []
        for t in pair_teams:
            for m in t:
                pair_teams_list.append(m)
        not_pair_teams = set(sub_teams) - set(pair_teams_list)
        # 检验1.成对的球队是否在上下半区有足够分组供选择
        temp_up_result = {}
        temp_down_result = {}
        for pair in pair_teams:
            temp_up_result[pair[0]] = list(set(sub_result[pair[0]]) - set(groupPart['down']))
            temp_down_result[pair[0]] = list(set(sub_result[pair[0]]) - set(groupPart['up']))
            # 如果temp_up_result 或 temp_down_result中但凡有一个key对应的value是空，则检验失败。
            if (not temp_up_result[pair[0]]) or (not temp_down_result[pair[0]]):
                return False
        if (not Pick.check1(temp_up_result)) or (not Pick.check1(temp_down_result)):
            return False
        else:  # 以下检验剩余不成对球队是否有足够分组
            sub_result_values = []
            temp_up_result_values = []
            temp_down_result_values = []
            for v1 in sub_result.values():
                for v2 in v1:
                    sub_result_values.append(v2)
            for v1 in temp_up_result.values():
                for v2 in v1:
                    temp_up_result_values.append(v2)
            for v1 in temp_down_result.values():
                for v2 in v1:
                    temp_down_result_values.append(v2)
            up_comb = combinations(temp_up_result_values, pair_count)
            down_comb = combinations(temp_down_result_values, pair_count)
            # 从sub_result中剔除pair_teams
            for up in up_comb:
                for down in down_comb:
                    picked_groups = list(up) + list(down)
                    sub2_result = {}
                    unpicked_groups = set(sub_result_values) - set(picked_groups)
                    for unpicked_team in not_pair_teams:
                        sub2_result[unpicked_team] = set(sub_result[unpicked_team]) & unpicked_groups
                        if not sub2_result[unpicked_team]:
                            return False
                    if Pick.check1(sub2_result):
                        return True
                    else:
                        continue
            return False

    @staticmethod
    def cal_candidate_groups(team_picked, teams_left, current_drawn, valid_groups: list):
        """
        在考虑尚未抽出球队的可选组别后，确定本次被抽中球队最终的候选分组
        :param team_picked: 本次被抽出的球队
        :param teams_left: 本档次尚未抽出的球队
        :param current_drawn: 已抽出的结果
        :param valid_groups:
        :return: 最终确定的有效候选分组列表
        """
        result_groups = deepcopy(valid_groups)
        tuple_groups = deepcopy(valid_groups)
        drawn = deepcopy(current_drawn)
        if len(result_groups) <= 1:
            return result_groups
        else:
            for group in tuple_groups:
                drawn[group].add_a_team(team_picked)  # 假设被抽到的球队被分到组group
                # 计算剩余球队的选择可能
                sub_result = {}
                flag1 = 1
                for team in teams_left:
                    sub_result[team.name] = Pick.cal_valid_groups(team, drawn)
                    if not sub_result[team.name]:
                        flag1 = 0
                        break
                if flag1 == 0:
                    result_groups.remove(group)
                    drawn[group].del_a_team(team_picked)
                    continue
                group_teams = Pick.reverse_cal(sub_result)
                left_groups = Pick.cal_left_groups(drawn, team_picked.rank)
                if sorted(list(group_teams.keys())) != sorted(left_groups):
                    result_groups.remove(group)
                else:
                    drawn[group].del_a_team(team_picked)
            return result_groups

    @staticmethod
    def pick(teamLists, latest_drawn):
        """
        pick a team and assign a group
        :param teamLists: 待抽取的Team对象列表
        :param latest_drawn: 最新的抽签结果
        :return: 被抽出的组名
        """
        # 步骤1.随机选出一个球队
        random.shuffle(teamLists)
        team_picked = teamLists.pop()  # 随机抽出一个teamObj; teamObjs相应剔除被抽中项
        # 步骤2.计算可选择的组
        valid_groups = Pick.cal_valid_groups(teamObj=team_picked, groups_drawn=latest_drawn)
        candidate_groups = Pick.cal_candidate_groups(team_picked, teamLists, latest_drawn, valid_groups)
        # 步骤3.从candidate_groups中抽出一个组，分配给本次被抽出的球队
        random.shuffle(candidate_groups)
        group_picked = candidate_groups.pop()
        return team_picked, group_picked


class Draw(object):
    def __init__(self):
        self.groups = Groups()
        self.groupDrawn = self.groups.group_obj_dict

    def draw_for_one_round(self, roundStage):
        """
        完成一轮抽签，抽出本档次所有球队
        :param roundStage: 轮次
        :return: 本轮抽出的（team,group) 列表
        """

        teams = list(teamDataFrame[teamDataFrame['rank'] == roundStage]['clubs'].values)
        teamObjs = [Team(team) for team in teams]
        while len(teamObjs) > 0:
            team, group = Pick.pick(teamObjs, self.groupDrawn)
            self.groupDrawn[group].add_a_team(team)

    def draw_for_all(self):
        """
        完成全部参赛球队的抽签
        :return:
        """
        # 初始化全部组对象
        for rank in RANKS:
            self.draw_for_one_round(rank)

    def print_draw_result(self):
        """
        打印抽签结果
        :return:
        """
        for group in self.groupDrawn.values():
            print("The result of Group %s:" % group.group_name)
            i = 1
            for team in group.teams:
                print(i, team)
                i += 1
            print("*" * 10)


if __name__ == "__main__":
    fail_count = 0
    for _ in range(50):
        draw = Draw()
        try:
            draw.draw_for_all()
        except:
            fail_count += 1
    print(fail_count)
