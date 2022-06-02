# -*- coding: utf-8 -*-
import math

import numpy as np

'''
Node of MCTS Searching Tree
'''


class TreeNode(object):
    def __init__(self, parent, prior_p):
        self._parent = parent  # parent node
        self._children = {}  # child nodes，a map from action to TreeNode
        self._n_visits = 0  # visit count
        self._Q = 0  # Q Value
        self._u = 0  # bonus，calculated based on the visit count and prior probability
        self._P = prior_p  # prior probability,calculated based on the Network

    def expand(self, action_priors):
        """Expand tree by creating new children.
                action_priors -- output from policy function - a list of tuples of actions
                    and their prior probability according to the policy function.
                """
        for action, prob in action_priors:
            if action not in self._children:
                self._children[action] = TreeNode(self, prob)

    def select(self, c_puct=5.0, epsilon=0.0, alpha=0.3):
        """Select action among children that gives maximum action value, Q plus bonus u(P).
        (1-e)pa+e*dirichlet(eta) # add Dirichlet Noise for exploration
                Returns:
                A tuple of (action, next_node)
                """
        return max(self._children.items(), key=lambda act_node: act_node[1]._get_value(c_puct, epsilon, alpha))

    def _get_value(self, c_puct, epsilon=0, alpha=0.3):
        """Calculate and return the value for this node: a combination of leaf evaluations, Q, and
        this node's prior adjusted for its visit count, u

        c_puct -- a number in (0, inf) controlling the relative impact of values, Q, and
            prior probability, P, on this node's score.
        epsilon -- the fraction of the prior probability, and 1-epsilon is the corresponding dirichlet noise fraction
        alpha -- the parameter of dirichlet noise
        """
        # noise = 0
        # if epsilon > 0: noise = np.random.dirichlet([alpha])[0] # 添加噪声，目前噪声比例epsilon=0,即，不使用噪声
        # self._u = c_puct * ((1-epsilon) * self._P + epsilon * noise) * \
        #           np.sqrt(self._parent._n_visits) / (1 + self._n_visits)
        # return self._Q + self._u
        noise = 0
        if epsilon > 0: noise = np.random.dirichlet([alpha])[0]  # 添加噪声，目前噪声比例epsilon=0,即，不使用噪声
        pb_c = math.log((self._parent._n_visits + 19652 + 1) / 19652) + c_puct  # 其实几乎等于c_puct
        self._u = pb_c * ((1 - epsilon) * self._P + epsilon * noise) * \
                  np.sqrt(self._parent._n_visits) / (1 + self._n_visits)
        return self._Q + self._u

    def backup(self, leaf_value):
        """Like a call to update(), but applied recursively for all ancestors.
                """
        # If it is not root, this node's parent should be updated first.
        if self._parent:
            self._parent.backup(-leaf_value)

        self._n_visits += 1
        # Update Q, a running average of values for all visits.
        # This step combine W,Q. Derived formula is as follows (reference AlphaGoZero Method Section)：
        # W = W_old + leaf_value; Q_old = W_old / (n-1) => W_old = (n-1)*Q_old; Q = W/n
        # Q = W/n=(W_old + leaf_value)/n = ((n-1)*Q_old+leaf_value)/n
        #   = (n*Q_old-Q_old+leaf_value)/n = Q_old + (leaf_value-Q_old)/n
        self._Q += 1.0 * (leaf_value - self._Q) / self._n_visits

    def is_leaf(self):
        """Check if leaf node (i.e. no nodes below this have been expanded).
        """
        return self._children == {}

    def is_root(self):
        return self._parent is None
