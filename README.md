# VS Code Profiles

A modular architecture for managing multiple Visual Studio Code profiles without settings duplication.

## Architecture

* **`settings.json`**: Single source of truth for all profiles. Contains global UI, theme (Vision Night), typography (JetBrains Mono), telemetry, Copilot, and language-specific overrides (`[c, cpp]`, `[swift]`, `[csharp]`) for indentation and rulers.
* **`keybindings.json`**: Shared custom keybindings.
* **`extensions/`**: Plain text extension manifests (one extension ID per line):
  * `base.txt`: Shared core extensions used by all profiles (GitLens, ErrorLens, Todo Tree, WakaTime, etc.).
  * `default.txt`: Web development (ESLint, Prettier, Tailwind CSS, Vue, Prisma, etc.).
  * `audio.txt`: Audio plugin & C++ development (C/C++, CMake Tools, Code Runner).
  * `game.txt`: Game development (C#, C# Dev Kit, Unity Tools, Docker).
  * `ios.txt`: iOS & macOS development (Swift, Sweetpad, LLDB).
* **`manage.py`**: Standalone CLI utility (Python 3, standard library only, zero dependencies) to build, sync, and install profiles.
* **`*.code-profile`**: Clean exported profile files (~11 KB each, stripped of internal `globalState` bloat). Compatible with VS Code and Cursor.

---

## CLI Usage (`manage.py`)

The script is executable and requires Python 3:

```bash
./manage.py [command]
```

### 1. Build Clean `.code-profile` Files

Combines `settings.json` + `keybindings.json` + `base.txt` + the profile's specific extension file to produce lightweight `.code-profile` files in the repository root:

```bash
./manage.py --build
```

> [!NOTE]
> Running `./manage.py` without arguments defaults to `--build`.

### 2. Sync Settings to Local VS Code Profiles

Copies `settings.json` and `keybindings.json` directly into your active local VS Code profile directories (`~/Library/Application Support/Code/User/profiles/...`):

```bash
./manage.py --sync
```

Use this command whenever you modify `settings.json` or `keybindings.json` to propagate changes across all local profiles immediately.

### 3. Install Extensions via VS Code CLI

Installs all resolved extensions (`base.txt` + profile specific) directly into your VS Code profiles:

```bash
# Install extensions for a single profile
./manage.py --install Audio
./manage.py --install Game
./manage.py --install iOS
./manage.py --install Default

# Install extensions for ALL profiles sequentially
./manage.py --install
```

---

## Workflow: How to Update Your Setup

* **To add a global extension (used everywhere):** Add its ID to `extensions/base.txt` and run `./manage.py --build`.
* **To add a stack-specific extension:** Add its ID to the corresponding file in `extensions/` (e.g. `extensions/audio.txt`) and run `./manage.py --build`.
* **To change editor settings:** Edit `settings.json` in the root and run `./manage.py --sync` to update your local VS Code, then `./manage.py --build` to keep git tracked profiles updated.

---

## Documentation & References

* [Official VS Code Profiles Documentation](https://code.visualstudio.com/docs/configure/profiles)

