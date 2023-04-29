import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from modules import shared
from modules.text_generation import encode, generate_reply

path_settings_json =  "extensions/api_advanced/settings.json"
path_cache_en_json =  "extensions/api_advanced/cache_en.json"

params = {
    'port': 5000,
    'default_stopping_strings': [],
    #'default_stopping_strings': ["\n"],
    'is_advanced_translation': True,

}

cache_en_translation:dict[str,str] = {"":"","<START>":"<START>"}
#en_not_translate:dict[str,str] = {}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/v1/model':
            self.send_response(200)
            self.end_headers()
            response = json.dumps({
                'result': shared.model_name
            })

            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = json.loads(self.rfile.read(content_length).decode('utf-8'))

        if self.path == '/api/v1/generate':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            prompt = body['prompt']
            prompt_lines_orig = [k.strip() for k in prompt.split('\n')]
            import copy
            prompt_lines = copy.deepcopy(prompt_lines_orig)


            # running advanced translation logic
            if params["is_advanced_translation"]:
                from extensions.multi_translate import script
                script.params["is_translate_user"] = True # we need proc to English

                stat_miss = 0
                for i in range(len(prompt_lines)):
                    if cache_en_translation.get(prompt_lines[i]) is not None:
                        print("CACHE en_translation hit:",prompt_lines[i])
                        prompt_lines[i] = cache_en_translation.get(prompt_lines[i])
                    else:
                        print("CACHE en_translation MISS!:", prompt_lines_orig[i])
                        stat_miss += 1
                        res = script.input_modifier(prompt_lines_orig[i])
                        cache_en_translation[prompt_lines_orig[i]] = res
                        prompt_lines[i] = res

                script.params["is_translate_user"] = False  # not needed English processing further
                print("------ CACHE STAT: MISSES {0}/{1} (lower - better, ideally - 1)".format(stat_miss,len(prompt_lines)))





            max_context = body.get('max_context_length', 2048)
            while len(prompt_lines) >= 0 and len(encode('\n'.join(prompt_lines))) > max_context:
                prompt_lines.pop(0)

            prompt = '\n'.join(prompt_lines)
            generate_params = {
                'max_new_tokens': int(body.get('max_length', 200)),
                'do_sample': bool(body.get('do_sample', True)),
                'temperature': float(body.get('temperature', 0.5)),
                'top_p': float(body.get('top_p', 1)),
                'typical_p': float(body.get('typical', 1)),
                'repetition_penalty': float(body.get('rep_pen', 1.1)),
                'encoder_repetition_penalty': 1,
                'top_k': int(body.get('top_k', 0)),
                'min_length': int(body.get('min_length', 0)),
                'no_repeat_ngram_size': int(body.get('no_repeat_ngram_size', 0)),
                'num_beams': int(body.get('num_beams', 1)),
                'penalty_alpha': float(body.get('penalty_alpha', 0)),
                'length_penalty': float(body.get('length_penalty', 1)),
                'early_stopping': bool(body.get('early_stopping', False)),
                'seed': int(body.get('seed', -1)),
                'add_bos_token': int(body.get('add_bos_token', True)),
                'truncation_length': int(body.get('truncation_length', 2048)),
                'ban_eos_token': bool(body.get('ban_eos_token', False)),
                'skip_special_tokens': bool(body.get('skip_special_tokens', True)),
                'custom_stopping_strings': '',  # leave this blank
                'stopping_strings': body.get('stopping_strings', params["default_stopping_strings"]),
            }
            stopping_strings = generate_params.pop('stopping_strings')
            if not params["is_advanced_translation"]:
                generator = generate_reply(prompt, generate_params, stopping_strings=stopping_strings)
            else:
                # advanced logic
                script.params["is_translate_user"] = False  # we don't need proc to English
                script.params["is_translate_system"] = False  # we don't need proc back
                generator = generate_reply(prompt, generate_params, stopping_strings=stopping_strings)


            answer = ''
            for a in generator:
                if isinstance(a, str):
                    answer = a
                else:
                    answer = a[0]

            # seems we need it here....
            answer = answer[len(prompt):]

            if params["is_advanced_translation"]:
                print("is_advanced_translation original answer:", answer )
                answer_lines_orig = [k.strip() for k in answer.split('\n')]
                answer_lines = copy.deepcopy(answer_lines_orig)
                script.params["is_translate_system"] = True  # we need translate back
                for i in range(len(answer_lines)):
                    res = script.output_modifier(answer_lines_orig[i])
                    cache_en_translation[res] = answer_lines_orig[i]
                    answer_lines[i] = res

                # special case - mixing two end phrases together

                # example: prompt end: Aqua:
                # result end: Hi!
                # so we need cache for phrase "Aqua: Hi!"

                complex_phrase1_user = prompt_lines_orig[len(prompt_lines_orig)-1]+" "+answer_lines[0]
                complex_phrase1_user2 = prompt_lines_orig[len(prompt_lines_orig) - 1] + answer_lines[0]
                complex_phrase1_en = prompt_lines[len(prompt_lines_orig)-1]+" "+answer_lines_orig[0]
                cache_en_translation[complex_phrase1_user] = complex_phrase1_en
                cache_en_translation[complex_phrase1_user2] = complex_phrase1_en

                answer = "\n".join(answer_lines)

                print("is_advanced_translation final answer:", answer)

                save_cache_en()

            response = json.dumps({
                'results': [{
                    'text': answer
                }]
            })
            self.wfile.write(response.encode('utf-8'))
        # deprecated API for translation
        # elif self.path == '/api/v1/translate-to-en':
        #     # Not compatible with KoboldAI api
        #     from extensions.multi_translate import script
        #
        #     self.send_response(200)
        #     self.send_header('Content-Type', 'application/json')
        #     self.end_headers()
        #
        #     response = json.dumps({
        #         'result': script.input_modifier(body['prompt'])
        #     })
        #     self.wfile.write(response.encode('utf-8'))
        # elif self.path == '/api/v1/translate-from-en':
        #     # Not compatible with KoboldAI api
        #     from extensions.multi_translate import script
        #
        #     self.send_response(200)
        #     self.send_header('Content-Type', 'application/json')
        #     self.end_headers()
        #
        #     response = json.dumps({
        #         'result': script.output_modifier(body['prompt'])
        #     })
        #     self.wfile.write(response.encode('utf-8'))

        elif self.path == '/api/v1/token-count':
            # Not compatible with KoboldAI api
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

            tokens = encode(body['prompt'])[0]
            response = json.dumps({
                'results': [{
                    'tokens': len(tokens)
                }]
            })
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_error(404)


def run_server():
    server_addr = ('0.0.0.0' if shared.args.listen else '127.0.0.1', params['port'])
    server = ThreadingHTTPServer(server_addr, Handler)
    if shared.args.share:
        try:
            from flask_cloudflared import _run_cloudflared
            public_url = _run_cloudflared(params['port'], params['port'] + 1)
            print(f'Starting KoboldAI compatible api at {public_url}/api')
        except ImportError:
            print('You should install flask_cloudflared manually')
    else:
        print(f'Starting KoboldAI compatible api advanced at http://{server_addr[0]}:{server_addr[1]}/api')
    server.serve_forever()


def setup():
    load_settings()
    load_cache_en()
    print("Loaded Cache_en length: {0}".format(len(cache_en_translation)))
    Thread(target=run_server, daemon=True).start()


# settings etc
def save_settings():
    global params


    with open(path_settings_json, 'w') as f:
        json.dump(params, f, indent=2)

def save_cache_en():
    global cache_en_translation

    with open(path_cache_en_json, 'w', encoding="utf-8") as f:
        json.dump(cache_en_translation, f, indent=2)

def load_settings():
    global params

    try:
        with open(path_settings_json, 'r') as f:
            # Load the JSON data from the file into a Python dictionary
            data = json.load(f)

        if data:
            params = {**params, **data} # mix them, this allow to add new params seamlessly

    except FileNotFoundError:
        #memory_settings = {"position": "Before Context"}
        save_settings()
        pass

def load_cache_en():
    global cache_en_translation

    try:
        with open(path_cache_en_json, 'r') as f:
            # Load the JSON data from the file into a Python dictionary
            data = json.load(f)

        if data:
            cache_en_translation = {**cache_en_translation, **data} # mix them, this allow to add new params seamlessly

    except FileNotFoundError:
        #memory_settings = {"position": "Before Context"}
        pass


