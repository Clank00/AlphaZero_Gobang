# -*- coding: utf-8 -*-
"""
An implementation of the training pipeline of AlphaZero for Gobang

tensorboard查看loss曲线使用方法：
1、在Terminal中运行 tensorboard --logdir=D:\GitHub\AlphaZero_Gobang\out\logs
 （其中D:\GitHub\AlphaZero_Gobang\为项目地址需要替换）
2、在浏览器中打开 http://localhost:6006/ 即可查看曲线

"""

from __future__ import print_function

import os
import random
from tqdm import trange
import numpy as np
import pickle
from collections import defaultdict, deque
from Game import Game
from Board import Board
from PolicyValueNet import *  # Pytorch
from AlphaZeroPlayer import AlphaZeroPlayer
from RolloutPlayer import RolloutPlayer
from Config import *
import argparse
from Util import *
from utils.debugging import AlphaZeroMonitor, logging_initialize

NUM_ROLLOUT = 0


class TrainPipeline():
    def __init__(self, config=None):
        # params of the board and the game
        self.config = config if config else Config()
        if not hasattr(self.config, "use_gpu"): setattr(config, "use_gpu", False)  # compatible with old version config
        # Network wrapper
        self.policy_value_net = PolicyValueNet(self.config.board_width, self.config.board_height,
                                               net_params=self.config.policy_param,
                                               Network=self.config.network, use_gpu=self.config.use_gpu)

        # forward the reference of policy_value_net'predict function，for MCTS simulation
        self.mcts_player = AlphaZeroPlayer(self.policy_value_net.predict, c_puct=self.config.c_puct,
                                           nplays=self.config.n_playout, is_selfplay=True)

        self.monitor = AlphaZeroMonitor(self)

    def self_play(self, n_games=1):
        """
        collect self-play data for training
        n_game: self-play n_games and then optimize
        """
        self.episode_len = 0
        self.augmented_len = 0
        for i in range(n_games):
            winner, play_data, episode_len = self.config.game.start_self_play_game(self.mcts_player, is_shown=1,
                                                                                   temp=self.config.temp)
            self.episode_len += episode_len  # episode_len is the length of each self_play epoch
            # augment the data
            play_data = self.augment_data(play_data)
            self.augmented_len += len(play_data)
            self.config.data_buffer.extend(play_data)

    def optimize(self, iteration):
        """update the policy-value net"""
        mini_batch = random.sample(self.config.data_buffer, self.config.batch_size)
        state_batch, mcts_probs_batch, winner_batch = list(zip(*mini_batch))

        if self.config.is_adjust_lr and iteration % self.config.adjust_lr_freq == 0:
            old_probs, old_v = self.policy_value_net.predict_many(state_batch)  # used for adjusting lr

        opt_times = int(5.12 * len(self.config.data_buffer) / self.config.batch_size)
        for i in range(opt_times):  # number of opt times   原为self.config.per_game_opt_times
            loss_info = self.policy_value_net.fit(state_batch, mcts_probs_batch, winner_batch,
                                                  self.config.learn_rate * self.config.lr_multiplier)
        if self.config.is_adjust_lr and iteration % self.config.adjust_lr_freq == 0:
            # adaptively adjust the learning rate
            self.adjust_learning_rate(old_probs, old_v, state_batch, winner_batch)
            # self.adjust_learning_rate_2(iteration)

        print("combined loss:{0:.5f}, value loss:{1:.5f}, policy loss:{2:.5f}, entropy:{3:.5f}".
              format(loss_info['combined_loss'], loss_info['value_loss'], loss_info['policy_loss'],
                     loss_info['entropy']))

        return loss_info

    def adjust_learning_rate(self, old_probs, old_v, state_batch, winner_batch):
        '''
        reference paper: PPO:Proximal Policy Optimization
        adjust learning rate based on KL
        '''
        new_probs, new_v = self.policy_value_net.predict_many(state_batch)
        kl = np.mean(np.sum(old_probs * (np.log(old_probs + 1e-10) - np.log(new_probs + 1e-10)), axis=1))  # KL
        if kl > self.config.kl_targ * 2 and self.config.lr_multiplier > 0.1:  # kl increase, denote that the new move prob distribution deviate a lot from original distribution, that's what we don't expect. maybe dute to too large lr
            self.config.lr_multiplier /= 1.5
        elif kl < self.config.kl_targ / 2 and self.config.lr_multiplier < 10:  # kl decrease, denote that learning procedure is vary stable and slow
            self.config.lr_multiplier *= 1.5

        explained_var_old = 1 - np.var(np.array(winner_batch) - old_v.flatten()) / np.var(np.array(winner_batch))
        explained_var_new = 1 - np.var(np.array(winner_batch) - new_v.flatten()) / np.var(np.array(winner_batch))

        print("\n学习率调整    kl:{:.5f},lr:{:.7f},explained_var_old:{:.3f},explained_var_new:{:.3f}".format(
            kl, self.config.learn_rate * self.config.lr_multiplier, explained_var_old, explained_var_new))

    def adjust_learning_rate_2(self, iteration):
        '''衰减法'''
        if (iteration + 1) % self.config.lr_decay_per_iterations == 0:
            self.config.lr_multiplier /= self.config.lr_decay_speed
        print("lr:{}".format(self.config.learn_rate * self.config.lr_multiplier))

    def evaluate(self, n_games=10):
        """
        Evaluate the trained policy by playing games against the pure MCTS player
        Note: this is only for monitoring the progress of training
        """
        current_mcts_player = AlphaZeroPlayer(self.policy_value_net.predict, c_puct=self.config.c_puct,
                                              nplays=self.config.n_playout)

        if self.config.evaluate_opponent == 'Pure':
            # opponent is rolloutplayer
            print("Begin evaluation, Opponent is RolloutMCTSPlayer")
            opponent_mcts_player = RolloutPlayer(c_puct=5, nplays=self.config.pure_mcts_playout_num)
        else:
            # oppenent is AlphaZeroPlayer
            print("Begin evaluation, Opponent is AlphaZeroMCTSPlayer")
            opponent_mcts_player = load_player_from_file(self.config.cur_best_alphazero_store_filename)

        win_cnt = defaultdict(int)
        for i in range(n_games):
            print("evaluate game %d" % i)
            winner = self.config.game.start_game(current_mcts_player, opponent_mcts_player, who_first=i % 2, is_shown=0)
            win_cnt[winner] += 1
        win_ratio = 1.0 * (win_cnt[1] + 0.5 * win_cnt[-1]) / n_games
        print("num_playouts:{}, win: {}, lose: {}, tie:{}".format(self.config.pure_mcts_playout_num, win_cnt[1],
                                                                  win_cnt[2],
                                                                  win_cnt[-1]))
        return win_ratio

    def augment_data(self, play_data):
        """
        augment the data set by rotation and flipping
        play_data: [(state, mcts_prob, winner_z), ..., ...]"""
        extend_data = []
        for state, mcts_porb, winner in play_data:
            '''
            state:
            3*3 board's moves like:
                6 7 8
                3 4 5
                0 1 2
            mcts_porb: flatten
            0,1,2,3,4,5,6,7,8
            winner
            1 or -1
            '''
            for i in [1, 2, 3, 4]:
                # rotate counterclockwise
                equi_state = np.array([np.rot90(s, i) for s in state])  # i=4 represents the origin data
                equi_mcts_prob = np.rot90(
                    np.flipud(mcts_porb.reshape(self.config.board_height, self.config.board_width)),
                    i)  # flip up and down
                extend_data.append((equi_state, np.flipud(equi_mcts_prob).flatten(), winner))
                # flip horizontally
                equi_state = np.array([np.fliplr(s) for s in equi_state])  # flip left and right
                equi_mcts_prob = np.fliplr(equi_mcts_prob)  # equi_mcts_prob need to flip left and right too
                extend_data.append((equi_state, np.flipud(equi_mcts_prob).flatten(), winner))
        return extend_data

    def save_model(self, win_ratio, epochs):
        # save model if necessary
        # if opponent is Rollout Player, then win_ratio > best_win_pure_so_far
        # if opponent is the Strongest Rollout Player, then win_ratio must be 1.0
        # else win_ratio >= win_ratio_alphazero
        if (self.config.evaluate_opponent == 'Pure' and win_ratio > self.config.best_win_pure_so_far) or \
                (
                        self.config.evaluate_opponent == 'Pure' and self.config.pure_mcts_playout_num == NUM_ROLLOUT and win_ratio == 1.0) or \
                (self.config.evaluate_opponent == 'AlphaZero' and win_ratio >= self.config.win_ratio_alphazero):
            print("New best policy!!!!!!!!")
            # load network parameters
            self.config.policy_param = self.policy_value_net.get_policy_param()  # get model params

            self.config.cur_best_alphazero_store_filename = root_data_file + "epochs-{0}-opponent-{1}-win-{2:.2f}.pkl".format(
                epochs,
                self.config.evaluate_opponent,
                win_ratio)
            # 检查并创建文件夹
            if not os.path.exists(root_data_file):
                print(f"Checkpoint Directory does not exist! Making directory {root_data_file}")
                os.makedirs(root_data_file)
            pickle.dump(self.config, open(self.config.cur_best_alphazero_store_filename, 'wb'))

        # ---------------Adjust Opponent---------------------#
        # Firstly, Make Rollout stronger(increase pure_mcts_playout_num)
        # Secondly, when RolloutPlayer is the strongest version(mcts_num=NUM_ROLLOUT) but still lose self.config change_opponent_continuous_times Times,
        # Then Change the opponent to AlphaZero Player

        # 别搞这些有的没的了，棋盘大了一点用都没有
        # # if opponent is RolloutPlayer, Then make it Stronger!!
        # if self.config.evaluate_opponent == 'Pure' and win_ratio > self.config.best_win_pure_so_far:
        #     if win_ratio == 1.0 and self.config.pure_mcts_playout_num < NUM_ROLLOUT:
        #         self.config.pure_mcts_playout_num += 1000  # stronger
        #         self.config.best_win_pure_so_far = 0.0  # reset win_ratio

        # current model continuously win(or tie) against the strongest pure mcts player(mcts_play_out>=NUM_ROLLOUT)
        if self.config.evaluate_opponent == 'Pure' and self.config.pure_mcts_playout_num >= NUM_ROLLOUT and win_ratio == 1.0:
            self.config.continuous_win_pure_times += 1

        # change the opponent
        if self.config.evaluate_opponent == 'Pure' and \
                self.config.continuous_win_pure_times >= self.config.change_opponent_continuous_times:
            print('Change Opponent:AlphaZero')
            self.config.evaluate_opponent = 'AlphaZero'

    def check_loss_change(self):
        '''
        check loss change every self.config.check_freq steps
        record the current minimum [mean loss of every self.config.check_freq steps]
        if the mean loss of every self.config.check_freq steps don't decrease for twice times comparing to the current minimum
        then decrease the learn_rate by half
        '''
        combined_loss_list = [loss['combined_loss'] for loss in self.config.loss_records]
        last_check_freq_mean_loss = np.mean(combined_loss_list[-self.config.check_freq:])
        if self.config.min_mean_loss_every_check_freq is None or \
                last_check_freq_mean_loss < self.config.min_mean_loss_every_check_freq:
            if self.config.min_mean_loss_every_check_freq is not None:
                print('decrease loss by {0:.4f}'.format(
                    self.config.min_mean_loss_every_check_freq - last_check_freq_mean_loss))
            self.config.min_mean_loss_every_check_freq = last_check_freq_mean_loss  # update
            self.config.increase_mean_loss_times = 0  # reset to zero
        else:
            print('increase loss by {0:.4f}'.format(
                last_check_freq_mean_loss - self.config.min_mean_loss_every_check_freq))
            self.config.increase_mean_loss_times += 1

        if self.config.increase_mean_loss_times >= self.config.adjust_lr_increase_loss_times:
            self.config.learn_rate /= 10  # decrease init lr by half
            self.config.kl_targ /= 10  # decrease kl_targ, so that the lr tends to be smaller
            # self.config.increase_mean_loss_times = 0 # reset again
            print('decrease lr by half, now init lr is {0:.5f}'.format(self.config.learn_rate))

    def run(self):
        """run the training pipeline"""
        print("start training from game:{}".format(self.config.start_game_num))
        logging_initialize()

        try:
            for i in trange(self.config.game_batch_num):
                if i < self.config.start_game_num:  # 这样写为了trange可以看出来训练了总量的多少
                    continue

                self.self_play(self.config.play_batch_size)  # big step 1
                print("iteration i:{}, episode_len:{}, augmented_len:{}, current_buffer_len:{}".format(i + 1,
                                                                                                       self.episode_len,
                                                                                                       self.augmented_len,
                                                                                                       len(self.config.data_buffer)))
                # new Added parameters,So check for old config file
                if not hasattr(self.config, "episode_records"):
                    setattr(config, "episode_records", [])  # setattr(x, 'y', v) is equivalent to ``x.y = v''
                self.config.episode_records.append(self.episode_len)

                if len(self.config.data_buffer) > self.config.batch_size:
                    loss_info = self.optimize(iteration=i + 1)  # big step 2

                    # tensorboard
                    self.monitor.log(loss_info['combined_loss'], 'loss')
                    self.monitor.log(loss_info['value_loss'], 'value_loss')
                    self.monitor.log(loss_info['policy_loss'], 'policy_loss')
                    self.monitor.log(loss_info['entropy'], 'entropy')

                    self.config.loss_records.append(loss_info)

                self.config.start_game_num = i + 1  # update for restart

                # check the performance of the current model，and save the model params
                if (i + 1) % self.config.check_freq == 0:
                    print("current iteration: {}".format(i + 1))
                    win_ratio = self.evaluate()  # big step 3
                    # self.check_loss_change() # check loss, and adjust init lr if necessary
                    self.save_model(win_ratio, i + 1)



        except KeyboardInterrupt:
            print('\n\rquit')


"""
tensorboard --logdir=D:\GitHub\AlphaZero_Gobang\out\logs 
"""
if __name__ == '__main__':
    # name = "epochs-500-opponent-Pure-win-1.00"  # 继续训练时要填这个
    name = input("请输入pkl文件名（无后缀）：")
    if name.lower() == "none":
        default = None  # 原先是None
        print("从空白网络开始训练")
    else:
        default = f"data/gomoku/{name}.pkl"
        print(f"加载{default}继续训练")

    parser = argparse.ArgumentParser(description='AlphaZero Training....')
    parser.add_argument('--config', default=default, type=str,
                        help='config files to resume training....')
    args = parser.parse_args()
    # config = "tmp/epochs-{0}-opponent-{1}-win-{2:.2f}.pkl".format(360, 'AlphaZero', 0.60)
    config = None
    if args.config:
        config = pickle.load(open(args.config, 'rb'))  # resume from a checkpoint
    training_pipeline = TrainPipeline(config=config)
    training_pipeline.run()
