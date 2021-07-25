import argparse
import csv
import json

# settings
ap = argparse.ArgumentParser()

ap.add_argument("in_csv", type=argparse.FileType('r'), help="dataset CSV (time,sent_src,sent_tgt)")
ap.add_argument("out_json", type=argparse.FileType('w'), help="GPT2-Chinese input format")

args = ap.parse_args()

csv_reader = csv.DictReader(args.in_csv, delimiter=',', fieldnames=["time", "sent_src", "sent_tgt"])
text_list = []
for row in csv_reader:
    #print(row)
    text_list.append( "[zh_a]" + row["sent_src"] + "[zh_m]" + row["sent_tgt"] + "[chron]" + row["time"] )

json.dump(text_list, args.out_json, ensure_ascii=False)
