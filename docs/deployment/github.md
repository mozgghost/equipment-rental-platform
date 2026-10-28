# Publish to a new GitHub repository

The connected GitHub actions available during preparation allowed reading an existing repository, but did not expose a confirmed repository-creation operation. Therefore no remote repository was created and no push was performed.

1. On GitHub choose **New repository** and create `equipment-rental-platform` (private is recommended until security review). Do not pre-populate it with a README/license, because these files already exist locally.
2. Extract the ZIP to a directory and inspect `.env`, credentials and generated files; only `.env.example` should be present.
3. In the project folder run:

```bash
git init -b main
git add .
git commit -m "chore: initialize equipment rental platform"
git remote add origin https://github.com/<your-account>/equipment-rental-platform.git
git push -u origin main
```

4. Protect `main`: require pull requests, passing CI, at least one approval if collaborators exist, conversation resolution, and disallow force-push/deletion.
5. Add deployment secrets only through GitHub Environments/secret store; never as repository files.
