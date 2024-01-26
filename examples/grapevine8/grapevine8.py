# from model import Problem,E_TYPE,PDDL_TERNARY
import logging 
import math
from typing import Tuple
import numpy as np
import traceback

import re


from util import PDDL_TERNARY
from util import EpistemicQuery,E_TYPE
AGENT_ID_PREFIX = "agent_at-"
AGENT_LOC_PREFIX = 'agent_at-'
OBJ_LOC_PREFIX = 'shared-s'

LOGGER_NAME = "grapevine8"
LOGGER_LEVEL = logging.INFO
from util import setup_logger
 
# declare common variables
common_constants = {

}

class ExternalFunction:
    logger = None
    
    def __init__(self, handlers):
        self.logger = setup_logger(LOGGER_NAME,handlers,logger_level=logging.INFO) 

    # # customized evaluation function

    def extractVariable(self,q_content_str):
        if not re.search("\([0-9a-z _\-\'\"]*,[0-9a-z _\'\"]*\)",q_content_str) == None:
            var_name = q_content_str.split(",")[0][1:]
            value = q_content_str.split(",")[1][:-1]
            return (var_name.replace('"','').replace("'",''),value.replace('"','').replace("'",''))
        else:
            # customized function here
            pass


    def extractAgents(self,eq):
        if not type(eq) == EpistemicQuery:
            return []
        else:
            
            return eq.q_group + self.extractVariables(eq.q_content)    

    # customized evaluation function
    def evaluateS(self,world,statement):
        #default evaluation for variables
        if world == {}:
            return 2
        if not re.search("\([0-9a-z _\-\'\"]*,[0-9a-z _\'\"]*\)",statement) == None:
            var_name = statement.split(",")[0][1:].replace("'",'').replace('"','')
            value = statement.split(",")[1][:-1].replace("'",'').replace('"','')
            if var_name in world:
                return 1
            else:
                return 0
        else:
            self.logger.warning("the evaluation of the seeing equation has not defined")
            return 0

    def agentsExists(self,path,g_group_index):
        state = path[-1][0]
        for agt_id in g_group_index:
            if not AGENT_ID_PREFIX+agt_id in state.keys():
                return False
        return True


    def checkVisibility(self,state,agt_index,var_index,entities,variables):
        
        # logger.debug(f"checkVisibility(_,_,{agt_index},{var_index})")
        try:

            self.logger.debug('checking seeing for agent {} on {} in state {}',agt_index,var_index,state)
            tgt_index = variables[var_index].v_parent
            
            # check if the agt_index can be found
            assert(entities[agt_index].e_type==E_TYPE.AGENT)
            
            # if the variable contains shared or secret, then it means checking secret location
            # which mean checking location of shared (agent's own secret can be shared by others)
            # otherwise it checking agent's current location
            if 'secret' in var_index:
                tgt_loc = state[f'shared-{tgt_index}']
                if type(tgt_loc) == str:
                    tgt_loc = int(state[f'shared-{tgt_index}'])

                # agent should know their own secret before sharing
                if tgt_index == agt_index and  tgt_loc == 0:
                    return PDDL_TERNARY.TRUE
                
                # if the secret has not been shared
                if tgt_loc == 0:
                    return PDDL_TERNARY.FALSE
                
                
            elif 'shared' in var_index:
                tgt_loc = state[f'shared-{tgt_index}']
                if type(tgt_loc) == str:
                    tgt_loc = int(state[f'shared-{tgt_index}'])
                
                # agent knows if a secret is not been shared
                # this is to break the continues effect of a sharing secret
                if tgt_loc == 0:
                    return PDDL_TERNARY.TRUE
                    
            
            else:
                # the target is an agent, it has its own location
                # tgt_loc = int(state[f'agent_at-{tgt_index}'])
                # Since in Grapevine domain, there is only two rooms
                # agent will know others location if they are in the same room
                # agent will also know others location if they are not in the same room
                return PDDL_TERNARY.TRUE



            agt_loc_str = AGENT_LOC_PREFIX+agt_index
            if agt_loc_str not in state.keys() or state[agt_loc_str] == None:
                return PDDL_TERNARY.UNKNOWN
            else:
                agt_loc = int(state[agt_loc_str])

            
            # extract necessary common constants from given domain
            # logger.debug(f"necessary common constants from given domain")

            # logger.debug(f'checking seeing with agent location: {agt_loc} and target location: {tgt_loc}')
            # agent is able to see anything in the same location
            if tgt_loc == agt_loc:
                return PDDL_TERNARY.TRUE
            else:
                return PDDL_TERNARY.FALSE

        except KeyError:
            self.logger.warning(traceback.format_exc())
            self.logger.warning("variable not found when check visibility")
            # logging.error("error when checking visibility")
            return PDDL_TERNARY.UNKNOWN
        except TypeError:
            self.logger.warning(traceback.format_exc())
            self.logger.warning("variable is None d when check visibility")
            # logging.error("error when checking visibility")
            return PDDL_TERNARY.UNKNOWN

    # customise action filters
    # to filter out the irrelevant actions
    # customise action filters
    # to filter out the irrelevant actions
    def filterActionNames(self,problem,action_dict):
        # print(action_dict.keys())
        action_name_list = []
        relevant_variable_parent_index = []
        relevant_agent_index = []
        

        for key,ep_obj in problem.goals.epistemic_dict.items():
            eq_str = ep_obj.query
            match = re.search("[edc]?[ksb] \[[0-9a-z_,]*\] ",eq_str)
            while not match == None:
                eq_list = eq_str.split(" ")
                relevant_agent_index += eq_list[1][1:-1].split(",")
                eq_str = eq_str[len(eq_list[0])+len(eq_list[1])+2:]
                match = re.search("[edc]?[ksb] \[[0-9a-z_,]*\] ",eq_str)
                
            # variable_name,value =self.extractVariable(eq_str)
            variable_name = ep_obj.variable_name
            relevant_variable_parent_index.append(problem.variables[variable_name].v_parent)
            self.logger.debug("variable_name[%s] , problem.variables[variable_name].v_parent [%s]",variable_name,problem.variables[variable_name].v_parent)




        for name,action in action_dict.items():
            self.logger.debug('action_name: [%s]',name) 
            if "sharing_" in name:
                if name.split("-")[2] in relevant_variable_parent_index:
                    action_name_list.append(name)
            elif "sharing" in name or "lying" in name:
                if name.split("-")[1] in relevant_variable_parent_index:
                    action_name_list.append(name)
            elif "move" in name:
                self.logger.debug('agent_in: [%s]',name.split("-")[1]) 
                if name.split("-")[1] in relevant_agent_index:
                    action_name_list.append(name) 
            else:
                action_name_list.append(name)
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            self.logger.debug('action names after filter: [%s]',action_name_list)   
        return action_name_list
        return action_dict.keys()

    