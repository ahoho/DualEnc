#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import division
import six
import sys
import numpy as np
import argparse
import torch


def get_vocabs(dict_file):
    vocabs = torch.load(dict_file)

    enc_vocab, enc_vocab2, dec_vocab = None, None, None

    # the vocab object is a list of tuple (name, torchtext.Vocab)
    # we iterate over this list and associate vocabularies based on the name
    for vocab in vocabs:
        if vocab[0] == 'src':
            enc_vocab = vocab[1]
        if vocab[0] == 'src2':
            enc_vocab2 = vocab[1]
        if vocab[0] == 'tgt':
            dec_vocab = vocab[1]

    print(enc_vocab)
    print(enc_vocab2)
    print(dec_vocab)
    if enc_vocab is None or dec_vocab is None:
        exit()
    #assert None not in [enc_vocab, dec_vocab]

    print("From: %s" % dict_file)
    print("\t* source vocab: %d words" % len(enc_vocab))
    print("\t* source vocab 2: %d words" % len(enc_vocab2))
    print("\t* target vocab: %d words" % len(dec_vocab))

    return enc_vocab, enc_vocab2, dec_vocab


def get_embeddings(file, opt):
    embs = dict()

    for (i, l) in enumerate(open(file, 'rb')):
        if i < opt.skip_lines:
            continue
        if not l:
            break
        if len(l) == 0:
            continue

        l_split = l.decode('utf8').strip().split()
        if len(l_split) == 2:
            continue
        embs[l_split[0]] = [float(em) for em in l_split[1:]]
    print("Got {} embeddings from {}".format(len(embs), file))

    return embs


def match_embeddings(vocab, emb, opt):
    dim = len(six.next(six.itervalues(emb)))
    filtered_embeddings = np.zeros((len(vocab), dim))
    count = {"match": 0, "miss": 0}
    for w, w_id in vocab.stoi.items():
        if w in emb:
            filtered_embeddings[w_id] = emb[w]
            count['match'] += 1
        else:
            if opt.verbose:
                print(u"not found:\t{}".format(w), file=sys.stderr)
            count['miss'] += 1

    return torch.Tensor(filtered_embeddings), count


TYPES = ["GloVe", "word2vec"]


def main():

    parser = argparse.ArgumentParser(description='embeddings_to_torch.py')
    parser.add_argument('-emb_file', required=True,
                        help="Embeddings from this file")
    parser.add_argument('-output_file', required=True,
                        help="Output file for the prepared data")
    parser.add_argument('-dict_file', required=True,
                        help="Dictionary file")
    parser.add_argument('-verbose', action="store_true", default=False)
    parser.add_argument('-skip_lines', type=int, default=0,
                        help="Skip first lines of the embedding file")
    parser.add_argument('-type', choices=TYPES, default="GloVe")
    opt = parser.parse_args()

    enc_vocab, enc_vocab2, dec_vocab = get_vocabs(opt.dict_file)
    if opt.type == "word2vec":
        opt.skip_lines = 1

    embeddings = get_embeddings(opt.emb_file, opt)

    filtered_enc_embeddings, enc_count = match_embeddings(enc_vocab,
                                                          embeddings,
                                                          opt)
    filtered_enc_embeddings2, enc_count2 = match_embeddings(enc_vocab2,
                                                          embeddings,
                                                          opt)
    filtered_dec_embeddings, dec_count = match_embeddings(dec_vocab,
                                                          embeddings,
                                                          opt)

    print("\nMatching: ")
    match_percent = [_['match'] / (_['match'] + _['miss']) * 100
                     for _ in [enc_count,enc_count2, dec_count]]
    print("\t* enc: %d match, %d missing, (%.2f%%)" % (enc_count['match'],
                                                       enc_count['miss'],
                                                       match_percent[0]))
    print("\t* enc2: %d match, %d missing, (%.2f%%)" % (enc_count2['match'],
                                                       enc_count2['miss'],
                                                       match_percent[1]))
    print("\t* dec: %d match, %d missing, (%.2f%%)" % (dec_count['match'],
                                                       dec_count['miss'],
                                                       match_percent[2]))

    print("\nFiltered embeddings:")
    print("\t* enc: ", filtered_enc_embeddings.size())
    print("\t* enc2: ", filtered_enc_embeddings2.size())
    print("\t* dec: ", filtered_dec_embeddings.size())

    enc_output_file = opt.output_file + ".enc.pt"
    enc2_output_file = opt.output_file + ".enc2.pt"
    dec_output_file = opt.output_file + ".dec.pt"
    print("\nSaving embedding as:\n\t* enc: %s\n\t* enc2: %s\n\t* dec: %s"
          % (enc_output_file, enc2_output_file, dec_output_file))
    torch.save(filtered_enc_embeddings, enc_output_file)
    torch.save(filtered_enc_embeddings2, enc2_output_file)
    torch.save(filtered_dec_embeddings, dec_output_file)
    print("\nDone.")


if __name__ == "__main__":
    main()
