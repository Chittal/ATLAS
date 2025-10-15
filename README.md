Open Kuzu Explorer
```
docker run --rm -p 8000:8000 -v "${PWD}:/database" -e KUZU_FILE="skills_graph.db" kuzudb/explorer:latest
```

Run Pocketbase database
```
../pocketbase_0.29.3_windows_amd64/pocketbase serve --dir ./pocketbase-data
```

Run Application
```
venv\Scripts\activate
python run_server.py
```