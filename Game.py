# -*- coding: utf-8 -*-
from __future__ import print_function
import numpy as np
from VisualTool import *
from gomokuUI import GomokuGUI


class Game(object):
    def __init__(self, board, is_visualize=False):
        self.board = board
        self.visualTool = None
        if is_visualize: self.visualTool = VisualTool(board_size=[self.board.width, self.board.height])

    def show(self):
        self.visualTool.draw()

    def graphic(self, board, player1, player2):
        """
        Draw the board and show game info
        """
        loc = self.board.move2loc(self.board.last_move)
        self.visualTool.graphic(loc[0], loc[1])

    def graphic_command(self, board, player1, player2):
        '''graphic in the command line for self-play'''
        width = board.width
        height = board.height
        player1_no = player1 if isinstance(player1, int) else player1.get_player_no()
        player2_no = player2 if isinstance(player2, int) else player2.get_player_no()

        print("player:", player1, self.player1_symbol.rjust(3))
        print("player:", player2, self.player2_symbol.rjust(3))
        print()
        for x in range(width):
            print("{0:8}".format(x), end='')
        print('\r\n')
        for i in range(height - 1, -1, -1):
            print("{0:4d}".format(i), end='')
            for j in range(width):
                loc = i * width + j
                p = board.states.get(loc, -1)
                if p == player1_no:
                    if loc == self.board.last_move:
                        print(("[%s]" % (self.player1_symbol)).center(8), end='')
                    else:
                        print(self.player1_symbol.center(8), end='')
                elif p == player2_no:
                    if loc == self.board.last_move:
                        print(("[%s]" % (self.player2_symbol)).center(8), end='')
                    else:
                        print(self.player2_symbol.center(8), end='')
                else:
                    print('_'.center(8), end='')
            print('\r\n\r\n')

    def set_player_symbol(self, who_first):
        '''show board, set player symbol X OR O'''
        p1, p2 = self.board.players
        if self.board.players[who_first] == p1:
            self.player1_symbol = "X"
            self.player2_symbol = "O"
        else:
            self.player1_symbol = "O"
            self.player2_symbol = "X"

    def start_game(self, player1, player2, who_first=0, is_shown=1):
        """
        start a game between two players
        """
        gui = GomokuGUI(self.board.width)
        if is_shown: self.visualTool.set_player(player1, player2, who_first)
        self.board.init_board(who_first)
        p1, p2 = self.board.players

        self.set_player_symbol(who_first)

        players = {p1: player1, p2: player2}
        # if is_shown:
        #     self.graphic(self.board, player1, player2)
        while (True):
            current_player = self.board.get_current_player()
            player_in_turn = players[current_player]
            move = player_in_turn.play(self.board, tool=self.visualTool)
            self.board.do_move(move)
            if is_shown:
                self.graphic(self.board, player1, player2)
            gui.render_step(action=move, player=current_player)
            end, winner = self.board.game_end()
            if end:
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is", players[winner])
                        self.visualTool.wininfo("Game end. Winner is {}".format(players[winner]))
                    else:
                        print("Game end. Tie")
                        self.visualTool.wininfo("Game end. Tie")
                return winner

    def start_self_play_game(self, player, is_shown=0, temp=1e-3):
        """ start a self-play game using a MCTS player, reuse the search tree
        store the self-play data: (state, mcts_probs, z)
        """
        gui = GomokuGUI(self.board.width)
        self.board.init_board()
        p1, p2 = self.board.players
        states, mcts_probs, current_players = [], [], []
        if is_shown:
            self.set_player_symbol(who_first=0)
        while True:
            # ZE gui显示用，self.board会变，所以放这里（神他妈奇，action_probs_gui变量会被下面哪个语句改变值，去掉当前的move）
            action_probs_gui, leaf_value = player.mcts._policy_value_fn(self.board)
            x, y = zip(*action_probs_gui)
            policy = dict(zip(x, y))
            for a in range(self.board.width * self.board.width):
                if a not in x: policy[a] = 0.
            gui.update_value_s((1 - leaf_value) / 2)  # 左边显示胜率
            gui.draw_value(-leaf_value)  # 左右两个value都会画出，左边的是上一轮由动态网络生成，右边的是本轮由初始网络生成

            move, move_probs = player.play(self.board, temp=temp, epsilon=0.1, return_prob=True)  # 0.2感觉太随机了
            # store the data
            states.append(self.board.current_state())
            mcts_probs.append(move_probs)
            current_players.append(self.board.get_current_player())
            # perform a move
            self.board.do_move(move)
            if is_shown:
                # self.graphic_command(self.board, p1, p2)
                # gui.render_step(action=move, player=current_players[-1])
                gui.render_all_step(action=move,
                                    player=current_players[-1],
                                    policy=policy,
                                    pi=move_probs,
                                    v=player.mcts.child_values[-1],
                                    min_max_stats=None
                                    )

            end, winner = self.board.game_end()
            if end:
                # 最后一步的v也显示/打印出来
                action_probs_gui, leaf_value = player.mcts._policy_value_fn(self.board)
                gui.update_value_s((1 - leaf_value) / 2)  # 左边显示胜率
                gui.draw_value(-leaf_value)

                # winner from the perspective of the current player of each state
                winners_z = np.zeros(len(current_players))
                if winner != -1:  # end and has a winner
                    winners_z[np.array(current_players) == winner] = 1.0
                    winners_z[np.array(current_players) != winner] = -1.0
                # reset MCTS root node
                player.reset_player()
                if is_shown:
                    if winner != -1:
                        print("Game end. Winner is player:", winner)
                    else:
                        print("Game end. Tie")
                return winner, zip(states, mcts_probs, winners_z), len(states)

    def __str__(self):
        return "Game"
