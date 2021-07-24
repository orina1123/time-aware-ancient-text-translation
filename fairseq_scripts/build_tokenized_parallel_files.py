import argparse
import csv
import json

# settings
ap = argparse.ArgumentParser()

ap.add_argument("in_csv", type=argparse.FileType('r'), help="dataset CSV (...,sent_src,sent_tgt)")
ap.add_argument("out_prefix", type=str, help="write source and target side to separate files <out_prefix>.{source_lang, target_lang}")
ap.add_argument("--source-lang", type=str, default="zh_a", help="source language tag (for file extension)")
ap.add_argument("--target-lang", type=str, default="zh_m", help="target language tag (for file extension)")

args = ap.parse_args()

args.in_csv.readline() # ...,sent_src,sent_tgt
csv_reader = csv.reader(args.in_csv, delimiter=',')
f_src = open("{}.{}".format(args.out_prefix, args.source_lang), "w")
f_tgt = open("{}.{}".format(args.out_prefix, args.target_lang), "w")
for row in csv_reader:
    f_src.write(' '.join([ c for c in row[-2] ]) + '\n')
    f_tgt.write(' '.join([ c for c in row[-1] ]) + '\n')
