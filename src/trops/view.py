import os
import subprocess
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

from textwrap import dedent

from .trops import TropsMain
from .utils import absolute_path


class TropsView(TropsMain):
    """View tracked file contents from the repository.

    Usage examples:
      - trops view /etc/hosts
      - trops view --commit HEAD~1 /var/log/syslog
    """

    def __init__(self, args, other_args):
        super().__init__(args, other_args)

        if other_args:
            msg = f"""\
                Unsupported argments: {', '.join(other_args)}
                > trops view --help"""
            print(dedent(msg))
            exit(1)

        if not hasattr(args, 'file') or not args.file:
            print('ERROR: file path is required')
            exit(1)

        self.web = getattr(args, 'web', False)
        self.no_browser = getattr(args, 'no_browser', False)
        self.target_path = absolute_path(args.file)
        self.commit = getattr(args, 'commit', None) or 'HEAD'

        if self.web:
            if not os.path.isdir(self.target_path):
                print(f"ERROR: '{self.target_path}' is not a directory")
                exit(1)
        else:
            if not os.path.isfile(self.target_path):
                print(f"ERROR: '{self.target_path}' is not a file")
                exit(1)

        # Resolve repository-relative path if viewing a single file
        if not self.web:
            self.rel_path = os.path.relpath(self.target_path, start=self.work_tree)

    def view(self) -> None:
        """Show file contents from a specific commit (default: HEAD)."""
        if self.web:
            self._serve_web(self.target_path)
        else:
            cmd = self.git_cmd + ['show', f'{self.commit}:{self.rel_path}']
            subprocess.call(cmd)

    def _serve_web(self, folder: str) -> None:
        md_files = [f for f in os.listdir(folder) if f.endswith('.md')]
        md_files.sort()

        git_cmd = ['git']  # use current directory's repo, not trops repo
        repo_cwd = os.getcwd()  # set current directory as git directory for web app

        class Handler(BaseHTTPRequestHandler):
            def _send(self, code: int, body: str, content_type: str = 'text/html; charset=utf-8'):
                self.send_response(code)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(body.encode('utf-8'))

            def do_GET(self):  # noqa: N802 (http.server API)
                parsed = urlparse(self.path)
                if parsed.path == '/' or parsed.path == '/index.html':
                    self._send(200, self._render_index(md_files))
                elif parsed.path == '/raw':
                    qs = parse_qs(parsed.query)
                    name = (qs.get('name') or [''])[0]
                    if not name or name not in md_files:
                        self._send(404, 'Not found', 'text/plain; charset=utf-8')
                        return
                    file_path = os.path.join(folder, name)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        # YAML front matter (--- ... ---) を先頭に持つ場合は無視
                        if content.startswith('---'):
                            lines = content.splitlines()
                            if lines and lines[0].strip() == '---':
                                end_idx = -1
                                for i in range(1, len(lines)):
                                    if lines[i].strip() == '---':
                                        end_idx = i
                                        break
                                if end_idx != -1:
                                    content = '\n'.join(lines[end_idx+1:]).lstrip('\n')
                        self._send(200, content, 'text/plain; charset=utf-8')
                    except Exception as e:
                        self._send(500, f'Error: {e}', 'text/plain; charset=utf-8')
                elif parsed.path == '/git':
                    qs = parse_qs(parsed.query)
                    hashv = (qs.get('hash') or [''])[0]
                    pathv = (qs.get('path') or [''])[0]
                    # very simple validation for hash
                    if not hashv or not all(c in '0123456789abcdefABCDEF' for c in hashv):
                        self._send(400, 'Invalid hash', 'text/plain; charset=utf-8')
                        return
                    try:
                        if pathv:
                            cmd = git_cmd + ['show', f'{hashv}:{pathv}']
                        else:
                            cmd = git_cmd + ['show', hashv]
                        result = subprocess.run(cmd, capture_output=True, cwd=repo_cwd)
                        if result.returncode != 0:
                            self._send(500, result.stderr.decode('utf-8') or 'git show failed', 'text/plain; charset=utf-8')
                        else:
                            self._send(200, result.stdout.decode('utf-8'), 'text/plain; charset=utf-8')
                    except Exception as e:
                        self._send(500, f'Error: {e}', 'text/plain; charset=utf-8')
                else:
                    self._send(404, 'Not found', 'text/plain; charset=utf-8')

            def log_message(self, format, *args):  # silence default logging
                return

            @staticmethod
            def _render_index(files):
                # Use client-side markdown rendering via marked.js CDN
                items = '\n'.join(
                    f'<li><a href="#" onclick="loadFile(\'{name}\');return false;">{name}</a></li>'
                    for name in files
                )
                first = files[0] if files else ''
                html = f"""
                <!doctype html>
                <html>
                <head>
                  <meta charset="utf-8" />
                  <title>Trops View</title>
                  <style>
                    body {{ margin: 0; font-family: -apple-system, Helvetica, Arial, sans-serif; }}
                    .container {{ display: flex; height: 100vh; }}
                    .sidebar {{ width: 280px; background:#f6f8fa; border-right:1px solid #e1e4e8; overflow:auto; }}
                    .sidebar h2 {{ margin: 16px; font-size: 16px; }}
                    .sidebar ul {{ list-style:none; padding:0 8px 16px 16px; margin:0; }}
                    .sidebar li {{ margin: 6px 0; }}
                    /* Links: keep color same as text, underline only */
                    .sidebar a {{ color: inherit; text-decoration: underline; }}
                    .content {{ flex:1; padding:20px; overflow:auto; }}
                    pre {{ background:#f6f8fa; padding: 12px; overflow:auto; }}
                    code {{ background:#f6f8fa; padding: 2px 4px; }}
                    /* table borders */
                    #content table {{ border-collapse: collapse; width: 100%; }}
                    #content table, #content th, #content td {{ border: 1px solid #e1e4e8; }}
                    #content th, #content td {{ padding: 6px 8px; }}
                    /* content links follow same style */
                    #content a {{ color: inherit; text-decoration: underline; }}
                    /* modal */
                    .modal {{ display:none; position:fixed; inset:0; background:rgba(0,0,0,.45); }}
                    .modal-inner {{ position:absolute; top:5%; left:50%; transform:translateX(-50%); width:80%; max-height:90%; background:#fff; border-radius:6px; box-shadow:0 10px 40px rgba(0,0,0,.3); display:flex; flex-direction:column; }}
                    .modal-header {{ padding:10px 14px; border-bottom:1px solid #e1e4e8; display:flex; justify-content:space-between; align-items:center; }}
                    .modal-body {{ padding:0 14px 14px; overflow:auto; }}
                    .close-btn {{ cursor:pointer; border:none; background:none; font-size:18px; }}
                  </style>
                  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
                </head>
                <body>
                  <div class="container">
                    <div class="sidebar">
                      <h2>Files</h2>
                      <ul>
                        {items}
                      </ul>
                    </div>
                    <div class="content">
                      <div id="content"></div>
                    </div>
                  </div>
                  <div id="modal" class="modal" onclick="if(event.target.id==='modal')closeModal();">
                    <div class="modal-inner">
                      <div class="modal-header">
                        <div id="modal-title">git show</div>
                        <button class="close-btn" onclick="closeModal()">✕</button>
                      </div>
                      <div class="modal-body">
                        <pre id="modal-content"></pre>
                      </div>
                    </div>
                  </div>
                  <script>
                    async function loadFile(name) {{
                      const res = await fetch('/raw?name=' + encodeURIComponent(name));
                      if (!res.ok) {{ document.getElementById('content').innerText = 'Failed to load.'; return; }}
                      const text = await res.text();
                      const html = marked.parse(text);
                      const enhanced = enhanceTropsShow(html);
                      document.getElementById('content').innerHTML = enhanced;
                    }}
                    function enhanceTropsShow(html) {{
                      // Replace occurrences of: trops show <hash>[:<path>]
                      const re = /(trops\s+show\s+)([0-9a-fA-F]{{7,}})(?::([^\s<]+))?/g;
                      return html.replace(re, (m, pfx, hash, path) => {{
                        const hlink = `<a href="#" onclick="gitShow('${{hash}}');return false;">${{hash}}</a>`;
                        if (path) {{
                          const plink = `<a href="#" onclick="gitShowFile('${{hash}}','${{path}}');return false;">${{path}}</a>`;
                          return `${{pfx}}${{hlink}}:${{plink}}`;
                        }} else {{
                          return `${{pfx}}${{hlink}}`;
                        }}
                      }});
                    }}
                    async function gitShow(hash) {{
                      document.getElementById('modal-title').innerText = 'git show ' + hash;
                      const res = await fetch('/git?hash=' + encodeURIComponent(hash));
                      const text = await res.text();
                      document.getElementById('modal-content').textContent = text;
                      openModal();
                    }}
                    async function gitShowFile(hash, path) {{
                      document.getElementById('modal-title').innerText = 'git show ' + hash + ':' + path;
                      const res = await fetch('/git?hash=' + encodeURIComponent(hash) + '&path=' + encodeURIComponent(path));
                      const text = await res.text();
                      document.getElementById('modal-content').textContent = text;
                      openModal();
                    }}
                    function openModal() {{ document.getElementById('modal').style.display = 'block'; }}
                    function closeModal() {{ document.getElementById('modal').style.display = 'none'; }}
                    { 'loadFile("' + first + '");' if first else '' }
                  </script>
                </body>
                </html>
                """
                return html

        httpd = HTTPServer(('127.0.0.1', 8001), Handler)
        print('Serving trops view on http://localhost:8001 (Ctrl+C to stop)')
        # Optionally open browser
        if not self.no_browser:
            try:
                webbrowser.open('http://localhost:8001', new=2)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nStopping server...')
        finally:
            httpd.server_close()


def run(args, other_args):
    tv = TropsView(args, other_args)
    tv.view()


def add_view_subparsers(subparsers):
    parser_view = subparsers.add_parser('view', help='view file content from repo')
    parser_view.add_argument('-e', '--env', help='Set environment name')
    parser_view.add_argument('--commit', help='Commit-ish (default: HEAD)')
    parser_view.add_argument('--web', action='store_true', help='Start a local web viewer for a folder of .md files')
    parser_view.add_argument('--no-browser', action='store_true', help='Do not open the browser automatically')
    parser_view.add_argument('file', help='Absolute path to file (or folder with --web) in work tree')
    parser_view.set_defaults(handler=run)


