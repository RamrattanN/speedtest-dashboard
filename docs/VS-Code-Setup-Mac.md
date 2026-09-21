# VS Code Setup on Mac

The repository includes a ready-made VS Code workspace configuration.  Follow
these steps after cloning the recovery branch.

## 1. Install and open VS Code

Install Visual Studio Code from <https://code.visualstudio.com/>, then start it.
Choose **File > Open Folder** and select:

```text
Desktop/speedtest-dashboard
```

Choose **Trust the authors** when VS Code asks whether you trust the folder.

## 2. Install the recommended extensions

VS Code should offer to install the workspace recommendations.  Select
**Install All**.  The recommendations provide Python language support,
debugging, and GitHub pull-request integration.

If the prompt does not appear:

1. Select the **Extensions** icon in the left sidebar.
2. Enter `@recommended` in the search box.
3. Install the recommendations under **Workspace Recommendations**.

## 3. Create the project environment

1. Open **Terminal > Run Task**.
2. Select **Setup project**.
3. Wait until the Terminal finishes without a red error.

This creates `.venv` inside the project and installs the application and its
test tools.

## 4. Select the correct Python interpreter

1. Press **Command-Shift-P**.
2. Enter `Python: Select Interpreter`.
3. Select the interpreter ending in:

```text
speedtest-dashboard/.venv/bin/python
```

The workspace normally selects this interpreter automatically after setup.

## 5. Run the automated tests

Use either method:

- Select the laboratory-flask **Testing** icon, then select **Run Tests**.
- Open **Terminal > Run Task**, then select **Run automated tests**.

All tests should pass without performing a real internet speed test.

## 6. Start the application

For normal acceptance testing:

1. Open **Terminal > Run Task**.
2. Select **Start Speedtest Monitor**.
3. Wait for the browser to open <http://localhost:8501>.

Stop it by selecting its Terminal and pressing **Control-C**.

## 7. Run through the debugger

Select the **Run and Debug** icon in the sidebar.  The workspace provides:

- **Dashboard only**, which opens the UI without starting the collector.
- **Collector single test**, which performs one real speed test.
- **Full application**, which starts the collector and dashboard together.

Select a configuration and press the green start button.  Use **Dashboard
only** when changing the visual interface and **Full application** for an
end-to-end check.

## 8. Review Git changes

Select the **Source Control** icon in the sidebar.  Modified files appear under
**Changes**.  Select a filename to review its comparison before committing.

The GitHub Pull Requests extension can sign in to your GitHub account and show
the recovery PR inside VS Code.  Signing in is optional for local testing.

## Common fixes

### VS Code cannot find Python

Install Python 3.11 or newer, restart VS Code, and repeat **Setup project**.

### The test icon shows no tests

Press **Command-Shift-P**, run `Python: Configure Tests`, select **pytest**, and
select the `tests` folder.

### Port 8501 is already in use

Stop the other dashboard with **Control-C**, or edit the port in the selected
debug configuration within `.vscode/launch.json`.
