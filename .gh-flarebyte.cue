package ghflarebyte

project: {
	org:  "flarebyte"
	repo: "astrea-fake-mail-generator"
}

sync: {
	mode: "push"
}

repository: {
	description:   "Fake email generator for providing testing fixtures"
	defaultBranch: "main"
	homepage:      "https://github.com/flarebyte/astrea-fake-mail-generator"
	visibility:    "public"
	template:      false
	topics: [
		"python",
		"email",
		"testing",
		"flarebyte",
	]
	labels: [
		{
			name:        "bug"
			color:       "d73a4a"
			description: "Something isn't working"
		},
		{
			name:        "documentation"
			color:       "0075ca"
			description: "Improvements or additions to documentation"
		},
		{
			name:        "duplicate"
			color:       "cfd3d7"
			description: "This issue or pull request already exists"
		},
		{
			name:        "enhancement"
			color:       "a2eeef"
			description: "New feature or request"
		},
		{
			name:        "good first issue"
			color:       "7057ff"
			description: "Good for newcomers"
		},
		{
			name:        "help wanted"
			color:       "008672"
			description: "Extra attention is needed"
		},
		{
			name:        "invalid"
			color:       "e4e669"
			description: "This doesn't seem right"
		},
		{
			name:        "question"
			color:       "d876e3"
			description: "Further information is requested"
		},
		{
			name:        "wontfix"
			color:       "ffffff"
			description: "This will not be worked on"
		},
	]
	features: {
		issues:                        true
		wiki:                          false
		projects:                      false
		discussions:                   false
		autoMerge:                     true
		mergeCommit:                   false
		rebaseMerge:                   false
		squashMerge:                   true
		squashMergeCommitMessage:      "pr-title"
		deleteBranchOnMerge:           true
		allowForking:                  false
		allowUpdateBranch:             false
		advancedSecurity:              true
		secretScanning:                true
		secretScanningPushProtection:  true
	}
}

build: {
    language: "python"
    mode: "package"
    runTests: true
    outputDir: "build"
    checksumFile: "build/checksums.txt"
}

// The specification validator uses only the Python standard library.
script: {
    runtime: "python3"
    root: "scripts"
}

devOutput: {
    color: "auto"
    style: "summary"
    showPassed: true
}

coverage: {
    min: 80
    enforceMin: true
}

release: {
    versionSource: "pyproject.toml"
    tagPrefix: "v"
    notesMode: "generate-notes"
    includeArtifacts: true
    artifactDir: "build"
    includeChecksums: true
}
