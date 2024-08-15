# storm-server

## Context
Based implementation of [Storm](https://github.com/stanford-oval/storm)

## Used
```
FastAPI + Storm + Mysql
```

### Config
```sh
cp .env.example .env
```

### Database
```sh
./db/init_data.sql
```

### Install
```sh
pip install -r requirements.txt
```

### Start
```sh
#local
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

### Docs
* http://127.0.0.1:8080/api/v1/docs
* http://127.0.0.1:8080/api/v1/redoc

### Citations
```bibtex
@inproceedings{shao2024assisting,
      title={{Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models}}, 
      author={Yijia Shao and Yucheng Jiang and Theodore A. Kanell and Peter Xu and Omar Khattab and Monica S. Lam},
      year={2024},
      booktitle={Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers)}
}
```