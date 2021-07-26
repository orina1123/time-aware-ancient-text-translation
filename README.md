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
In `zh_a-zh_m.{train,dev,test}.csv`, the last two columns `sent_src` and `sent_tgt` should contain the ancient Chinese setences and the corresponding modern Chinese translations repectively. The above commands will produce the following files that can be taken by `fairseq-preprocess` as input:
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
* `output.json` will be in the format that can be taken by `GPT2-Chinese/train.py`. The JSON object will be a list of training instances, each of which is a string `[zh_a] sent_src [zh_m] sent_tgt [chron] time`.

Example:
```
python build_zh_a-zh_m-chron_json.py zh_a-zh_m.profile.train.csv ancient-modern-time.train.json
python build_zh_a-zh_m-chron_json.py zh_a-zh_m.profile.dev.csv ancient-modern-time.dev.json
```
The above commands produce the train and development JSON files that can be passed as the value of the `--raw_data_path` argument of the `GPT2-Chinese` training scripts.

#### Rerank Translation Candidates with GPT-2
First, generate n-best translation candidates with `fairseq-generate`. Then, use the following scripts to obtain LM scores of each candidate.
* `score_hyp_nbest.py`: rank candidates by scoring strings `[zh_a] sent_src [zh_m] sent_tgt [chron]`, without considering chronology information
* `score_hyp_nbest_with_period.py`: time-aware ranking by scoring strings `[zh_a] sent_src [zh_m] sent_tgt [chron] time` for all possible values of `time`

Example:
Let `test.hyp5` be the output of `fairseq-generate` with `N=5` candidates per sentence.

The following command reranks the candidates by considering source sentences (in `test.zh_a`) and the candidates.
```
python score_hyp_nbest.py test.hyp5 5 /path/to/test.zh_a test.hyp5.gpt2-rerank \
        --pretrained_model /path/to/fine_tuned/gpt2_model/
```
The output file `test.hyp5.gpt2-rerank` will be a TSV like this:
```
3       -1.9268633127212524     -0.6304359436035156     子 胥 回 答 说 ： 大 王 不 喜 欢 ！
3       -1.986321210861206      -0.4897662401199341     子 胥 说 ： 大 王 不 喜 欢 ！
3       -2.1779110431671143     -0.50040602684021       伍 子 胥 说 ： 大 王 不 喜 欢 ！
3       -2.3064706325531006     -0.6741451025009155     伍 子 胥 回 答 说 ： 大 王 不 喜 ！
3       -2.3135294914245605     -0.5642138123512268     伍 子 胥 说 ： 大 王 不 喜 ！
```
The 2nd column is the GPT-2 LM score (normalized log probability) and the 3rd column is the original hypothesis score provided by `fairseq-generate`. Every `N` lines (with the same sentence id indicated by the 1st column) are sorted by the GPT-2 scores in decending order, so the first candidate will be selected after reranking.

Similarly, the following command performs time-aware reranking.
```
python score_hyp_nbest_with_period.py test.hyp5.gpt2-rerank 5 /path/to/test.zh_a test.hyp5.gpt2-period-rerank \
        --pretrained_model /path/to/fine_tuned/gpt2_model/
```
The output file `test.hyp5.gpt2-period-rerank` will be a TSV with all columns in `test.hyp5.gpt2-rerank` and an additional column inserted right after the sentence id column. This column contains three values indicating the GPT-2 LM scores when the source sentence and the translation candidate are associated with time period `pre-qin`, `han` and `song` respectively. These scores can be used for chronology inference and time-aware reranking. In the following example, since the highest time-aware LM score is `-1.7751`, the first translation candidate `子 胥 回 答 说 ： 大 王 不 喜 欢 ！` will be selected and the chronological period prediction will be `han`.
```
3       -1.8583,-1.7751,-1.8961 -1.9268633127212524     -0.6304359436035156     子 胥 回 答 说 ： 大 王 不 喜 欢 ！
3       -1.8925,-1.8212,-1.9475 -1.986321210861206      -0.4897662401199341     子 胥 说 ： 大 王 不 喜 欢 ！
3       -2.0852,-2.0016,-2.1322 -2.1779110431671143     -0.50040602684021       伍 子 胥 说 ： 大 王 不 喜 欢 ！
3       -2.2085,-2.1246,-2.2645 -2.3064706325531006     -0.6741451025009155     伍 子 胥 回 答 说 ： 大 王 不 喜 ！
3       -2.1959,-2.1210,-2.2644 -2.3135294914245605     -0.5642138123512268     伍 子 胥 说 ： 大 王 不 喜 ！
```
