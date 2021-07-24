# Time-aware Ancient Text Translation and Inference
This repository containts code and data for the paper "Time-Aware Ancient Chinese Text Translation and Inference" (LChange'21).
If you use any resources here, please cite our paper as follows:
> Ernie Chang, Yow-Ting Shiue, Hui-Syuan Yeh and Vera Demberg. Time-Aware Ancient Chinese Text Translation and Inference. Proceedings of the 2nd International Workshop on Computational Approaches to Historical Language Change (LChange'21).
```
TODO
@inproceedings{chang-etal-2021-time-aware,
    title = "Time-Aware Ancient Chinese Text Translation and Inference",
    author = "Chang, Ernie  and
      Shiue, Yow-Ting  and
      Yeh, Hui-Syuan  and
      Demberg, Vera",
    booktitle = "Proceedings of the 2nd International Workshop on Computational Approaches to Historical Language Change",
    year = "2021",
    publisher = "Association for Computational Linguistics",
}
```
## Data
The train/development/test sets used in our ancient Chinese experiments can be found in `data/`. Each CSV file has the following columns:
* `time`: the historic time period of the sentence in the `sent_src` column. In this dataset, the value is one of `pre-qin`(先秦), `han`(漢) and `song`(宋).
* `sent_src`: the ancient sentence, which is the source sentence that will be translated.

Note that to train and evaluate the model with the provided code, you need to obtain modern Chinese translation for each sentence and put it in an additional column `sent_tgt`.
In our experiments, the modern Chinese translations were obtained from [Liu et al., 2019](https://dl.acm.org/doi/abs/10.1145/3325887) and [Shang et al., 2019](http://dx.doi.org/10.18653/v1/D19-1499).
