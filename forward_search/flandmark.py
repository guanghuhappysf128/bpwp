import logging

from util import setup_logger, PriorityQueue, PDDL_TERNARY
# import util


LOGGER_NAME = "forward_search:bfsdc"
LOGGER_LEVEL = logging.INFO
# LOGGER_LEVEL = logging.DEBUG

SPLIT_KEY_WORD = "@"

class Search:
    def __init__(self,handlers):        
        self.logger = setup_logger(LOGGER_NAME,handlers,logger_level=LOGGER_LEVEL) 
        self.expanded = 0
        self.goal_checked = 0
        self.generated = 0
        self.pruned = 0
        self.pruned_by_unknown = 0
        self.pruned_by_visited = 0
        self.visited = []
        self.short_visited = []
        self.result = dict()
        self.branch_factors = []
        self.p_path = {}

    class SearchNode:
        state = None
        epistemic_item_set = set([])
        remaining_goal = 9999
        path = []

        def __init__(self,state,epistemic_item_set,path):
            self.state = state
            self.epistemic_item_set = epistemic_item_set
            self.path = path




    #BFS with duplicate check on the state + epistemic formula
    # for novelty checking purpose, we need to move the goal check process at where the node is generated
    def searching(self,problem, filterActionNames = None):
        
        
        self.logger.info("starting searching using %s",LOGGER_NAME)
        max_goal_num = len(problem.goals.ontic_dict)+len(problem.goals.epistemic_dict)
        # self.logger.info(f'the initial is {problem.initial_state}')
        # self.logger.info(f'the variables are {problem.variables}')
        # self.logger.info(f'the domains are {problem.domains}')
        
        # check whether the initial state is the goal state
        init_state = problem.initial_state
        init_path = [(problem.initial_state,'')]
        init_epistemic_item_set = dict()
        
        init_node = Search.SearchNode(init_state,init_epistemic_item_set,init_path)
        self.group_eg_dict = self.group_epistemic_goals(problem)
        # print(self.group_eg_dict)
        # self.landmarks_dict = problem.external.generate_constrain_dict(problem,self.group_eg_dict)

        
        
        
        open_list = PriorityQueue()
        p,es = self._f(init_node,problem,self.p_path)
        init_node.remaining_goal =  p-self._gn(init_node)
        init_node.epistemic_item_set.update(es)
        # remaining_g = p-_gn(init_node)
        open_list.push(item=init_node, priority=self._gn(init_node))
        
        
        while not open_list.isEmpty():

            current_p , _, current_node = open_list.pop_full()

            state = current_node.state
            ep_goal_dict = current_node.epistemic_item_set
            path = current_node.path
            actions = [ a  for s,a in path]
            actions = actions[1:]

            # if len(path) > 5:
            #     exit()
            self.logger.debug("path: %s",actions)

            is_goal = (0 == current_node.remaining_goal)
            if is_goal:
                # self.logger.info(path)
                actions = [ a  for s,a in path]
                actions = actions[1:]
                self.logger.info(f'plan is: {actions}')
                self.logger.info(f'Goal found')
                self.result.update({'solvable': True})
                self.result.update({'plan':actions})
                self._finalise_result(problem)
                return self.result
            
            all_actions = problem.getAllActions(state,path)
            # self.logger.debug(actions)
            filtered_action_names = filterActionNames(problem,all_actions)
            
            ontic_pre_dict = {}
            epistemic_pre_dict = {}
            for action_name in filtered_action_names:
                action = all_actions[action_name]
                ontic_pre_dict.update({action_name:action.a_preconditions.ontic_dict})
                epistemic_pre_dict.update({action_name:action.a_preconditions.epistemic_dict})
 
            flag_dict,e_pre_dict,pre_dict = problem.checkAllPreconditions(state,path, ontic_pre_dict,epistemic_pre_dict,self.p_path)

            # e_pre_dict.update(state)
            # e_pre_dict.update(ep_goal_dict)
            e_pre_dict.update(state)
            e_pre_dict.update(ep_goal_dict)
            e_pre_dict.update(pre_dict)
            
            self.logger.debug("flag_dict is [%s]",flag_dict)
            # assert(len(path) <=2)
            ep_state_str = state_to_string(e_pre_dict)
            if not ep_state_str in self.visited:
                # self.logger.debug(epistemic_item_set)
            # if True:
                # self.branch_factors.append(flag_dict.values().count(True))
                self.logger.debug("path [%s] get in visited",actions)
                self.logger.debug("ep_state_str is [%s]",ep_state_str)
                self.expanded +=1
                temp_successor = 0
                temp_actions = []
                # update the visited list
                # self.short_visited.append(temp_str)
                self.visited.append(ep_state_str)

                
                # self.logger.debug("finding legal actions:")


                
                for action_name in filtered_action_names:

                    self.logger.debug(action_name)

                    if flag_dict[action_name]: 
                        action = all_actions[action_name]
                        self.logger.debug("action [%s] passed the precondition check", action_name)
                        # passed the precondition
                        succ_state = problem.generateSuccessor(state, action,path)
                        # self.visited.append(e_dict)
                        self.goal_checked += 1
                        succ_node = self.SearchNode(succ_state,{},path + [(succ_state,action_name)])
                        p,ep_dict = self._f(succ_node,problem,self.p_path)
                        
                        succ_node.remaining_goal = p - self._gn(succ_node)
                        if succ_node.remaining_goal <= max_goal_num+2:
                            succ_node.epistemic_item_set = ep_dict
                            self.generated += 1
                            open_list.push(item=succ_node, priority=p)
                            temp_successor +=1
                            temp_actions.append(action_name)
                        else:
                            self.pruned_by_unknown +=1


                    else:
                        self.logger.debug('action [%s] not generated in state [%s] due to not pass precondition',action_name,state)
                self.logger.debug('successor: [%s] with actions [%s]',temp_successor,temp_actions)
            else:
                self.pruned_by_visited += 1
                self.logger.debug("path [%s] already visited",actions)
                self.logger.debug("ep_state_str: [%s]",ep_state_str)
                self.logger.debug("visited: [%s]",self.visited)
            # self.logger.debug(open_list.count)
            
            
        self.logger.info(f'Problem is not solvable')
        self.result.update({'plan':[]})
        self.result.update({'solvable': False})
        
        self._finalise_result(problem)
        self.logger.debug(self.result)
        return self.result

    
    




    def _finalise_result(self,problem):
        # logger output


        self.logger.info(f'[number of node pruned_by_unknown]: {self.pruned_by_unknown}')
        self.logger.info(f'[number of node pruned_by_visited]: {self.pruned_by_visited}')
        self.pruned = self.pruned_by_unknown + self.pruned_by_visited
        self.logger.info(f'[number of node pruned]: {self.pruned}')

        self.logger.info(f'[number of node goal_checked]: {self.goal_checked}')
        self.logger.info(f'[number of node expansion]: {self.expanded}')
        self.logger.info(f'[number of node generated]: {self.generated}')
        self.logger.info(f'[number of epistemic formulas evaluation: {problem.epistemic_calls}]')
        self.logger.info(f'[time in epistemic formulas evaluation: {problem.epistemic_call_time}]')
        
        # file output
        self.result.update({'pruned':self.pruned})
        self.result.update({'pruned_by_unknown':self.pruned_by_unknown})
        self.result.update({'pruned_by_visited':self.pruned_by_visited})
        self.result.update({'goal_checked':self.goal_checked})
        self.result.update({'expanded':self.expanded})
        self.result.update({'generated':self.generated})
        self.result.update({'epistemic_calls':problem.epistemic_calls})
        self.result.update({'epistemic_call_time':problem.epistemic_call_time.total_seconds()})
        
        ## added for common perspective iterations
        common_iteration_list = problem.epistemic_model.common_iteration_list
        num_common_call = 0
        all_common_iteration = 0
        max_common_iteration = 0
        average_common_iteration = 0
        if not common_iteration_list == list():
            num_common_call = len(common_iteration_list)
            all_common_iteration = sum(common_iteration_list)
            max_common_iteration = max(common_iteration_list)
            average_common_iteration = all_common_iteration/(num_common_call*1.0)
        self.logger.info(f'[number of common perspective generated]: {num_common_call}')
        self.logger.info(f'[number of all iterations used when generating common perspectives]: {all_common_iteration}')
        self.logger.info(f'[number of max iterations used when generating common perspectives]: {max_common_iteration}')
        self.logger.info(f'[number of average iterations used when generating common perspectives]: {average_common_iteration}')
        self.result.update( {'common_calls':num_common_call})
        self.result.update( {'common_total':all_common_iteration})
        self.result.update( {'common_max':max_common_iteration})
        self.result.update( {'common_average':average_common_iteration})

    def group_epistemic_goals(self,problem):
        group_eg_dict = {}
        for eq_str,ep_condition in problem.goals.epistemic_dict.items():
            variable_name = ep_condition.variable_name
            # var_str = eq_str.split(" ")[-1].split(",")[0][2:-1]
            if variable_name in group_eg_dict:
                group_eg_dict[variable_name].append((eq_str,ep_condition))
            else:
                group_eg_dict.update({variable_name:[(eq_str,ep_condition)]})
        return group_eg_dict



    def _f(self,node,problem,p_path):
        heuristic = self.goal_counting
        g = self._gn(node)
        h,es = heuristic(node,problem,p_path)
        f = g*1+h*1
        return f,es

    def _isGoal(self,current_p, current_node):
        return (current_p - self._gn(current_node)*1) == 0

    def _gn(self,node):
        path = node.path
        return len(path)-1

    # it is not admissible
    def goal_counting(self,node,problem,p_path):
        remain_goal_number = 0
        state = node.state
        path = node.path
        
        is_goal,epistemic_dict,goal_dict = problem.isGoal(state,path,p_path)
        
        remain_goal_number = list(goal_dict.values()).count(False)

        for key,value in goal_dict.items():
            if str(PDDL_TERNARY.UNKNOWN.value) in key and not value:
                self.logger.debug('Unknown been updated, goal is impossible')
                return 9999,epistemic_dict      
        # return remain_goal_number,epistemic_dict

        # {'secret-b': [("b [a] ('secret-b','t')", 1), ("b [d] b [a] ('secret-b','f')", 1)], 
        #  'secret-c': [("b [b] ('secret-c','t')", 1), ("b [c] b [b] ('secret-c','f')", 1)], 
        #  'secret-d': [("b [c] ('secret-d','t')", 1), ("b [b] b [c] ('secret-d','f')", 1)], 
        #  'secret-a': [("b [d] ('secret-a','t')", 1), ("b [a] b [d] ('secret-a','f')", 1)]}

        # {"b [a] ('secret-b','t') 1": False, 
        #  "b [b] ('secret-c','t') 1": False, 
        #  "b [c] ('secret-d','t') 1": False, 
        #  "b [d] ('secret-a','t') 1": False, 
        #  "b [d] b [a] ('secret-b','f') 1": False, 
        #  "b [c] b [b] ('secret-c','f') 1": False, 
        #  "b [b] b [c] ('secret-d','f') 1": False, 
        #  "b [a] b [d] ('secret-a','f') 1": False}
        # exit()
        heuristic_value = remain_goal_number
        
        landmark_constrain = []
        temp_v_name_list = []

        # print(goal_dict.keys())
        
        for v_name, ep_goals in self.group_eg_dict.items():
            # print(ep_goals)
            for ep_str,ep_condition in ep_goals:
                # print(ep_str)
                # print(goal_dict[ep_str])
                if not goal_dict[ep_str]:
                    temp_v_name_list.append(v_name)
                    # heuristic_value +=1
                    # break



        # for v_name in temp_v_name_list:
        #     temp_pair_dict = {}
        #     for ep_str,value in group_eg_dict[v_name]:
        #         ep_value = ep_str.split(v_name)[1][3:-2]
        #         ep_front = ep_str.split(v_name)[0]
        #         ep_header = format_ep(ep_value,value)
        temp_landmark = set()
         
        # print(temp_v_name_list)       
        # for temp_v_name in temp_v_name_list:
        #     # flag = True
        #     for temp_state in self.landmarks_dict[temp_v_name]:
        #         if not str(sorted(temp_state)) in temp_landmark:
        #             temp_flag = True
        #             for key,value in temp_state.items():
        #                 if key in state.keys():
        #                     if not state[key]==value:
        #                         temp_flag = False
        #                         break
        #             if temp_flag:
        #                 heuristic_value +=1
        #                 temp_landmark.add(str(sorted(temp_state)))
        #                 break
                
            # if flag:
            #     heuristic_value +=1
                
                
        
        
        # if 'secret-a' in temp_v_name_list:
        #     landmark_constrain.append(('agent_at-b','agent_at-d'))
        # elif 'secret-c' in temp_v_name_list:
        #     landmark_constrain.append(('agent_at-b','agent_at-d'))
        if temp_v_name_list.count('secret-b') == 1:
            landmark_constrain.append(('agent_at-b','agent_at-a'))
        if temp_v_name_list.count('secret-c') == 1:
        # if 'secret-c' in temp_v_name_list:
            landmark_constrain.append(('agent_at-b','agent_at-c'))
        # elif 'secret-d' in temp_v_name_list:
        #     landmark_constrain.append(('agent_at-c','agent_at-a'))
        # print(heuristic_value)
        for v1,v2 in landmark_constrain:
            if state[v1] == state[v2]:
                heuristic_value +=1
        # print(heuristic_value)
        
        return heuristic_value,epistemic_dict



def state_to_string(dicts):
    output = []
    for key,value in dicts.items():
        output.append(f'{key}:{value}')
    output.sort() 
    return str(output)
