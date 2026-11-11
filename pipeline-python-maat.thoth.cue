// Generic Python pipeline: no package names or repository-specific paths.
{
  configVersion: "1"
  action: "input-pipeline"

  discovery: {
    root: "."
    exclude: [".venv/**", "venv/**", ".uv-cache/**", "build/**", "dist/**", "thoth-meta/**"]
  }

  // Stop on analysis errors rather than persisting incomplete summaries.
  errors: { mode: "fail-fast" }

  filter: {
    inline: """
      if not thoth.ends_with(locator, ".py") then return false end
      local path = "/" .. locator
      local name = locator:match("([^/]+)$") or locator
      local is_test = path:find("/tests/", 1, true) ~= nil
        or path:find("/test/", 1, true) ~= nil
        or name:match("^test_.*%.py$") ~= nil
        or name:match(".*_test%.py$") ~= nil
      return not is_test
      """
  }

  shell: {
    enabled: true
    decodeJsonStdout: true
    // Keep the locator in a positional argument, outside shell source.
    program: "sh"
    workingDir: "."
    argsTemplate: [
      "-c",
      "exec npx --yes maat-ostraca@0.9.0 analyse --in \"$1\" --rules import_files_list,function_map,method_map,class_map --language python --json",
      "thoth-maat", "{locator}",
    ]
  }

  postMap: {
    inline: """
      local rules = shell and shell.json and shell.json.rules
      assert(rules, "maat did not return analysis rules")
      return {
        meta = {
          language = "python",
          import_files_list = rules.import_files_list or {},
          function_list = thoth.sort_keys(rules.function_map or {}),
          method_list = thoth.sort_keys(rules.method_map or {}),
          class_list = thoth.sort_keys(rules.class_map or {}),
        },
      }
      """
  }

  persistMeta: {
    enabled: true
    outDir: "./thoth-meta/python"
  }

  output: {
    out: "./temp/pipeline-python-maat.json"
    pretty: true
    lines: false
  }

  ui: { progress: true, progressIntervalMs: 250 }
}
