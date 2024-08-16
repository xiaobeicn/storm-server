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
conda create -n storm-server python=3.11
conda activate storm-server
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

### Openapi - check_sensitive_info
```json
{
    "id": "chatcmpl-9wgLzyUVgvTmZ3gOMveN4K4i4F6iA",
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null,
            "message": {
                "content": "No",
                "refusal": null,
                "role": "assistant",
                "function_call": null,
                "tool_calls": null
            }
        }
    ],
    "created": 1723772859,
    "model": "gpt-3.5-turbo-0125",
    "object": "chat.completion",
    "service_tier": null,
    "system_fingerprint": null,
    "usage": {
        "completion_tokens": 1,
        "prompt_tokens": 68,
        "total_tokens": 69
    }
}
```

### Run log
```text
Successfully current_working_dir:./output/user
Successfully set up engine args
Successfully get rm from you.com
Successfully get runner
openai._base_client : INFO     : Retrying request to /chat/completions in 0.766432 seconds
knowledge_storm.interface : INFO     : run_knowledge_curation_module executed in 109.1289 seconds
knowledge_storm.interface : INFO     : run_outline_generation_module executed in 26.3068 seconds
Have successfully finished the running research and generate_outline process
sentence_transformers.SentenceTransformer : INFO     : Use pytorch device_name: cpu
sentence_transformers.SentenceTransformer : INFO     : Load pretrained SentenceTransformer: paraphrase-MiniLM-L6-v2
knowledge_storm.interface : INFO     : run_article_generation_module executed in 17.6854 seconds
knowledge_storm.interface : INFO     : run_article_polishing_module executed in 7.2693 seconds
Have successfully finished the running generate_article and polish_article process
Have successfully finished the article generation process
***** Execution time *****
run_knowledge_curation_module: 109.1289 seconds
run_outline_generation_module: 26.3068 seconds
run_article_generation_module: 17.6854 seconds
run_article_polishing_module: 7.2693 seconds
***** Token usage of language models: *****
run_knowledge_curation_module
    gpt-3.5-turbo: {'prompt_tokens': 2557, 'completion_tokens': 790}
    gpt-4-1106-preview: {'prompt_tokens': 3390, 'completion_tokens': 1645}
    gpt-4-0125-preview: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4o-2024-05-13: {'prompt_tokens': 0, 'completion_tokens': 0}
run_outline_generation_module
    gpt-3.5-turbo: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4-1106-preview: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4-0125-preview: {'prompt_tokens': 1321, 'completion_tokens': 676}
    gpt-4o-2024-05-13: {'prompt_tokens': 0, 'completion_tokens': 0}
run_article_generation_module
    gpt-3.5-turbo: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4-1106-preview: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4-0125-preview: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4o-2024-05-13: {'prompt_tokens': 5299, 'completion_tokens': 2995}
run_article_polishing_module
    gpt-3.5-turbo: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4-1106-preview: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4-0125-preview: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4o-2024-05-13: {'prompt_tokens': 3186, 'completion_tokens': 526}
***** Number of queries of retrieval models: *****
run_knowledge_curation_module: {'YouRM': 9}
run_outline_generation_module: {'YouRM': 0}
run_article_generation_module: {'YouRM': 0}
run_article_polishing_module: {'YouRM': 0}
Finished running runner!
Article_output_dir: ./output/user/title
Fully parsed file, sending response back!
```

### Output file tree
```text
.
├── conversation_log.json
├── direct_gen_outline.txt
├── llm_call_history.jsonl
├── raw_search_results.json
├── run_config.json
├── storm_gen_article.txt
├── storm_gen_article_polished.txt
├── storm_gen_outline.txt
└── url_to_info.json
```

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