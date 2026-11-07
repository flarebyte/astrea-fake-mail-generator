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
			color:       "B60205"
			description: "Something is broken"
		},
		{
			name:        "enhancement"
			color:       "0E8A16"
			description: "New feature"
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
