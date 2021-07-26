import transformers
import torch
import os
import json
import random
import numpy as np
import argparse
from datetime import datetime
from tqdm import tqdm
from torch.nn import DataParallel

import csv


def build_files(data_path, tokenized_data_path, num_pieces, full_tokenizer, min_length):
    if not os.path.exists(tokenized_data_path):
        os.mkdir(tokenized_data_path)
    with open(data_path, 'r', encoding='utf8') as f:
        print('reading lines')
        lines = json.load(f)
        all_len = len(lines)
    for i in tqdm(range(num_pieces)):
        sublines = lines[all_len // num_pieces * i: all_len // num_pieces * (i + 1)]
        if i == num_pieces - 1:
            sublines.extend(lines[all_len // num_pieces * (i + 1):])  # 把尾部例子添加到最后一个piece
        sublines = [full_tokenizer.tokenize(line) for line in sublines if
                    len(line) > min_length]  # 只考虑长度超过min_length的句子
        sublines = [full_tokenizer.convert_tokens_to_ids(line) for line in sublines]
        full_line = []
        for subline in sublines:
            full_line.append(full_tokenizer.convert_tokens_to_ids('[MASK]'))  # 文章开头添加MASK表示文章开始
            full_line.extend(subline)
            full_line.append(full_tokenizer.convert_tokens_to_ids('[CLS]'))  # 文章之间添加CLS表示文章结束
        with open(tokenized_data_path + 'tokenized_train_{}.txt'.format(i), 'w') as f:
            for id in full_line:
                f.write(str(id) + ' ')
    print('finish')


def main():
    parser = argparse.ArgumentParser()
    
    parser.add_argument('in_tsv', type=argparse.FileType('r'), help='TSV ouput by score_fairseq_hyp_nbest.py, [id, GPT-2_score, fairseq_score, hypothesis]')
    parser.add_argument('n', type=int, help='fairseq-generate --nbest, every n lines are for same source')
    parser.add_argument('src_file', type=argparse.FileType('r'), help='source file')
    parser.add_argument('out_tsv', type=argparse.FileType('w'), help='output TSV with time prob. for each candidates, [id, p1,p2,p3, GPT-2_score, fairseq_score, hypothesis]')

    parser.add_argument('--device', default='0,1,2,3', type=str, required=False, help='设置使用哪些显卡')
    parser.add_argument('--model_config', default='config/model_config_small.json', type=str, required=False,
                        help='选择模型参数')
    parser.add_argument('--tokenizer_path', default='cache/vocab_small.txt', type=str, required=False, help='选择词库')
    #parser.add_argument('--raw_data_path', default='data/eval.json', type=str, required=False, help='原始语料')
    #parser.add_argument('--tokenized_data_path', default='data/tokenized_eval/', type=str, required=False,
    #                    help='tokenized语料存放位置')
    #parser.add_argument('--raw', action='store_true', help='是否先做tokenize')
    #parser.add_argument('--batch_size', default=8, type=int, required=False, help='batch size')
    parser.add_argument('--log_step', default=1, type=int, required=False, help='多少步汇报一次')
    #parser.add_argument('--stride', default=768, type=int, required=False, help='取数据的窗口步长')
    #parser.add_argument('--num_pieces', default=100, type=int, required=False, help='将训练语料分成多少份')
    #parser.add_argument('--min_length', default=128, type=int, required=False, help='最短收录文章长度')
    parser.add_argument('--pretrained_model', default='', type=str, required=False, help='模型起点路径')
    #parser.add_argument('--output_dir', default='eval_result/', type=str, required=False, help='结果输出路径')

    args = parser.parse_args()
    print('args:\n' + args.__repr__())

    # if args.no_wordpiece:
    #     from tokenizations import tokenization_bert_without_wordpiece as tokenization_bert
    # else:
    from tokenizations import tokenization_bert

    os.environ["CUDA_VISIBLE_DEVICES"] = args.device  # 此处设置程序使用哪些显卡

    model_config = transformers.modeling_gpt2.GPT2Config.from_json_file(args.model_config)
    print('config:\n' + model_config.to_json_string())

    n_ctx = model_config.n_ctx
    full_tokenizer = tokenization_bert.BertTokenizer(vocab_file=args.tokenizer_path)
    full_tokenizer.max_len = n_ctx
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print('using device:', device)

    #raw_data_path = args.raw_data_path
    #tokenized_data_path = args.tokenized_data_path
    #raw = args.raw  # 选择是否从零开始构建数据集
    #batch_size = args.batch_size
    log_step = args.log_step
    #stride = args.stride
    #num_pieces = args.num_pieces
    #min_length = args.min_length
    #output_dir = args.output_dir
    
    if not args.pretrained_model:
        print('you need to specify a trained model.')
        exit(1)
    else:
        model = transformers.modeling_gpt2.GPT2LMHeadModel.from_pretrained(args.pretrained_model)
    model.eval()
    model.to(device)

    num_parameters = 0
    parameters = model.parameters()
    for parameter in parameters:
        num_parameters += parameter.numel()
    print('number of parameters: {}'.format(num_parameters))

    multi_gpu = False
    
    if torch.cuda.device_count() > 1:
        print("Let's use", torch.cuda.device_count(), "GPUs!")
        model = DataParallel(model)
        multi_gpu = True
    print('starting training')
    overall_step = 0

    total_loss = 0
    total_steps = 0
    #  eval
    now = datetime.now()
    print('time: {}'.format(now))
    
    # load source sentences
    src_untok_list = []
    for line in args.src_file:
        src_untok_list.append(line.strip().replace(' ', ''))

    src_p = 0
    cnt = 0
    tsv_reader = csv.reader(args.in_tsv, delimiter='\t')
    tsv_writer = csv.writer(args.out_tsv, delimiter='\t')
    out_row_buff = []
    for row in tsv_reader:
        hyp = row[-1]
        hyp_untok = hyp.replace(' ', '')
    
        src_untok = src_untok_list[src_p]

        prob_str_list = []
        for period in ["pre-qin", "han", "song"]:
            query_str = "[CLS][MASK][zh_a]{}[zh_m]{}[chron]{}[CLS][MASK]".format(src_untok, hyp_untok, period)
            query_tokens = full_tokenizer.tokenize(query_str)
            query_token_ids = full_tokenizer.convert_tokens_to_ids(query_tokens)

            #  prepare data
            batch = [ query_token_ids ]
            batch_labels = []
            batch_inputs = []
            for ids in batch:
                int_ids_for_labels = [int(x) for x in ids]
                int_ids_for_inputs = [int(x) for x in ids]
                batch_labels.append(int_ids_for_labels)
                batch_inputs.append(int_ids_for_inputs)
            batch_labels = torch.tensor(batch_labels).long().to(device)
            batch_inputs = torch.tensor(batch_inputs).long().to(device)

            #  forward pass
            outputs = model.forward(input_ids=batch_inputs, labels=batch_labels)
            loss, logits = outputs[:2]
            
            loss = loss.item()
            ### loss=cross-entropy=(-1/N)log P(w1, ..., w_N)
            lm_score = -loss
            print(query_str, lm_score)

            prob_str_list.append("{:.4f}".format(lm_score))
        tsv_writer.writerow([row[0], ','.join(prob_str_list)] + row[1:]) # id  GPT-2_period_scores  GPT-2_score  farseq_score  hypothesis

        cnt += 1
        if cnt % args.n == 0:
            # increment source list pointer
            src_p += 1

if __name__ == '__main__':
    main()
