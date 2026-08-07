# Installing model CLIs (macOS)

This repository supports two ways to run the master developer prompt:

- `claude` — Claude Code CLI (Anthropic)
- `codex` — Codex CLI (alternative)

If you already have a vendor CLI installed and configured, the scripts will
auto-detect it and use it. If not, you can either install a CLI per your
provider's instructions or use the repository's mock mode (`--mock` /
`MOCK_OUTPUT=1`) to run locally without a real model.

General macOS steps (safe, provider-agnostic):

1. Check whether a CLI is already available in your PATH:

```bash
command -v claude || command -v codex || echo "no model CLI found"
```

2. Install the CLI per your provider's docs.

- If your provider publishes a Homebrew formula, prefer:

```bash
brew install <formula-name>
```

- If the provider supplies a packaged binary, download, unzip, and move the
binary to `/usr/local/bin` or a location on your `PATH`.

3. Authenticate the CLI.

- Many CLIs accept an API key via environment variables. Common examples:

```bash
export ANTHROPIC_API_KEY="<your-key>"   # example for Claude-like CLIs
export CODEX_API_KEY="<your-key>"      # example for Codex-like CLIs
```

- Other CLIs provide an interactive `login` command, e.g. `claude login` or
`codex login` — follow the provider instructions.

4. Verify installation:

```bash
command -v claude && claude --help
command -v codex && codex --help
```

5. Run the master pipeline with a transcript:

```bash
cd /path/to/master-dev-prompt
./run_master_dev.sh sample_transcript.txt > outputs/sample.json
python3 validate_output.py outputs/sample.json
```

Mock mode (no CLI needed):

```bash
./run_master_dev.sh sample_transcript.txt --mock > outputs/sample.json
# or
MOCK_OUTPUT=1 ./run_master_dev.sh sample_transcript.txt > outputs/sample.json
```

If you need concrete install commands for a specific CLI (e.g. a known
Homebrew formula or pip package), tell me which CLI you want and I'll provide
step-by-step commands for macOS.

## GitHub CLI (`gh`) authentication

Some workflows in this repository (e.g. opening PRs, checking CI status)
assume the [GitHub CLI](https://cli.github.com/) is installed and
authenticated. This is separate from the model CLIs above.

1. Install `gh`:

```bash
brew install gh
```

2. Check whether it's already authenticated:

```bash
gh auth status
```

3. Authenticate — pick the flow that matches your context:

- **Interactive (local machine)** — opens a browser to complete login:

```bash
gh auth login
```

  Follow the prompts: choose `GitHub.com`, your preferred protocol
  (`HTTPS` is the safe default), and `Login with a web browser`.

- **Non-interactive (CI, containers, remote sessions)** — authenticate with a
  personal access token via stdin, without any interactive prompts:

```bash
echo "$GH_TOKEN" | gh auth login --with-token
```

  `GH_TOKEN` should hold a token with at least `repo` scope (and `workflow`
  if you need to trigger Actions). Never paste the token directly into a
  command or commit it to the repo — pass it through an environment
  variable or secret store.

4. Verify:

```bash
gh auth status
gh repo view
```

If `gh auth login` isn't available (e.g. a locked-down sandbox), tools in
this environment may instead rely on the GitHub API/MCP tooling configured
by the harness — in that case no local `gh` auth is required.
