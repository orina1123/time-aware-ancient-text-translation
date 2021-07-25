# Time-aware Ancient Text Translation and Inference
This repository containts code and data for the paper "Time-Aware Ancient Chinese Text Translation and Inference" (LChange'21).
If you use any resources here, please cite our paper as follows:
> Ernie Chang, Yow-Ting Shiue, Hui-Syuan Yeh and Vera Demberg. 2021. [Time-Aware Ancient Chinese Text Translation and Inference](https://arxiv.org/abs/2107.03179). *arXiv preprint arXiv:1712.05690*.
```
@article{chang2021timeaware,
      title={Time-Aware Ancient Chinese Text Translation and Inference}, 
      author={Ernie Chang and Yow-Ting Shiue and Hui-Syuan Yeh and Vera Demberg},
      journal={arXiv preprint arXiv:2107.03179},
      year={2021}
}
```
Accepted by the 2nd International Workshop on Computational Approaches to Historical Language Change (LChange'21).

## Data
The train/development/test sets used in our ancient Chinese experiments can be found in the `data/` directory. Each CSV file has the following columns:
* `time`: the historic time period of the sentence in the `sent_src` column. In this dataset, the value is one of `pre-qin`(先秦), `han`(漢) and `song`(宋).
* `sent_src`: the ancient sentence, which is the source sentence that will be translated.

Note that to train and evaluate the model with the provided code, you need to obtain modern Chinese translation for each sentence and put it in an additional column `sent_tgt`.
In our experiments, the modern Chinese translations were obtained from [Liu et al., 2019](https://dl.acm.org/doi/abs/10.1145/3325887) and [Shang et al., 2019](http://dx.doi.org/10.18653/v1/D19-1499).

## Code
We provide the scripts used to prepare data for training and process output for evaluation. The scripts are written in Python. You can view the usage of each script by passing the `-h` argument.

### Ancient-to-Modern Text Translation
The `fairseq-scripts/` directory contains the scripts we used to process data for [Fairseq](https://github.com/pytorch/fairseq/), the toolkit we utilized to build the translation model. Chronology information is not required in this step.

To prepare the parallel data for training, run the following command for the train, dev and test CSV files respectively.
```
python build_tokenized_parallel_files.py /path/to/input.csv /path/to/output_prefix [--source-lang SOURCE_LANG (default: zh_a)] [--target-lang TARGET_LANG (default: zh_m)]
```
* `input.csv` is a CSV file whose last two columns contain the source (ancient) and target (modern) sentences.
* The script will tokenize the sentences by splitting characters and produce parallel files `/path/to/output_prefix.[SOURCE_LANG|TARGET_LANG]`.

Example:
```
python build_tokenized_parallel_files.py zh_a-zh_m.train.csv train
python build_tokenized_parallel_files.py zh_a-zh_m.dev.csv dev
python build_tokenized_parallel_files.py zh_a-zh_m.test.csv test
```
The last two columns of `zh_a-zh_m.{train,dev,test}.csv`, `sent_src` and `sent_tgt`, should contain the ancient Chinese setences and the corresponding modern Chinese translations repectively.
The above commands will produce the following files that can be taken by `fairseq-preprocess` as input:
```
train.zh_a
train.zh_m
dev.zh_a
dev.zh_m
test.zh_a
test.zh_m
```
Additional monolingual ancient/modern sentences can be added to the source/target side. In our experiments, we used the same nonparallel data as [Shang et al., 2019](http://dx.doi.org/10.18653/v1/D19-1499).

### Chronology Inference with Large-scale LM
We leveraged GPT-2 to perform chronology inference and select better translations. To repeat the experiments, clone the [GPT2-Chinese](https://github.com/Morizeyao/GPT2-Chinese) repository and put all the `.py` files in `GPT2_scripts/` into the root directory of the cloned repository.

#### Prepare Chronologically-annotated Data for Fine-tuning GPT-2
The following command converts a CSV file with chronologically-annotated sentence pairs to a JSON file that can be used to fine-tune a pretrained GPT-2 model.
```
python build_zh_a-zh_m-chron_json.py /path/to/input.csv /path/to/output.json
```
* `input.csv` is the train/development CSV file with columns `time`, `sent_src` and `sent_tgt`.
* `output.json` will be in the format that can be taken by `GPT2-Chinese/train.py`. Each training instance is a string 
`[zh_a] sent_src [zh_m] sent_tgt [chron] time`.

Example:
```
python build_zh_a-zh_m-chron_json.py zh_a-zh_m.profile.train.csv ancient-modern-time.train.json
python build_zh_a-zh_m-chron_json.py zh_a-zh_m.profile.dev.csv ancient-modern-time.dev.json
```
The above commands produce the train and development JSON files that can be passed as the value of the `--raw_data_path` argument of the `GPT2-Chinese` training scripts.

#### Rerank Translation Candidates with GPT-2
#TODO
