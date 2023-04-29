# Advanced API plugin for oobabooga/text-generation-webui

This plugin
1. Provide Kobold-like interface (the same way as "api" classic extension)
2. **Provide advanced logic to auto-translate income prompts:**
    - You need to use multi_translate extension: https://github.com/janvarev/multi_translate
    - Set up param `'is_advanced_translation': True`, (set by default)
    - ...see the details in console
      - Due to advanced logic script splits income prompt by lines, and cache translation results
      - **Text quality feature:** when it generate English response, it cache it too (so you don't do double-translation English->UserLang->English next time) 
3. **Provide additional interfaces for text translations** (from and to English language).
    - _deprecated_, use https://github.com/janvarev/OneRingTranslator instead

## How to run this plugin

1. Download it
2. Move downloaded files to folder `extensions/api_advanced`
3. Run oobabooga bat with params: `--extensions multi_translate api_advanced` and NO --chat or --cai-chat!

To connect to this point use
`http://localhost:5000/api` (this can't run together with classic api extension by default)

