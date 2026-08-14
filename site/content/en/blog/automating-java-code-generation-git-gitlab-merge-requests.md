---
title: "Automating Java Code Generation, Git, and GitLab Merge Requests Using Java"
date: 2023-12-30
draft: false
description: "Generate Java source with JavaPoet, commit and push with JGit, and open a GitLab merge request with GitLab4j — an end-to-end CI/CD automation in a single Java program."
tags: ["java", "java-poet", "jgit", "gitlab4j", "automation"]
featured_image: "/images/blog/java-codegen-gitlab.gif"
og_image: "/images/blog/java-codegen-gitlab.gif"
external_url: "https://medium.com/@mayurprajapatiin/automating-java-code-generation-git-and-gitlab-merge-requests-using-java-1e11f1a4bf45"
external_source: "Medium"
---

![Automating Java code generation, Git, and GitLab merge requests](/images/blog/java-codegen-gitlab.gif)

*Cover image from the original Medium post — the automation's final output: generated code, a pushed branch, and a GitLab merge request.*

Picture a Python microservice that keeps updating a database, while another team
must repeatedly modify a separate project's code to stay aligned with that
evolving data. Instead of a human in the loop, a single Java program can
generate the code, commit it, and open a merge request — entirely on its own.

The full post walks through the pipeline step by step: **JavaPoet** generates the
Java source, **JGit** clones the repository, checks out a new branch, commits, and
pushes, and **GitLab4j** creates the merge request with an assignee — all driven by
a simple `props.properties` file.

[**Read the full post on Medium →**](https://medium.com/@mayurprajapatiin/automating-java-code-generation-git-and-gitlab-merge-requests-using-java-1e11f1a4bf45)
