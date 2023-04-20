# Advanced API plugin for oobabooga/text-generation-webui

This plugin
1. Provide Kobold-like interface (the same way as "api" classic extension)
2. **Provide additional interfaces for text translations** (from and to English language).
    - This allows AI clients to follow this pipeline
      - Translate user prompt to English language
      - Process it with text gen
      - Translate result back from English to user language
    - ... because chatting on English is more stable and usually produce better results 
3. (fix) problem with text generation

## How to run this plugin

1. Download it
2. Move downloaded files to folder `extensions/api_advanced`
3. Run oobabooga bat with params: `--extensions google_translate api_advanced`

To connect to this point use
`http://localhost:4999/api`

## API for text translations

API uses settings from oobaboog/google_translate plugin, so setup it first.

Call API (from user language to English):
```python
response = requests.post(f"http://{server}:4999/api/v1/translate-to-en", json={
    "prompt": prompt,
}).json()
```
result:
```json
{'result': 'translated text'}
```

Call API (from English to user language):
```python
response = requests.post(f"http://{server}:4999/api/v1/translate-from-en", json={
    "prompt": prompt,
}).json()
```
result:
```json
{'result': 'translated text'}
```