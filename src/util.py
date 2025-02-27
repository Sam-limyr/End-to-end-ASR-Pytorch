import matplotlib.pyplot as plt
import math
import time
import torch
import numpy as np
from torch import nn
import editdistance as ed

import matplotlib
matplotlib.use('Agg')


class Timer():
    ''' Timer for recording training time distribution. '''

    def __init__(self):
        self.prev_t = time.time()
        self.clear()

    def set(self):
        self.prev_t = time.time()

    def cnt(self, mode):
        self.time_table[mode] += time.time()-self.prev_t
        self.set()
        if mode == 'bw':
            self.click += 1

    def show(self):
        total_time = sum(self.time_table.values())
        self.time_table['avg'] = total_time/self.click
        self.time_table['rd'] = 100*self.time_table['rd']/total_time
        self.time_table['fw'] = 100*self.time_table['fw']/total_time
        self.time_table['bw'] = 100*self.time_table['bw']/total_time
        msg = '{avg:.3f} sec/step (rd {rd:.1f}% | fw {fw:.1f}% | bw {bw:.1f}%)'.format(
            **self.time_table)
        self.clear()
        return msg

    def clear(self):
        self.time_table = {'rd': 0, 'fw': 0, 'bw': 0}
        self.click = 0

# Reference : https://github.com/espnet/espnet/blob/master/espnet/nets/pytorch_backend/e2e_asr.py#L168

ann_classifier_warning_sounded = False

def init_weights(module):
    # Exceptions
    if type(module) == nn.Embedding:
        module.weight.data.normal_(0, 1)
    else:
        for p in module.parameters():
            data = p.data
            if data.dim() == 1:
                # bias
                data.zero_()
            elif data.dim() == 2:
                # linear weight
                n = data.size(1)
                stdv = 1. / math.sqrt(n)
                data.normal_(0, stdv)
            elif data.dim() in [3, 4]:
                # conv weight
                n = data.size(1)
                for k in data.size()[2:]:
                    n *= k
                stdv = 1. / math.sqrt(n)
                data.normal_(0, stdv)
            elif data.dim() == 5:
                global ann_classifier_warning_sounded
                if not ann_classifier_warning_sounded:
                    print("\n\nIgnore this warning if ANNClassifier is being used:\nParameter dimension is 5 in init_weights(), src/util.py line 48, called in asr.py line 48.\n\n\n")
                    ann_classifier_warning_sounded = True
            else:
                raise NotImplementedError


def init_gate(bias):
    n = bias.size(0)
    start, end = n // 4, n // 2
    bias.data[start:end].fill_(1.)
    return bias

# Convert Tensor to Figure on tensorboard


def feat_to_fig(feat):
    # feat TxD tensor
    data = _save_canvas(feat.numpy())
    return torch.FloatTensor(data), "HWC"


def _save_canvas(data, meta=None):
    fig, ax = plt.subplots(figsize=(16, 8))
    if meta is None:
        ax.imshow(data, aspect="auto", origin="lower")
    else:
        ax.bar(meta[0], data[0], tick_label=meta[1], fc=(0, 0, 1, 0.5))
        ax.bar(meta[0], data[1], tick_label=meta[1], fc=(1, 0, 0, 0.5))
    fig.canvas.draw()
    # Note : torch tb add_image takes color as [0,1]
    data = np.array(fig.canvas.renderer._renderer)[:, :, :-1]/255.0
    plt.close(fig)
    return data

# Reference : https://stackoverflow.com/questions/579310/formatting-long-numbers-as-strings-in-python


def human_format(num):
    magnitude = 0
    while num >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '{:3.1f}{}'.format(num, [' ', 'K', 'M', 'G', 'T', 'P'][magnitude])


def cal_er(tokenizer, pred, truth, mode='wer', ctc=False):
    # Calculate error rate of a batch
    if pred is None:
        return np.nan
    elif len(pred.shape) >= 3:
        pred = pred.argmax(dim=-1)
    er = []
    for p, t in zip(pred, truth):
        p = tokenizer.decode(p.tolist(), ignore_repeat=ctc)
        t = tokenizer.decode(t.tolist())
        if mode == 'wer':
            p = p.split(' ')
            t = t.split(' ')
        er.append(float(ed.eval(p, t))/len(t)) # can be larger than 1 due to insertion error
    return sum(er)/len(er)


def load_embedding(text_encoder, embedding_filepath):
    with open(embedding_filepath, "r") as f:
        vocab_size, embedding_size = [int(x)
                                      for x in f.readline().strip().split()]
        embeddings = np.zeros((text_encoder.vocab_size, embedding_size))

        unk_count = 0

        for line in f:
            vocab, emb = line.strip().split(" ", 1)
            # fasttext's <eos> is </s>
            if vocab == "</s>":
                vocab = "<eos>"

            if text_encoder.token_type == "subword":
                idx = text_encoder.spm.piece_to_id(vocab)
            else:
                # get rid of <eos>
                idx = text_encoder.encode(vocab)[0]

            if idx == text_encoder.unk_idx:
                unk_count += 1
                embeddings[idx] += np.asarray([float(x)
                                               for x in emb.split(" ")])
            else:
                # Suppose there is only one (w, v) pair in embedding file
                embeddings[idx] = np.asarray(
                    [float(x) for x in emb.split(" ")])

        # Average <unk> vector
        if unk_count != 0:
            embeddings[text_encoder.unk_idx] /= unk_count

        return embeddings
