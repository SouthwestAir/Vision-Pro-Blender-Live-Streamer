# Contributing to Southwest Airlines Open-Source Projects

First and foremost, thank you for your interest in contributing to Southwest Airlines' open-source projects! We appreciate your efforts and contributions to our community. This document provides guidelines and instructions for submitting contributions.

## Code of Conduct

By participating in this project, you are expected to adhere to our [Code of Conduct](https://github.com/SouthwestAir/.github/blob/main/CODE_OF_CONDUCT.md). Please read it before contributing.

## Getting Started

1. Fork the repository you wish to contribute to.
2. Clone your forked repository to your local machine.
3. Set up the development environment following the instructions provided in the README file.
4. Create a new branch for your changes using **slashes** for categorization. Use a descriptive name following these prefixes:


	* `feat/` for new features (e.g., `feat/add-login-support`)
	* `fix/` for bug fixes (e.g., `fix/header-alignment`)
	* `chore/` for version bumps, typo fixes, or maintenance (e.g., `chore/bump-version-v1.1`)



## How to Contribute

You can contribute to our projects in several ways:

* Reporting bugs
* Suggesting new features or improvements
* Submitting bug fixes
* Implementing new features
* Improving documentation

#### Submitting Code Changes

1. **Single Responsibility:** Each Pull Request (PR) should address one single issue, bug fix, or feature.
2. **Avoid "Kitchen Sink" PRs:** Do not combine unrelated changes—such as fixing a typo in one file and adding a feature in another—into the same PR.
3. **Refactoring:** If you identify a need for large-scale refactoring while working on a feature, please submit the refactor as a separate PR before or after your functional change.
4. **Clean Code:** Ensure your code is clean, well-documented, and adheres to the project's coding style.
5. **Testing:** Test your changes to ensure they work as expected and do not introduce new bugs.
6. **Commits:** Use a clear action and description (e.g., added, modified, deleted, updated).
	* Examples:
		* "feat: added new feature that does x, y, z"
		* "fix: modified something so that the button works"
7. **Code Assist** You can use LLMs and code-assists, but make sure you review every line of code before submitting and note your LLMs in your pull request.

## Pull Request Process

1. **Contextual Clarity:** Ensure the code changes are strictly relevant to the issue discussed in the initial consultation via issue or email.
2. **Size Limits:** Aim for small, incremental PRs; smaller sets of changes are easier to review, less prone to bugs, and are merged more quickly.
3. **Clean Builds:** Ensure any install or build dependencies are removed before the end of the layer when doing a build.
4. **Documentation & Interface:** Update the `README.md` with details of changes to the interface, including new environment variables, exposed ports, and container parameters.
5. **Versioning:** Increase the version numbers in any examples files and the `README.md` using the [SemVer](http://semver.org/) scheme.
6. **Review & Approval:** A project maintainer will review your PR. You may merge the PR once you have the sign-off of two other developers.

Please note that the maintainers have the final say on whether to accept or reject a pull request.

## Additional Resources

* [GitHub Help](https://help.github.com/)
* [Git and GitHub Learning Resources](https://try.github.io/)

Thank you once again for your interest in contributing to Southwest Airlines' open-source projects. Your contributions are greatly appreciated!