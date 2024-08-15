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


### SSE
```json
[
    {"event_id": 1, "message": "Have successfully set up llm provider", "is_done": false, "code": 200},
    {"event_id": 2, "message": "I am brain**STORM**ing now to research the topic. (This may take 2-3 minutes.)", "is_done": false, "code": 200},
    {"event_id": 3, "message": "brain ** STORM ** ing complete!", "is_done": false, "code": 200},
    {"event_id": 4, "message": "Now I will connect the information I found for your reference. (This may take 4-5 minutes.)", "is_done": false, "code": 200},
    {"event_id": 5, "message": "information synthesis complete!", "is_done": false, "code": 200},
    {"event_id": 6, "message": "Updating article in database", "code": 200, "is_done": false},
    {"event_id": 7, "message": "Have successfully uploaded to db, sending article content back!", "is_done": true, "code": 200}
]
```


### Citations
```bibtex
@inproceedings{shao2024assisting,
      title={{Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models}}, 
      author={Yijia Shao and Yucheng Jiang and Theodore A. Kanell and Peter Xu and Omar Khattab and Monica S. Lam},
      year={2024},
      booktitle={Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers)}
}
```