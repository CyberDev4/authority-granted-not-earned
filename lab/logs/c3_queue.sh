cd ~/ai-lab/project/agentscope && source .venv/bin/activate
echo "$(date) waiting for granite controls"; while pgrep -f "granite3.3:8b --stage controls" >/dev/null; do sleep 30; done
echo "$(date) granite probe"; bash gne_c3/c3.sh probe granite3.3:8b > logs/c3_granite_probe.out 2>&1
ollama stop granite3.3:8b
echo "$(date) llama follow-up (H3)"; bash gne_c3/c3.sh followup llama3.1:8b > logs/c3_llama_followup.out 2>&1
ollama stop llama3.1:8b
echo "$(date) waiting for qwen2.5:7b main"; while pgrep -f "qwen2.5:7b --stage main" >/dev/null; do sleep 60; done
ollama stop qwen2.5:7b
echo "$(date) qwen2.5:14b all stages"; bash gne_c3/c3.sh all qwen2.5:14b > logs/c3_qwen14b_all.out 2>&1
echo "$(date) QUEUE DONE"
