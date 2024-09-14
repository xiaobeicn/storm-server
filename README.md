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
python main.py
```

### Docs
* http://127.0.0.1:8080/api/v1/docs

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

### Logging
```text
***** Execution time *****
run_knowledge_curation_module: 116.6072 seconds
run_outline_generation_module: 9.6553 seconds
run_article_generation_module: 38.8765 seconds
run_article_polishing_module: 7.7596 seconds
***** Token usage of language models: *****
run_knowledge_curation_module
    gpt-4o-mini-2024-07-18: {'prompt_tokens': 8377, 'completion_tokens': 3306}
    gpt-4o-2024-08-06: {'prompt_tokens': 0, 'completion_tokens': 0}
run_outline_generation_module
    gpt-4o-mini-2024-07-18: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4o-2024-08-06: {'prompt_tokens': 570, 'completion_tokens': 498}
run_article_generation_module
    gpt-4o-mini-2024-07-18: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4o-2024-08-06: {'prompt_tokens': 9253, 'completion_tokens': 3116}
run_article_polishing_module
    gpt-4o-mini-2024-07-18: {'prompt_tokens': 0, 'completion_tokens': 0}
    gpt-4o-2024-08-06: {'prompt_tokens': 3122, 'completion_tokens': 404}
***** Number of queries of retrieval models: *****
run_knowledge_curation_module: {'SerperRM': 9}
run_outline_generation_module: {'SerperRM': 0}
run_article_generation_module: {'SerperRM': 0}
run_article_polishing_module: {'SerperRM': 0}
```

### SSE
```text
data: {"state": "pre_writing", "is_done": false, "code": 200}

data: {"state": "identify_perspective_start", "is_done": false, "code": 200}

data: {"state": "identify_perspective_end", "is_done": false, "code": 200}

data: {"state": "information_gathering_start", "is_done": false, "code": 200}

data: {"state": "dialogue_turn_end", "is_done": false, "code": 200}

data: {"state": "dialogue_turn_end", "is_done": false, "code": 200}

data: {"state": "dialogue_turn_end", "is_done": false, "code": 200}

data: {"state": "information_gathering_start", "is_done": false, "code": 200}

data: {"state": "information_organization_start", "is_done": false, "code": 200}

data: {"state": "direct_outline_generation_end", "is_done": false, "code": 200}

data: {"state": "outline_refinement_end", "is_done": false, "code": 200}

data: {"state": "pre_writing_end", "is_done": false, "code": 200}

data: {"state": "generate_article_end", "is_done": false, "code": 200}

data: {"state": "completed", "is_done": true, "code": 200}
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