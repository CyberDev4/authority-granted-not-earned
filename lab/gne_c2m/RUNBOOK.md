# C2M runbook (mistral:7b)

Run from the project root (~/ai-lab/project/agentscope) with the venv active. Nothing touches C1 or C2.

1. `bash gne_c2m/c2m.sh check`: 25 tests OK, mistral:7b listed.
2. `bash gne_c2m/c2m.sh diag mistral:7b`: step 0, 25 single calls. It prints native vs text-call counts
   per configuration and saves runs/gne_c2m-diag-*/diag.json. Descriptive; it doesn't change the design.
3. `bash gne_c2m/c2m.sh freeze mistral:7b`: writes FREEZE.md. No package file may change after this.
4. Stage by stage, in the background, validating each before the next:
   `nohup bash gne_c2m/c2m.sh controls mistral:7b > logs/c2m_controls.out 2>&1 &`
   `nohup bash gne_c2m/c2m.sh probe mistral:7b > logs/c2m_probe.out 2>&1 &` (prints the gate; main runs either way)
   `nohup bash gne_c2m/c2m.sh main mistral:7b > logs/c2m_main.out 2>&1 &`
5. If a batch stops early: `bash gne_c2m/c2m.sh resume runs/<batch folder> mistral:7b`. Never start that stage again.
6. `bash gne_c2m/c2m.sh analyze`: controls with interface counts, gate, main rates, interface, written
   actions, the three-scorer comparison, then R1, R2, the reading and the seniority control.

Any deviation goes in gne_c2m/DEVIATIONS.md (not hashed).
