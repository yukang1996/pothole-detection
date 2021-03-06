import tensorflow as tf
import datetime
import os
import argparse
import yolo.config as cfg
from yolo.yolo_net import YOLONet
from utils.timer import Timer
from utils.pascal_voc import pascal_voc

def create_var_list(checkpoint_path):
    from tensorflow.python import pywrap_tensorflow
    reader = pywrap_tensorflow.NewCheckpointReader(checkpoint_path)
    var_to_shape_map = reader.get_variable_to_shape_map()
    print(reader)
    x=1
    for keys in var_to_shape_map:
    	print(x)
    	print('tensor_name',keys)
    	x+=1
    var_list = {}
    tvars = tf.trainable_variables()
    for i in range(54):
        if i == 0:
            key = 'Variable'
        else:
            key = 'Variable_'+str(i)

        if reader.get_tensor(key).shape == tvars[i].shape:
            var_list[key] = tvars[i]


    print(var_list)
    return var_list

class Solver(object):

    def __init__(self, net, data):
        self.net = net
        self.data = data
        self.weights_file = cfg.WEIGHTS_FILE
        self.max_iter = cfg.MAX_ITER
        self.initial_learning_rate = cfg.LEARNING_RATE
        self.decay_steps = cfg.DECAY_STEPS
        self.decay_rate = cfg.DECAY_RATE
        self.staircase = cfg.STAIRCASE
        self.summary_iter = cfg.SUMMARY_ITER
        self.save_iter = cfg.SAVE_ITER
        self.output_dir = os.path.join(
            cfg.OUTPUT_DIR, datetime.datetime.now().strftime('%Y_%m_%d_%H_%M'))
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.save_cfg()
        self.global_step = tf.get_variable(
           'global_step', [], initializer=tf.constant_initializer(0), trainable=False)
        # self.var_list = create_var_list(self.weights_file) 
        # self.variable_to_restore = tf.global_variables() #yk
        # self.restorer = tf.train.Saver(self.var_list, max_to_keep=None)  #yk
        # self.saver = tf.train.Saver(self.variable_to_restore, max_to_keep=None) #yk
        # self.saver = tf.train.Saver(max_to_keep=None) #yk
        self.ckpt_file = os.path.join(self.output_dir, 'save.ckpt')
        self.summary_op = tf.summary.merge_all()
        self.writer = tf.summary.FileWriter(self.output_dir, flush_secs=60)
        print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
        # self.global_step = tf.get_variable(
        #    'global_step', [], initializer=tf.constant_initializer(0), trainable=False)
        self.learning_rate = tf.train.exponential_decay(
            self.initial_learning_rate, self.global_step, self.decay_steps,
            self.decay_rate, self.staircase, name='learning_rate')
        self.optimizer = tf.train.GradientDescentOptimizer(
            learning_rate=self.learning_rate).minimize(
            self.net.total_loss, global_step=self.global_step)
        self.ema = tf.train.ExponentialMovingAverage(decay=0.9999)
        self.averages_op = self.ema.apply(tf.trainable_variables())
        with tf.control_dependencies([self.optimizer]):
            self.train_op = tf.group(self.averages_op)

        gpu_options = tf.GPUOptions()
        config = tf.ConfigProto(gpu_options=gpu_options)
        self.sess = tf.Session(config=config)
        self.sess.run(tf.global_variables_initializer())
        if self.weights_file is not None:
            print('Restoring weights from: ' + self.weights_file)
            self.restorer = tf.train.Saver() 
            # model = tf.train.latest_checkpoint('/home/jiahuei/Documents/Woh/pothole-detection/data/pascal_voc/output/2018_07_06_20_14/save.ckpt-6000')
            # model = '/home/jiahuei/Documents/Woh/YOLO_small.ckpt'
            model = '/home/jiahuei/Documents/Woh/pothole-detection/data/pascal_voc/output/2018_07_06_20_14/save.ckpt-6000'
            self.restorer.restore(self.sess, model)
            # self.restorer.restore(self.sess, self.weights_file)
            

        self.writer.add_graph(self.sess.graph)

    def train(self):

        train_timer = Timer()
        load_timer = Timer()

        for step in range(1, self.max_iter + 1):

            load_timer.tic()
            images, labels = self.data.get()
            print(images.shape, labels.shape)
            load_timer.toc()
            feed_dict = {self.net.images: images, self.net.labels: labels}

            train_timer.tic()
            summary_str, loss, _ = self.sess.run(
                [self.summary_op, self.net.total_loss, self.train_op],
                feed_dict=feed_dict)
            train_timer.toc()

            log_str = ('{} Epoch: {}, Step: {}, Learning rate: {},'
                ' Loss: {:5.3f}\nSpeed: {:.3f}s/iter,'
                ' Load: {:.3f}s/iter, Remain: {}').format(
                datetime.datetime.now().strftime('%m/%d %H:%M:%S'),
                self.data.epoch,
                int(step),
                round(self.learning_rate.eval(session=self.sess), 6),
                loss,
                train_timer.average_time,
                load_timer.average_time,
                train_timer.remain(step, self.max_iter))
            print(log_str)

            if step % self.summary_iter == 0:
                if step % (self.summary_iter * 10) == 0:

                    train_timer.tic()
                    summary_str, loss, _ = self.sess.run(
                        [self.summary_op, self.net.total_loss, self.train_op],
                        feed_dict=feed_dict)
                    train_timer.toc()

                    log_str = ('{} Epoch: {}, Step: {}, Learning rate: {},'
                        ' Loss: {:5.3f}\nSpeed: {:.3f}s/iter,'
                        ' Load: {:.3f}s/iter, Remain: {}').format(
                        datetime.datetime.now().strftime('%m/%d %H:%M:%S'),
                        self.data.epoch,
                        int(step),
                        round(self.learning_rate.eval(session=self.sess), 6),
                        loss,
                        train_timer.average_time,
                        load_timer.average_time,
                        train_timer.remain(step, self.max_iter))
                    print(log_str)

                else:
                    train_timer.tic()
                    summary_str, _ = self.sess.run(
                        [self.summary_op, self.train_op],
                        feed_dict=feed_dict)
                    train_timer.toc()

                self.writer.add_summary(summary_str, step)

            else:
                train_timer.tic()
                self.sess.run(self.train_op, feed_dict=feed_dict)
                train_timer.toc()

        if True:
            print('{} Saving checkpoint file to: {}'.format(
                datetime.datetime.now().strftime('%m/%d %H:%M:%S'),
                self.output_dir))
            self.saver.save(self.sess, self.ckpt_file,
                            global_step=self.global_step)    

    def save_cfg(self):

        with open(os.path.join(self.output_dir, 'config.txt'), 'w') as f:
            cfg_dict = cfg.__dict__
            for key in sorted(cfg_dict.keys()):
                if key[0].isupper():
                    cfg_str = '{}: {}\n'.format(key, cfg_dict[key])
                    f.write(cfg_str)


def update_config_paths(data_dir, weights_file):
    cfg.DATA_PATH = data_dir
    print('path'+cfg.DATA_PATH)
    cfg.PASCAL_PATH = os.path.join(data_dir, 'pascal_voc')
    cfg.CACHE_PATH = os.path.join(cfg.PASCAL_PATH, 'cache')
    cfg.OUTPUT_DIR = os.path.join(cfg.PASCAL_PATH, 'output')
    cfg.WEIGHTS_DIR = os.path.join(cfg.PASCAL_PATH, 'weights')

    cfg.WEIGHTS_FILE = os.path.join(cfg.WEIGHTS_DIR, weights_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', default="/home/jiahuei/Documents/Woh/pothole-detection/data/pascal_voc/output/2018_07_06_20_14/save.ckpt-6000", type=str)
    parser.add_argument('--data_dir', default="data", type=str)
    parser.add_argument('--threshold', default=0.2, type=float)
    parser.add_argument('--iou_threshold', default=0.5, type=float)
    parser.add_argument('--gpu', default='0', type=str)
    args = parser.parse_args()
    #if args.gpu is not None:
    #    cfg.GPU = args.gpu
    
    if args.data_dir != cfg.DATA_PATH:
        update_config_paths(args.data_dir, args.weights)

    os.environ['CUDA_VISIBLE_DEVICES'] = '0'

    yolo = YOLONet()
    pascal = pascal_voc('train')

    solver = Solver(yolo, pascal)

    print('Start training ...')
    solver.train()
    print('Done training.')

if __name__ == '__main__':

    # python train.py --weights YOLO_small.ckpt --gpu 0
    main()
